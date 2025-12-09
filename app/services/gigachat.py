import os
import json
import logging
import uuid
from typing import Optional, Dict, Any, List  # Optional должен быть импортирован
import httpx
from pydantic import ValidationError

from app.core.config import settings
from app.models.gigachat import GigaChatAnalysis
from app.models.analysis import AnalysisResult

logger = logging.getLogger(__name__)


class GigaChatError(Exception):
    """Кастомная ошибка для GigaChat API"""
    pass


def should_verify_ssl() -> bool:
    """Определяет, нужно ли проверять SSL сертификаты"""
    # Проверяем переменную окружения
    verify_env = os.environ.get('GIGACHAT_VERIFY_SSL', '').lower()

    if verify_env in ['false', '0', 'no']:
        logger.info("SSL verification disabled by environment variable")
        return False
    elif verify_env in ['true', '1', 'yes']:
        logger.info("SSL verification enabled by environment variable")
        return True

    # По умолчанию для тестирования отключаем SSL проверку
    # В продакшене это нужно включить!
    logger.warning("SSL verification disabled by default for testing")
    logger.warning("Set GIGACHAT_VERIFY_SSL=true for production")
    return False


class GigaChatClient:
    """Клиент для работы с GigaChat API"""

    def __init__(self, verify_ssl: Optional[bool] = None):
        self.api_key = settings.gigachat_api_key.get_secret_value(
        ) if settings.gigachat_api_key else None
        self.auth_url = settings.gigachat_auth_url
        self.api_url = settings.gigachat_api_url
        self.model = settings.gigachat_model
        self.timeout = settings.gigachat_timeout
        self.max_tokens = settings.gigachat_max_tokens
        self.scope = settings.gigachat_scope

        if verify_ssl is None:
            self.verify_ssl = should_verify_ssl()
        else:
            self.verify_ssl = verify_ssl

        if not self.verify_ssl:
            logger.warning("SSL verification is DISABLED! This is insecure!")
            import warnings
            warnings.filterwarnings(
                'ignore', message='Unverified HTTPS request')

        self._access_token: Optional[str] = None
        self._token_expires_at: Optional[float] = None

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            verify=self.verify_ssl,
            limits=httpx.Limits(
                max_keepalive_connections=5, max_connections=10)
        )

    async def authenticate(self) -> None:
        """Аутентификация в GigaChat API"""
        if not self.api_key:
            raise GigaChatError("GigaChat API key not configured")

        # Проверяем, не истек ли текущий токен
        if self._access_token and self._token_expires_at:
            import time
            if time.time() < self._token_expires_at - 60:  # 60 секунд до истечения
                logger.debug("Using cached access token")
                return

        try:
            headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Accept": "application/json",
                "RqUID": str(uuid.uuid4()),
                "Authorization": f"Basic {self.api_key}"
            }

            data = {"scope": self.scope}

            logger.info(
                f"Authenticating to GigaChat API (SSL: {self.verify_ssl})")

            auth_response = await self.client.post(
                self.auth_url,
                headers=headers,
                data=data
            )

            if auth_response.status_code == 429:
                # Ошибка 429 - слишком много запросов
                logger.warning(
                    "GigaChat rate limit exceeded (429 Too Many Requests)")
                logger.warning("Waiting and retrying...")

                # Ждем 30 секунд и пробуем еще раз
                import asyncio
                await asyncio.sleep(30)

                # Повторная попытка
                auth_response = await self.client.post(
                    self.auth_url,
                    headers=headers,
                    data=data
                )

            if auth_response.status_code != 200:
                logger.error(f"Auth failed with status {
                             auth_response.status_code}: {auth_response.text}")

                # Если все еще ошибка после повторной попытки
                if auth_response.status_code == 429:
                    raise GigaChatError(
                        "GigaChat rate limit exceeded. Please try again later.")
                else:
                    auth_response.raise_for_status()

            auth_result = auth_response.json()
            self._access_token = auth_result.get("access_token")
            self._token_expires_at = auth_result.get("expires_at")

            if not self._access_token:
                logger.error(f"No access_token in response: {auth_result}")
                raise GigaChatError("Failed to obtain access token")

            logger.info("GigaChat authentication successful")

        except httpx.RequestError as e:
            logger.error(f"GigaChat authentication request failed: {e}")

            if isinstance(e, httpx.ConnectError) and "SSL" in str(e) and self.verify_ssl:
                logger.warning("SSL error, retrying without verification...")
                await self._retry_without_ssl(headers, data)
            else:
                raise GigaChatError(f"Authentication request failed: {e}")

        except Exception as e:
            logger.error(f"GigaChat authentication error: {e}")
            raise GigaChatError(f"Authentication error: {e}")

    async def _retry_without_ssl(self, headers: dict, data: dict):
        """Повторяет аутентификацию без проверки SSL"""
        logger.warning("Creating new client with SSL verification disabled")

        await self.client.aclose()
        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            verify=False,
            limits=httpx.Limits(
                max_keepalive_connections=5, max_connections=10)
        )

        auth_response = await self.client.post(
            self.auth_url,
            headers=headers,
            data=data
        )
        auth_response.raise_for_status()

        auth_result = auth_response.json()
        self._access_token = auth_result.get("access_token")

        if not self._access_token:
            raise GigaChatError("Failed to obtain access token")

        logger.info(
            "GigaChat authentication successful (SSL verification disabled)")
        self.verify_ssl = False

    async def analyze_speech(self, analysis_result: AnalysisResult) -> Optional[GigaChatAnalysis]:
        """
        Отправляет результаты анализа в GigaChat для получения
        расширенных персонализированных рекомендаций.
        """
        if not settings.gigachat_enabled:
            logger.info("GigaChat analysis is disabled")
            return None

        # Пробуем аутентифицироваться, если нужно
        if not self._access_token:
            try:
                await self.authenticate()
            except GigaChatError as e:
                logger.warning(f"Failed to authenticate with GigaChat: {e}")

                # Если ошибка 429, логируем и возвращаем None
                if "rate limit" in str(e).lower() or "429" in str(e):
                    logger.warning(
                        "GigaChat rate limit exceeded, skipping analysis")
                else:
                    logger.error(f"GigaChat authentication error: {e}")

                return None

        try:
            prompt = self._create_analysis_prompt(analysis_result)

            chat_url = f"{self.api_url}/chat/completions"
            request_data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system",
                        "content": """Ты эксперт по публичным выступлениям и ораторскому искусству. 
                        Анализируй речь по предоставленным метрикам и транскрипту. 
                        Дай развернутый, персонализированный анализ. 
                        Отвечай в формате JSON со следующей структурой:
                        {
                            "overall_assessment": "строка - общая оценка",
                            "strengths": ["массив строк - сильные стороны"],
                            "areas_for_improvement": ["массив строк - зоны роста"],
                            "detailed_recommendations": ["массив строк - конкретные рекомендации"],
                            "key_insights": ["массив строк - ключевые инсайты"],
                            "confidence_score": число от 0 до 1
                        }"""
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": 0.7,
                "max_tokens": self.max_tokens
            }

            headers = {
                "Authorization": f"Bearer {self._access_token}",
                "Content-Type": "application/json",
                "Accept": "application/json"
            }

            logger.info("Sending analysis request to GigaChat...")

            response = await self.client.post(chat_url, json=request_data, headers=headers)

            if response.status_code == 429:
                logger.warning(
                    "GigaChat rate limit exceeded for analysis request")
                return None

            if response.status_code != 200:
                logger.error(f"GigaChat API error {
                             response.status_code}: {response.text}")
                return None

            result = response.json()

            if "choices" not in result or len(result["choices"]) == 0:
                logger.error("No choices in GigaChat response")
                return None

            content = result["choices"][0]["message"]["content"]

            logger.info("GigaChat analysis received successfully")

            try:
                parsed_content = json.loads(content)
                return GigaChatAnalysis(**parsed_content)
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(
                    f"Failed to parse GigaChat response as JSON: {e}")

                # Пробуем извлечь JSON из текста
                import re
                json_match = re.search(r'\{.*\}', content, re.DOTALL)
                if json_match:
                    try:
                        json_str = json_match.group(0)
                        parsed_content = json.loads(json_str)
                        return GigaChatAnalysis(**parsed_content)
                    except:
                        logger.warning("Could not extract JSON from response")

                # Если не удалось распарсить JSON, создаем структурированный ответ
                logger.info("Creating structured response from text")
                return GigaChatAnalysis(
                    overall_assessment=content[:500],
                    strengths=["Анализ выполнен, но в текстовом формате"],
                    areas_for_improvement=[],
                    detailed_recommendations=[
                        f"Полный текст анализа: {content[:1000]}"],
                    key_insights=["Ответ GigaChat не в формате JSON"],
                    confidence_score=0.3
                )

        except httpx.RequestError as e:
            logger.error(f"GigaChat API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing GigaChat response: {e}")
            return None

    def _create_analysis_prompt(self, analysis_result: AnalysisResult) -> str:
        """Создает промпт для анализа на основе результатов"""
        filler_items = ""
        for item in analysis_result.filler_words.items:
            if item.get("count", 0) > 0:
                filler_items += f"- {item['word']}: {item['count']} раз\n"

        pauses_info = ""
        if analysis_result.pauses.long_pauses:
            pauses_info = "Длинные паузы:\n"
            for pause in analysis_result.pauses.long_pauses[:3]:
                pauses_info += f"- {pause['duration']:.1f} сек (с {pause['start']:.1f} по {
                    pause['end']:.1f})\n"

        advice_info = ""
        for advice in analysis_result.advice:
            advice_info += f"- {advice.title}: {advice.observation}\n"

        prompt = f"""Проанализируй это публичное выступление:

=== ТРАНСКРИПТ ===
{analysis_result.transcript[:3000]}{'... [текст сокращен]' if len(analysis_result.transcript) > 3000 else ''}

=== МЕТРИКИ ===
Длительность: {analysis_result.duration_sec:.1f} секунд
Время говорения: {analysis_result.speaking_time_sec:.1f} секунд
Коэффициент говорения: {analysis_result.speaking_ratio:.2%}
Темп речи: {analysis_result.words_per_minute:.1f} слов/минуту
Общее количество слов: {analysis_result.words_total}

Слова-паразиты: {analysis_result.filler_words.total} ({analysis_result.filler_words.per_100_words:.1f} на 100 слов)
{f'Наиболее частые:\n{filler_items}' if filler_items else ''}

Количество пауз: {analysis_result.pauses.count}
Средняя длина паузы: {analysis_result.pauses.avg_sec:.1f} секунд
Самая длинная пауза: {analysis_result.pauses.max_sec:.1f} секунд
{pauses_info if pauses_info else ''}

Количество фраз: {analysis_result.phrases.count}
Средняя длина фразы: {analysis_result.phrases.avg_words:.1f} слов
Классификация длины фраз: {analysis_result.phrases.length_classification}
Вариативность ритма: {analysis_result.phrases.rhythm_variation}

=== СТАНДАРТНЫЕ РЕКОМЕНДАЦИИ ===
{advice_info}

Дай развернутый анализ с учетом контекста публичного выступления.
Обрати внимание на:
1. Ясность и структурированность мысли
2. Эмоциональную окраску речи
3. Убедительность аргументации
4. Взаимодействие с аудиторией (на основе пауз и темпа)
5. Профессиональную лексику и терминологию
6. Общее впечатление от выступления

Верни ответ строго в формате JSON, как указано в system prompt."""

        return prompt

    async def close(self):
        """Закрывает HTTP-клиент"""
        await self.client.aclose()

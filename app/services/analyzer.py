from typing import List, Dict, Tuple
import re
import wave
import struct
import math
from pathlib import Path

from app.models.transcript import Transcript, TranscriptSegment
from app.models.analysis import (
    AnalysisResult,
    FillerWordsStats,
    PausesStats,
    PhraseStats,
    AdviceItem,
)

# --------------------
# Константы "нормы"
# --------------------

# Порог разрыва между фразами, чтобы считать его паузой (сек)
MIN_PAUSE_GAP_SEC = 0.5

# Диапазон комфортной скорости речи (слов в минуту)
MIN_COMFORT_WPM = 100.0
MAX_COMFORT_WPM = 180.0

# Пауза считается "длинной", если длится дольше этого времени (сек)
LONG_PAUSE_SEC = 2.5

# Насколько тише должна быть пауза относительно медианной громкости речи,
# чтобы считать её настоящей тишиной (0.0–1.0)
SILENCE_FACTOR = 0.35

# Максимальное отклонение по времени (сек) при сопоставлении
# начала паузы и конца сегмента речи
PAUSE_SEGMENT_TIME_TOLERANCE = 0.25

# --------------------
# Слова-паразиты (логически упорядочены)
# --------------------
#
# Группы:
#  1) Русские звучания и частицы
#  2) Русские вводные/конструкции
#  3) Английские звучания
#  4) Английские вводные/конструкции

FILLER_DEFINITIONS: List[Tuple[str, str]] = [
    # 1. Русские: базовые звучания и короткие частицы
    ("э-э", r"\bэ+([- ]э+)*\b"),
    ("ну", r"\bну\b"),
    ("вот", r"\bвот\b"),

    # 2. Русские: конструкции и вводные слова
    ("как бы", r"\bкак бы\b"),
    ("типа", r"\bтипа\b"),
    ("то есть", r"\bто есть\b"),
    ("значит", r"\bзначит\b"),
    ("получается", r"\bполучается\b"),
    ("собственно", r"\bсобственно\b"),
    ("вообще-то", r"\bвообще-то\b"),
    ("как сказать", r"\bкак сказать\b"),
    ("в общем", r"\bв общем\b"),
    ("короче", r"\bкороче\b"),
    ("скажем так", r"\bскажем так\b"),
    ("так сказать", r"\bтак сказать\b"),
    ("это самое", r"\bэто самое\b"),
    ("как его", r"\bкак его\b"),
    ("вот этот вот", r"\bвот этот вот\b"),

    # 3. Английские: базовые звучания
    ("uh", r"\buh+\b"),
    ("um", r"\bum+\b"),
    ("er", r"\ber+\b"),
    ("ah", r"\bah+\b"),

    # 4. Английские: вводные слова и конструкции
    ("like", r"\blike\b"),
    ("so", r"\bso\b"),
    ("well", r"\bwell\b"),
    ("right", r"\bright\b"),
    ("you know", r"\byou know\b"),
    ("i mean", r"\bi mean\b"),
    ("kind of", r"\bkind of\b"),
    ("sort of", r"\bsort of\b"),
    ("you see", r"\byou see\b"),
    ("basically", r"\bbasically\b"),
    ("actually", r"\bactually\b"),
    ("literally", r"\bliterally\b"),
    ("okay", r"\bokay\b"),
    ("ok", r"\bok\b"),
    ("alright", r"\balright\b"),
]

COMPILED_FILLERS: List[Tuple[str, re.Pattern]] = [
    (name, re.compile(pattern, flags=re.IGNORECASE | re.MULTILINE))
    for name, pattern in FILLER_DEFINITIONS
]


class SpeechAnalyzer:
    """
    Анализирует транскрипт и формирует метрики/советы.
    Использует аудио для более умного анализа пауз
    (отсеивание аплодисментов и громкого шума).
    """

    def analyze(
        self,
        transcript: Transcript,
        audio_path: Path | None = None,
    ) -> AnalysisResult:
        segments = transcript.segments
        if not segments:
            duration_sec = 0.0
        else:
            duration_sec = float(segments[-1].end)

        full_text = transcript.text or ""
        words = self._split_words(full_text)
        words_total = len(words)

        # Время говорения и "сырые" паузы (по сегментам распознавания)
        speaking_time_sec = 0.0
        pauses_raw: List[Dict[str, float]] = []
        last_end = None

        for seg in segments:
            start = float(seg.start)
            end = float(seg.end)
            speaking_time_sec += max(0.0, end - start)
            if last_end is not None:
                gap = start - last_end
                if gap >= MIN_PAUSE_GAP_SEC:
                    pauses_raw.append(
                        {"start": last_end, "end": start, "duration": gap}
                    )
            last_end = end

        # Фильтрация "пауз" по уровню громкости относительно речи спикера
        if audio_path is not None and pauses_raw:
            pauses_filtered = self._filter_noisy_pauses(
                audio_path, pauses_raw, segments
            )
        else:
            pauses_filtered = pauses_raw

        # Скорость речи
        words_per_minute = 0.0
        if speaking_time_sec > 0 and words_total > 0:
            words_per_minute = words_total / (speaking_time_sec / 60.0)

        # Коэффициент говорения: доля времени, когда спикер говорит
        speaking_ratio = (
            speaking_time_sec / duration_sec if duration_sec > 0 else 0.0
        )

        filler_total, filler_detail = self._count_fillers(full_text)
        pauses_stats = self._summarize_pauses(pauses_filtered)
        phrase_stats = self._build_phrase_stats(segments, pauses_filtered)
        advice = self._generate_advice(
            words_per_minute, filler_total, words_total, pauses_stats, phrase_stats
        )

        # Формируем статистику по словам-паразитам
        items = [
            {"word": name, "count": filler_detail.get(name, 0)}
            for name, _ in COMPILED_FILLERS
        ]

        filler_stats = FillerWordsStats(
            total=filler_total,
            per_100_words=round(
                (filler_total / words_total * 100), 1
            ) if words_total else 0.0,
            items=items,
        )

        return AnalysisResult(
            duration_sec=duration_sec,
            speaking_time_sec=round(speaking_time_sec, 2),
            speaking_ratio=round(speaking_ratio, 3),
            words_total=words_total,
            words_per_minute=round(words_per_minute, 1),
            filler_words=filler_stats,
            pauses=pauses_stats,
            phrases=phrase_stats,
            advice=advice,
            transcript=full_text,
        )

    # --------------------
    # Вспомогательные методы
    # --------------------

    @staticmethod
    def _split_words(text: str) -> List[str]:
        return re.findall(r"[A-Za-zА-Яа-яЁё0-9]+", text.lower())

    @staticmethod
    def _count_fillers(text: str) -> Tuple[int, Dict[str, int]]:
        counts: Dict[str, int] = {}
        total = 0
        for name, pattern in COMPILED_FILLERS:
            c = len(pattern.findall(text))
            counts[name] = c
            total += c
        return total, counts

    @staticmethod
    def _filter_noisy_pauses(
        audio_path: Path,
        pauses: List[Dict[str, float]],
        segments: List[TranscriptSegment],
    ) -> List[Dict[str, float]]:
        """
        Оставляем только действительно тихие паузы.

        Алгоритм:
        - читаем WAV (моно 16-bit 16 kHz),
        - считаем RMS по каждому речевому сегменту -> список громкостей речи;
        - берём медиану RMS речи как "типичную громкость голоса";
        - считаем RMS для каждой паузы;
        - если RMS паузы < SILENCE_FACTOR * median_speech_rms -> это пауза,
          иначе -> шум (аплодисменты, толпа, музыка).
        """
        try:
            with wave.open(str(audio_path), "rb") as wf:
                n_channels, sampwidth, framerate, n_frames, comptype, compname = (
                    wf.getparams()
                )

                # Ожидаем моно 16-bit PCM
                if n_channels != 1 or sampwidth != 2:
                    return pauses

                frames = wf.readframes(n_frames)
        except Exception:
            # Не смогли прочитать аудио — не трогаем паузы
            return pauses

        num_samples = len(frames) // 2  # 2 байта на сэмпл (int16)
        if num_samples == 0:
            return pauses

        samples = struct.unpack("<{}h".format(num_samples), frames)

        def segment_rms(start_idx: int, end_idx: int) -> float:
            count = end_idx - start_idx
            if count <= 0:
                return 0.0
            sum_sq = 0
            for i in range(start_idx, end_idx):
                v = samples[i]
                sum_sq += v * v
            return math.sqrt(sum_sq / count)

        # 1) RMS по речевым сегментам
        speech_rms_values: List[float] = []
        for seg in segments:
            start_s = float(seg.start)
            end_s = float(seg.end)
            start_idx = max(0, int(start_s * framerate))
            end_idx = min(num_samples, int(end_s * framerate))
            # короткие сегменты (<0.2с) пропускаем
            if end_idx - start_idx < int(0.2 * framerate):
                continue
            r = segment_rms(start_idx, end_idx)
            if r > 0:
                speech_rms_values.append(r)

        if not speech_rms_values:
            # Не смогли оценить громкость речи — не фильтруем паузы
            return pauses

        # Медиана RMS речи
        speech_rms_values.sort()
        median_speech_rms = speech_rms_values[len(speech_rms_values) // 2]

        silence_threshold = median_speech_rms * SILENCE_FACTOR

        filtered: List[Dict[str, float]] = []

        for p in pauses:
            start_s = p["start"]
            end_s = p["end"]
            if end_s <= start_s:
                continue

            start_idx = max(0, int(start_s * framerate))
            end_idx = min(num_samples, int(end_s * framerate))
            if end_idx <= start_idx:
                continue

            r = segment_rms(start_idx, end_idx)

            # Если пауза заметно тише речи — считаем настоящей паузой
            if r < silence_threshold:
                filtered.append(p)
            else:
                # громкий отрезок (аплодисменты/шум) — не считаем паузой
                continue

        return filtered

    @staticmethod
    def _summarize_pauses(pauses: List[Dict[str, float]]) -> PausesStats:
        if not pauses:
            return PausesStats(
                count=0,
                avg_sec=0.0,
                max_sec=0.0,
                long_pauses=[],
            )
        durations = [p["duration"] for p in pauses]
        count = len(pauses)
        avg_sec = sum(durations) / count
        max_sec = max(durations)

        # Длинные паузы (>= LONG_PAUSE_SEC)
        long_pauses = [
            {
                "start": round(p["start"], 2),
                "end": round(p["end"], 2),
                "duration": round(p["duration"], 2),
            }
            for p in pauses
            if p["duration"] >= LONG_PAUSE_SEC
        ]
        # Топ-3 самых длинных
        long_pauses = sorted(long_pauses, key=lambda p: p["duration"], reverse=True)[
            :3
        ]

        return PausesStats(
            count=count,
            avg_sec=round(avg_sec, 2),
            max_sec=round(max_sec, 2),
            long_pauses=long_pauses,
        )

    def _build_phrase_stats(
        self,
        segments: List[TranscriptSegment],
        pauses: List[Dict[str, float]],
    ) -> PhraseStats:
        """
        Строим фразы как последовательности сегментов между "тихими" паузами.
        """

        if not segments:
            return PhraseStats(
                count=0,
                avg_words=0.0,
                avg_duration_sec=0.0,
                min_words=0,
                max_words=0,
                min_duration_sec=0.0,
                max_duration_sec=0.0,
                length_classification="insufficient_data",
                rhythm_variation="insufficient_data",
            )

        # Определяем, после каких сегментов есть пауза
        boundary_after_idx = set()  # индексы сегментов, после которых стоит пауза
        for p in pauses:
            pause_start = p["start"]
            best_idx = None
            best_diff = float("inf")
            for i, seg in enumerate(segments):
                diff = abs(float(seg.end) - pause_start)
                if diff < best_diff:
                    best_diff = diff
                    best_idx = i
            if best_idx is not None and best_diff <= PAUSE_SEGMENT_TIME_TOLERANCE:
                boundary_after_idx.add(best_idx)

        phrases_durations: List[float] = []
        phrases_words: List[int] = []

        phrase_start_idx = 0

        for idx in range(len(segments)):
            is_boundary = idx in boundary_after_idx
            is_last_seg = idx == len(segments) - 1

            if is_boundary:
                # фраза заканчивается на этом сегменте
                phrase_end_idx = idx
                segs = segments[phrase_start_idx: phrase_end_idx + 1]
                if segs:
                    dur, wcount = self._phrase_metrics(segs)
                    if wcount > 0 and dur > 0:
                        phrases_durations.append(dur)
                        phrases_words.append(wcount)
                # следующая фраза начинается со следующего сегмента
                phrase_start_idx = idx + 1

            if is_last_seg and phrase_start_idx <= idx:
                # закрываем последнюю фразу (если не закрыли выше)
                segs = segments[phrase_start_idx: idx + 1]
                if segs:
                    dur, wcount = self._phrase_metrics(segs)
                    if wcount > 0 and dur > 0:
                        phrases_durations.append(dur)
                        phrases_words.append(wcount)

        if not phrases_words:
            return PhraseStats(
                count=0,
                avg_words=0.0,
                avg_duration_sec=0.0,
                min_words=0,
                max_words=0,
                min_duration_sec=0.0,
                max_duration_sec=0.0,
                length_classification="insufficient_data",
                rhythm_variation="insufficient_data",
            )

        count = len(phrases_words)
        avg_words = sum(phrases_words) / count
        avg_dur = sum(phrases_durations) / count

        min_words = min(phrases_words)
        max_words = max(phrases_words)
        min_dur = min(phrases_durations)
        max_dur = max(phrases_durations)

        # Классификация по длине фраз
        if avg_words < 8:
            length_class = "short_phrases"
        elif avg_words <= 25:
            length_class = "balanced"
        else:
            length_class = "long_phrases"

        # Вариативность ритма (коэффициент вариации по длительности фраз)
        if count < 2 or avg_dur <= 0:
            rhythm_var = "insufficient_data"
        else:
            mean_dur = avg_dur
            var = sum((d - mean_dur) ** 2 for d in phrases_durations) / count
            std = math.sqrt(var)
            cv = std / mean_dur
            if cv < 0.25:
                rhythm_var = "uniform"
            elif cv < 0.6:
                rhythm_var = "moderately_variable"
            else:
                rhythm_var = "highly_variable"

        return PhraseStats(
            count=count,
            avg_words=round(avg_words, 1),
            avg_duration_sec=round(avg_dur, 2),
            min_words=min_words,
            max_words=max_words,
            min_duration_sec=round(min_dur, 2),
            max_duration_sec=round(max_dur, 2),
            length_classification=length_class,
            rhythm_variation=rhythm_var,
        )

    def _phrase_metrics(
        self,
        segs: List[TranscriptSegment],
    ) -> Tuple[float, int]:
        """
        Возвращает (длительность_фразы_сек, количество_слов_во_фразе).
        """
        if not segs:
            return 0.0, 0
        start = float(segs[0].start)
        end = float(segs[-1].end)
        duration = max(0.0, end - start)
        text = " ".join(s.text for s in segs)
        words = self._split_words(text)
        return duration, len(words)

    @staticmethod
    def _generate_advice(
        words_per_minute: float,
        filler_total: int,
        words_total: int,
        pauses_stats: PausesStats,
        phrase_stats: PhraseStats,
    ) -> List[AdviceItem]:
        advice: List[AdviceItem] = []

        # --- 1. Темп речи ---
        if words_total == 0 or words_per_minute == 0:
            speech_observation = (
                "Автоматический анализ темпа речи затруднён: "
                "объём распознанного текста или длительность фрагмента слишком малы."
            )
            speech_recommendation = (
                "Запишите более продолжительный фрагмент с отчётливой речью "
                "для получения корректной оценки темпа."
            )
            speech_severity = "info"
        elif words_per_minute < MIN_COMFORT_WPM:
            speech_observation = (
                "Оценённый темп речи составляет примерно {wpm:.1f} слов в минуту, "
                "что ниже типичного диапазона публичных выступлений "
                "({min_wpm:.0f}–{max_wpm:.0f} слов в минуту)."
            ).format(
                wpm=words_per_minute,
                min_wpm=MIN_COMFORT_WPM,
                max_wpm=MAX_COMFORT_WPM,
            )
            speech_recommendation = (
                "Если цель — более динамичная подача материала, имеет смысл немного ускорить речь, "
                "сократив избыточные паузы и используя более короткие формулировки."
            )
            speech_severity = "suggestion"
        elif words_per_minute > MAX_COMFORT_WPM:
            speech_observation = (
                "Оценённый темп речи составляет примерно {wpm:.1f} слов в минуту, "
                "что выше типичного диапазона публичных выступлений "
                "({min_wpm:.0f}–{max_wpm:.0f} слов в минуту)."
            ).format(
                wpm=words_per_minute,
                min_wpm=MIN_COMFORT_WPM,
                max_wpm=MAX_COMFORT_WPM,
            )
            speech_recommendation = (
                "Рекомендуется слегка замедлить подачу, делая более заметные логические паузы "
                "и подчёркивая ключевые фразы, чтобы слушателям было проще следить за мыслью."
            )
            speech_severity = "suggestion"
        else:
            speech_observation = (
                "Оценённый темп речи составляет примерно {wpm:.1f} слов в минуту, "
                "что находится в пределах типичного диапазона публичных выступлений."
            ).format(wpm=words_per_minute)
            speech_recommendation = (
                "Сохраняйте выбранный темп и при необходимости варьируйте его для "
                "подчёркивания ключевых смысловых блоков."
            )
            speech_severity = "info"

        advice.append(
            AdviceItem(
                category="speech_rate",
                severity=speech_severity,  # type: ignore[arg-type]
                title="Темп речи",
                observation=speech_observation,
                recommendation=speech_recommendation,
            )
        )

        # --- 2. Слова-паразиты ---
        fillers_per_100 = (filler_total / words_total *
                           100) if words_total else 0.0

        if filler_total == 0:
            filler_observation = (
                "В распознанном фрагменте не обнаружено типичных слов-паразитов "
                "на русском или английском языках."
            )
            filler_recommendation = (
                "Сохраняйте текущий уровень контроля речи: отсутствие слов-паразитов "
                "создаёт впечатление уверенного и подготовленного выступления."
            )
            filler_severity = "info"
        elif fillers_per_100 <= 3:
            filler_observation = (
                "Слова-паразиты присутствуют, но их доля невелика — порядка "
                "{value:.1f} на каждые 100 слов."
            ).format(value=fillers_per_100)
            filler_recommendation = (
                "Такой уровень слов-паразитов обычно не мешает восприятию. "
                "При желании можно дополнительно снизить их количество за счёт "
                "осознанных пауз и более точных формулировок."
            )
            filler_severity = "info"
        elif fillers_per_100 <= 8:
            filler_observation = (
                "Доля слов-паразитов составляет примерно {value:.1f} на каждые 100 слов, "
                "что может слегка утяжелять восприятие речи."
            ).format(value=fillers_per_100)
            filler_recommendation = (
                "Рекомендуется обратить внимание на наиболее часто повторяющиеся конструкции "
                "(например, «как бы», «типа», «you know», «like») и осознанно заменять их "
                "короткими паузами или нейтральными связками."
            )
            filler_severity = "suggestion"
        else:
            filler_observation = (
                "Доля слов-паразитов составляет примерно {value:.1f} на каждые 100 слов. "
                "Это достаточно высокий показатель, который заметно снижает чёткость речи."
            ).format(value=fillers_per_100)
            filler_recommendation = (
                "Рекомендуется специально потренировать фрагменты выступления без слов-паразитов, "
                "используя записи и самопроверку. Полезно делать сознательные паузы "
                "вместо автоматических вставок («ну», «типа», «как бы», «uh», «um» и т.п.)."
            )
            filler_severity = "warning"

        advice.append(
            AdviceItem(
                category="filler_words",
                severity=filler_severity,  # type: ignore[arg-type]
                title="Слова-паразиты",
                observation=filler_observation,
                recommendation=filler_recommendation,
            )
        )

        # --- 3. Паузы ---
        if pauses_stats.count == 0:
            pauses_observation = (
                "В записи практически отсутствуют выделенные паузы между фрагментами речи."
            )
            pauses_recommendation = (
                "Иногда полезно сознательно использовать короткие паузы для "
                "выделения ключевых мыслей и структурирования повествования."
            )
            pauses_severity = "info"
        else:
            long_count = len(pauses_stats.long_pauses)
            long_fraction = (
                long_count / pauses_stats.count if pauses_stats.count > 0 else 0.0
            )

            if long_count > 0 and long_fraction > 0.3:
                pauses_observation = (
                    "В речи обнаружены длинные паузы (до {max_sec:.1f} секунд), "
                    "и их доля среди всех пауз достаточно велика."
                ).format(max_sec=pauses_stats.max_sec)
                pauses_recommendation = (
                    "Рекомендуется заранее продумывать переходы между блоками выступления, "
                    "чтобы заполнять длинные паузы чёткими вводными фразами или кратким "
                    "резюме предыдущей части."
                )
                pauses_severity = "suggestion"
            else:
                pauses_observation = (
                    "В речи присутствуют паузы (средняя длительность около "
                    "{avg_sec:.1f} секунд), их использование выглядит естественным."
                ).format(avg_sec=pauses_stats.avg_sec)
                pauses_recommendation = (
                    "Сохраняйте подобный баланс: паузы помогают аудитории обрабатывать информацию "
                    "и воспринимать структуру выступления."
                )
                pauses_severity = "info"

        advice.append(
            AdviceItem(
                category="pauses",
                severity=pauses_severity,  # type: ignore[arg-type]
                title="Паузы в речи",
                observation=pauses_observation,
                recommendation=pauses_recommendation,
            )
        )

        # --- 4. Структура фраз ---
        if phrase_stats.count <= 1:
            phr_observation = (
                "Автоматический анализ структуры фраз затруднён: "
                "в записи выделен один непрерывный фрагмент речи без явных пауз "
                "между смысловыми блоками."
            )
            phr_recommendation = (
                "Для более чёткой структуры выступления имеет смысл сознательно "
                "использовать паузы между завершёнными мыслями и логическими частями."
            )
            phr_severity = "info"
        else:
            phr_observation = (
                "Средняя длина фразы составляет около {avg_words:.1f} слов "
                "(примерно {avg_dur:.1f} секунд). "
            ).format(
                avg_words=phrase_stats.avg_words,
                avg_dur=phrase_stats.avg_duration_sec,
            )

            if phrase_stats.length_classification == "short_phrases":
                phr_observation += (
                    "Фразы в основном короткие, структура может восприниматься несколько "
                    "фрагментированной."
                )
                phr_recommendation = (
                    "При необходимости можно объединять близкие по смыслу предложения в более "
                    "цельные фразы, чтобы улучшить связность повествования."
                )
                phr_severity = "suggestion"
            elif phrase_stats.length_classification == "long_phrases":
                phr_observation += (
                    "Фразы в среднем достаточно длинные, что может усложнять восприятие сложных "
                    "участков текста на слух."
                )
                phr_recommendation = (
                    "Рекомендуется разбивать особо длинные фразы на более короткие смысловые единицы, "
                    "добавляя паузы и явные логические связки."
                )
                phr_severity = "suggestion"
            else:  # balanced
                phr_observation += (
                    "Длина фраз выглядит сбалансированной для устного выступления."
                )
                phr_recommendation = (
                    "Сохраняйте подобную структуру: чередование фраз средней длины делает речь "
                    "более предсказуемой и удобной для восприятия."
                )
                phr_severity = "info"

            if phrase_stats.rhythm_variation == "uniform":
                phr_observation += (
                    " Длительность фраз и пауз относительно равномерна, ритм выступления стабилен."
                )
            elif phrase_stats.rhythm_variation == "moderately_variable":
                phr_observation += (
                    " Вариативность длительности фраз и пауз умеренная, что поддерживает внимание аудитории."
                )
            elif phrase_stats.rhythm_variation == "highly_variable":
                phr_observation += (
                    " Длительность фраз и пауз заметно варьируется, ритм выступления может "
                    "восприниматься неравномерным."
                )

        advice.append(
            AdviceItem(
                category="phrasing",
                severity=phr_severity,  # type: ignore[arg-type]
                title="Структура фраз",
                observation=phr_observation,
                recommendation=phr_recommendation,
            )
        )

        return advice

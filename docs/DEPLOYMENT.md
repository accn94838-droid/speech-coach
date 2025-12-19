# 🚀 Deployment Guide

Production deployment guide for Speech Coach application.

## Pre-Deployment Checklist

- [ ] Code reviewed and tested locally
- [ ] All environment variables documented
- [ ] Database migrations prepared
- [ ] Security scan completed
- [ ] Performance testing done
- [ ] Monitoring configured
- [ ] Backup strategy in place
- [ ] Rollback plan prepared

---

## Deployment Environments

### Development
- Single server
- Auto-reload enabled
- Debug mode ON
- SQLite database
- File-based cache

### Staging
- Load balancer + 2 app servers
- Debug mode OFF
- PostgreSQL database
- Redis cache
- SSL enabled
- Same config as production

### Production
- Load balancer + 3+ app servers
- Debug mode OFF
- PostgreSQL with replication
- Redis cluster for cache
- SSL certificates
- Monitoring/alerting active
- Daily backups enabled

---

## Docker Deployment

### Building Image

```bash
# Build image
docker build -t speech-coach:latest .

# Tag for registry
docker tag speech-coach:latest registry.example.com/speech-coach:latest

# Push to registry
docker push registry.example.com/speech-coach:latest
```

### Running Container

#### Single Container

```bash
docker run -d \
  --name speech-coach \
  -p 8000:8000 \
  -v /app/config/.env:/app/.env:ro \
  -v /app/logs:/app/logs \
  -e ENVIRONMENT=production \
  -e LOG_LEVEL=INFO \
  --restart unless-stopped \
  registry.example.com/speech-coach:latest
```

#### Docker Compose

```yaml
version: '3.8'

services:
  app:
    image: registry.example.com/speech-coach:latest
    ports:
      - "8000:8000"
    environment:
      - ENVIRONMENT=production
      - LOG_LEVEL=INFO
      - CACHE_BACKEND=redis
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://user:pass@postgres:5432/speech_coach
    volumes:
      - /app/config/.env:/app/.env:ro
      - /app/logs:/app/logs
      - /app/cache:/tmp/speech-coach-cache
    depends_on:
      - postgres
      - redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=speech_coach
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis-data:/data
    restart: unless-stopped

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - /app/ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres-data:
  redis-data:
```

---

## Kubernetes Deployment

### Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: speech-coach
  namespace: default
spec:
  replicas: 3
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 1
      maxUnavailable: 0
  selector:
    matchLabels:
      app: speech-coach
  template:
    metadata:
      labels:
        app: speech-coach
    spec:
      containers:
      - name: app
        image: registry.example.com/speech-coach:latest
        imagePullPolicy: IfNotPresent
        ports:
        - containerPort: 8000
          name: http
        env:
        - name: ENVIRONMENT
          value: "production"
        - name: LOG_LEVEL
          value: "INFO"
        - name: REDIS_URL
          value: "redis://redis-service:6379/0"
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: speech-coach-secrets
              key: database-url
        - name: GIGACHAT_API_KEY
          valueFrom:
            secretKeyRef:
              name: speech-coach-secrets
              key: gigachat-api-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        volumeMounts:
        - name: logs
          mountPath: /app/logs
      volumes:
      - name: logs
        emptyDir: {}

---
apiVersion: v1
kind: Service
metadata:
  name: speech-coach-service
spec:
  selector:
    app: speech-coach
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Secrets

```bash
# Create secrets
kubectl create secret generic speech-coach-secrets \
  --from-literal=database-url=postgresql://user:pass@postgres:5432/speech_coach \
  --from-literal=gigachat-api-key=your-api-key

# Apply deployment
kubectl apply -f deployment.yaml
```

---

## Traditional Server Deployment (Ubuntu/Debian)

### 1. System Setup

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
  python3.9 \
  python3.9-venv \
  ffmpeg \
  postgresql \
  redis-server \
  nginx \
  supervisor \
  curl

# Create application user
sudo useradd -m -s /bin/bash speech-coach
```

### 2. Clone Repository

```bash
sudo -u speech-coach git clone \
  https://github.com/your-org/speech-coach.git \
  /home/speech-coach/app

cd /home/speech-coach/app
sudo chown -R speech-coach:speech-coach .
```

### 3. Setup Virtual Environment

```bash
cd /home/speech-coach/app

# Create venv
python3.9 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Collect static files (if applicable)
python manage.py collectstatic --noinput
```

### 4. Configure Environment

```bash
# Copy and edit .env
cp .env.example .env
sudo nano .env

# Set permissions
sudo chmod 600 .env
sudo chown speech-coach:speech-coach .env
```

### 5. Setup PostgreSQL

```bash
# Connect to PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE USER speech_coach WITH PASSWORD 'strong-password';
CREATE DATABASE speech_coach OWNER speech_coach;
GRANT ALL PRIVILEGES ON DATABASE speech_coach TO speech_coach;

# Exit psql
\q
```

### 6. Run Database Migrations

```bash
cd /home/speech-coach/app
source venv/bin/activate

# Apply migrations (if using SQLAlchemy)
alembic upgrade head
```

### 7. Setup Gunicorn

Create `/home/speech-coach/app/gunicorn_config.py`:

```python
import multiprocessing

bind = "127.0.0.1:8000"
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

### 8. Setup Supervisor

Create `/etc/supervisor/conf.d/speech-coach.conf`:

```ini
[program:speech-coach]
user=speech-coach
directory=/home/speech-coach/app
command=/home/speech-coach/app/venv/bin/gunicorn app.main:app -c gunicorn_config.py
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/speech-coach/gunicorn.log
environment=PYTHONUNBUFFERED=1,ENVIRONMENT=production

[program:speech-coach-worker]
user=speech-coach
directory=/home/speech-coach/app
command=/home/speech-coach/app/venv/bin/python -m celery -A app.tasks worker -l info
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/speech-coach/worker.log
```

Update supervisor:

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start speech-coach
sudo supervisorctl start speech-coach-worker
```

### 9. Setup Nginx

Create `/etc/nginx/sites-available/speech-coach`:

```nginx
upstream speech_coach {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name api.example.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name api.example.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 100M;

    location / {
        proxy_pass http://speech_coach;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300;
    }

    location /static/ {
        alias /home/speech-coach/app/static/;
    }
}
```

Enable site:

```bash
sudo ln -s /etc/nginx/sites-available/speech-coach /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### 10. Setup SSL Certificate

```bash
# Using Let's Encrypt
sudo apt install certbot python3-certbot-nginx

sudo certbot certonly --nginx -d api.example.com
```

### 11. Setup Logs

```bash
# Create log directory
sudo mkdir -p /var/log/speech-coach
sudo chown speech-coach:speech-coach /var/log/speech-coach
sudo chmod 755 /var/log/speech-coach

# Setup log rotation
sudo tee /etc/logrotate.d/speech-coach > /dev/null <<EOF
/var/log/speech-coach/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
    create 0640 speech-coach speech-coach
    sharedscripts
    postrotate
        supervisorctl restart speech-coach 2>/dev/null || true
    endscript
}
EOF
```

---

## Cloud Deployment

### AWS Elastic Beanstalk

```bash
# Install EB CLI
pip install awsebcli

# Initialize
eb init -p docker speech-coach

# Create environment
eb create production --scale 3

# Deploy
eb deploy

# View logs
eb logs

# Monitor
eb health
```

### Google Cloud Run

```bash
# Build image
docker build -t speech-coach .

# Push to Container Registry
docker tag speech-coach gcr.io/PROJECT_ID/speech-coach
docker push gcr.io/PROJECT_ID/speech-coach

# Deploy
gcloud run deploy speech-coach \
  --image gcr.io/PROJECT_ID/speech-coach \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --timeout 300 \
  --set-env-vars ENVIRONMENT=production
```

### Heroku

```bash
# Login
heroku login

# Create app
heroku create speech-coach

# Add buildpacks
heroku buildpacks:add heroku/python
heroku buildpacks:add https://github.com/heroku-community/heroku-buildpack-apt

# Set environment
heroku config:set ENVIRONMENT=production
heroku config:set DEBUG=false

# Deploy
git push heroku main

# View logs
heroku logs --tail
```

---

## Monitoring & Logging

### Application Monitoring

```bash
# Install monitoring tools
pip install prometheus-client datadog

# Export metrics
PROMETHEUS_MULTIPROC_DIR=/tmp prometheus_multiproc_dir=/tmp gunicorn app.main:app
```

### Log Aggregation

```yaml
# ELK Stack
version: '3.8'

services:
  elasticsearch:
    image: docker.elastic.co/elasticsearch/elasticsearch:7.14.0
    environment:
      - discovery.type=single-node
    ports:
      - "9200:9200"

  kibana:
    image: docker.elastic.co/kibana/kibana:7.14.0
    ports:
      - "5601:5601"
    environment:
      - ELASTICSEARCH_HOSTS=http://elasticsearch:9200

  filebeat:
    image: docker.elastic.co/beats/filebeat:7.14.0
    volumes:
      - ./filebeat.yml:/usr/share/filebeat/filebeat.yml:ro
      - /var/log/speech-coach:/var/log/speech-coach:ro
```

---

## Scaling

### Horizontal Scaling

```bash
# Docker Compose
docker-compose up --scale app=3 -d

# Kubernetes
kubectl scale deployment speech-coach --replicas=5
```

### Vertical Scaling

```bash
# Update resource limits
kubectl set resources deployment speech-coach \
  --limits=cpu=1000m,memory=2Gi \
  --requests=cpu=500m,memory=1Gi
```

---

## Maintenance

### Database Backups

```bash
# PostgreSQL backup
pg_dump speech_coach > backup.sql

# Automated backup (cron)
0 2 * * * pg_dump speech_coach | gzip > /backup/$(date +%Y%m%d).sql.gz
```

### Updates

```bash
# Pull latest code
git pull origin main

# Rebuild image
docker build -t speech-coach:latest .

# Push to registry
docker push speech-coach:latest

# Redeploy
docker-compose up -d --no-deps --build app
```

---

## Troubleshooting

### Issue: High CPU Usage

```bash
# Check processes
top -b -n 1 | head -20

# Profile with cProfile
python -m cProfile -s cumtime app/main.py

# Reduce worker count
WHISPER_NUM_WORKERS=1
```

### Issue: Out of Memory

```bash
# Check memory
free -h

# Use smaller model
WHISPER_MODEL_SIZE=tiny

# Enable swap
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: Slow Requests

```bash
# Check logs
tail -f /var/log/speech-coach/gunicorn.log

# Enable query logging
LOG_LEVEL=DEBUG

# Use connection pooling
DATABASE_POOL_SIZE=10
```

---

**Last Updated**: December 19, 2025
**Version**: 1.0.0

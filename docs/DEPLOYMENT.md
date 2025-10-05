# FitHub Deployment Guide

## 🚀 Deployment Overview

FitHub is designed for easy deployment with Docker and includes a comprehensive CI/CD pipeline for automated deployments.

## 🐳 Docker Deployment

### Local Development with Docker

#### Using Docker Compose (Recommended)

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd fithub
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Start Services**
   ```bash
   docker-compose up -d
   ```

4. **Run Migrations**
   ```bash
   docker-compose exec web uv run manage.py migrate
   ```

5. **Create Superuser**
   ```bash
   docker-compose exec web uv run manage.py createsuperuser
   ```

6. **Access Application**
   - API: `http://localhost:8000`
   - Admin: `http://localhost:8000/admin/`
   - API Docs: `http://localhost:8000/api/docs/`

#### Using Docker Directly

1. **Build Image**
   ```bash
   docker build -t fithub .
   ```

2. **Run Container**
   ```bash
   docker run -d \
     --name fithub-app \
     -p 8000:8000 \
     -e POSTGRES_HOST=your-db-host \
     -e POSTGRES_DB=fithub \
     -e POSTGRES_USER=your-user \
     -e POSTGRES_PASSWORD=your-password \
     fithub
   ```

### Production Deployment

#### Docker Compose Production Setup

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
      - SECRET_KEY=your-secret-key
      - POSTGRES_HOST=db
      - POSTGRES_DB=fithub_prod
      - POSTGRES_USER=fithub_user
      - POSTGRES_PASSWORD=your-secure-password
    depends_on:
      - db
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    restart: unless-stopped

  db:
    image: postgres:16
    environment:
      - POSTGRES_DB=fithub_prod
      - POSTGRES_USER=fithub_user
      - POSTGRES_PASSWORD=your-secure-password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - static_volume:/app/static
      - media_volume:/app/media
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - web
    restart: unless-stopped

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

#### Nginx Configuration

Create `nginx.conf`:

```nginx
events {
    worker_connections 1024;
}

http {
    upstream web {
        server web:8000;
    }

    server {
        listen 80;
        server_name your-domain.com;
        return 301 https://$server_name$request_uri;
    }

    server {
        listen 443 ssl;
        server_name your-domain.com;

        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;

        location / {
            proxy_pass http://web;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /static/ {
            alias /app/static/;
        }

        location /media/ {
            alias /app/media/;
        }
    }
}
```

#### Deploy to Production

```bash
# Deploy with production compose file
docker-compose -f docker-compose.prod.yml up -d

# Run migrations
docker-compose -f docker-compose.prod.yml exec web uv run manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web uv run manage.py collectstatic --noinput

# Create superuser
docker-compose -f docker-compose.prod.yml exec web uv run manage.py createsuperuser
```

## ☁️ Cloud Deployment

### AWS Deployment

#### Using AWS ECS (Elastic Container Service)

1. **Push Image to ECR**
   ```bash
   # Create ECR repository
   aws ecr create-repository --repository-name fithub

   # Get login token
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

   # Build and push image
   docker build -t fithub .
   docker tag fithub:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/fithub:latest
   docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/fithub:latest
   ```

2. **Create ECS Task Definition**
   ```json
   {
     "family": "fithub",
     "networkMode": "awsvpc",
     "requiresCompatibilities": ["FARGATE"],
     "cpu": "256",
     "memory": "512",
     "executionRoleArn": "arn:aws:iam::<account-id>:role/ecsTaskExecutionRole",
     "containerDefinitions": [
       {
         "name": "fithub",
         "image": "<account-id>.dkr.ecr.us-east-1.amazonaws.com/fithub:latest",
         "portMappings": [
           {
             "containerPort": 8000,
             "protocol": "tcp"
           }
         ],
         "environment": [
           {
             "name": "POSTGRES_HOST",
             "value": "your-rds-endpoint"
           },
           {
             "name": "POSTGRES_DB",
             "value": "fithub"
           }
         ],
         "secrets": [
           {
             "name": "POSTGRES_PASSWORD",
             "valueFrom": "arn:aws:secretsmanager:us-east-1:<account-id>:secret:fithub/db-password"
           }
         ],
         "logConfiguration": {
           "logDriver": "awslogs",
           "options": {
             "awslogs-group": "/ecs/fithub",
             "awslogs-region": "us-east-1",
             "awslogs-stream-prefix": "ecs"
           }
         }
       }
     ]
   }
   ```

#### Using AWS App Runner

1. **Create apprunner.yaml**
   ```yaml
   version: 1.0
   runtime: docker
   build:
     commands:
       build:
         - echo "Build started on `date`"
         - echo "Build completed on `date`"
   run:
     runtime-version: latest
     command: uv run manage.py runserver 0.0.0.0:8000
     network:
       port: 8000
       env: PORT
     env:
       - name: POSTGRES_HOST
         value: your-rds-endpoint
       - name: POSTGRES_DB
         value: fithub
   ```

### Google Cloud Platform Deployment

#### Using Cloud Run

1. **Build and Deploy**
   ```bash
   # Build image
   gcloud builds submit --tag gcr.io/PROJECT-ID/fithub

   # Deploy to Cloud Run
   gcloud run deploy fithub \
     --image gcr.io/PROJECT-ID/fithub \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --set-env-vars POSTGRES_HOST=your-cloud-sql-ip
   ```

2. **Cloud Run Service Configuration**
   ```yaml
   apiVersion: serving.knative.dev/v1
   kind: Service
   metadata:
     name: fithub
     annotations:
       run.googleapis.com/ingress: all
   spec:
     template:
       metadata:
         annotations:
           run.googleapis.com/execution-environment: gen2
       spec:
         containers:
         - image: gcr.io/PROJECT-ID/fithub
           ports:
           - containerPort: 8000
           env:
           - name: POSTGRES_HOST
             value: your-cloud-sql-ip
           - name: POSTGRES_DB
             value: fithub
   ```

### Azure Deployment

#### Using Azure Container Instances

1. **Deploy Container**
   ```bash
   az container create \
     --resource-group myResourceGroup \
     --name fithub \
     --image your-registry.azurecr.io/fithub:latest \
     --dns-name-label fithub-app \
     --ports 8000 \
     --environment-variables \
       POSTGRES_HOST=your-azure-sql-server \
       POSTGRES_DB=fithub
   ```

## 🔄 CI/CD Pipeline

### GitHub Actions Deployment

The project includes automated deployment via GitHub Actions:

#### Pipeline Stages

1. **Code Quality** (Parallel)
   - Linting and formatting checks
   - Security vulnerability scanning

2. **Testing**
   - Unit tests with PostgreSQL containers
   - Coverage reporting

3. **Docker Build**
   - Multi-platform builds (linux/amd64, linux/arm64)
   - Push to DockerHub registry

4. **Deployment**
   - Automatic deployment on main branch
   - Environment-specific configurations

#### Deployment Configuration

Add these secrets to your GitHub repository:

- `DOCKERHUB_USERNAME`: Your DockerHub username
- `DOCKERHUB_TOKEN`: Your DockerHub access token
- `PRODUCTION_HOST`: Production server hostname
- `PRODUCTION_USER`: Production server username
- `PRODUCTION_SSH_KEY`: SSH private key for production server

#### Custom Deployment Script

Create `.github/scripts/deploy.sh`:

```bash
#!/bin/bash
set -e

# Deploy to production server
ssh -i $SSH_KEY $PRODUCTION_USER@$PRODUCTION_HOST << 'EOF'
  # Pull latest image
  docker pull zelenuk/fithub:latest
  
  # Stop existing container
  docker stop fithub-app || true
  docker rm fithub-app || true
  
  # Run new container
  docker run -d \
    --name fithub-app \
    -p 8000:8000 \
    -e POSTGRES_HOST=your-db-host \
    -e POSTGRES_DB=fithub \
    -e POSTGRES_USER=your-user \
    -e POSTGRES_PASSWORD=your-password \
    --restart unless-stopped \
    zelenuk/fithub:latest
  
  # Run migrations
  docker exec fithub-app uv run manage.py migrate
  
  # Collect static files
  docker exec fithub-app uv run manage.py collectstatic --noinput
EOF
```

## 🗄️ Database Setup

### PostgreSQL Configuration

#### Production Database Setup

1. **Create Database**
   ```sql
   CREATE DATABASE fithub_prod;
   CREATE USER fithub_user WITH PASSWORD 'secure_password';
   GRANT ALL PRIVILEGES ON DATABASE fithub_prod TO fithub_user;
   ```

2. **Connection Configuration**
   ```python
   # settings.py
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.postgresql',
           'NAME': os.environ.get('POSTGRES_DB', 'fithub'),
           'USER': os.environ.get('POSTGRES_USER', 'postgres'),
           'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
           'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
           'PORT': os.environ.get('POSTGRES_PORT', '5432'),
           'OPTIONS': {
               'sslmode': 'require',
           },
       }
   }
   ```

#### Database Migrations

```bash
# Create new migration
uv run manage.py makemigrations

# Apply migrations
uv run manage.py migrate

# Check migration status
uv run manage.py showmigrations
```

### Database Backups

#### Automated Backup Script

Create `scripts/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/backups/fithub"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/fithub_backup_$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB > $BACKUP_FILE

# Compress backup
gzip $BACKUP_FILE

# Remove backups older than 30 days
find $BACKUP_DIR -name "*.sql.gz" -mtime +30 -delete

echo "Backup created: $BACKUP_FILE.gz"
```

#### Restore from Backup

```bash
# Restore from backup
gunzip -c backup_file.sql.gz | psql -h $POSTGRES_HOST -U $POSTGRES_USER -d $POSTGRES_DB
```

## 🔒 Security Configuration

### Environment Variables

#### Required Environment Variables

```bash
# Django Settings
DEBUG=False
SECRET_KEY=your-very-secure-secret-key
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Database
POSTGRES_HOST=your-db-host
POSTGRES_DB=fithub_prod
POSTGRES_USER=fithub_user
POSTGRES_PASSWORD=your-secure-password

# Security
CSRF_TRUSTED_ORIGINS=https://your-domain.com
CORS_ALLOWED_ORIGINS=https://your-domain.com
```

#### Optional Environment Variables

```bash
# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password

# Static Files
STATIC_URL=https://your-cdn.com/static/
MEDIA_URL=https://your-cdn.com/media/

# Logging
LOG_LEVEL=INFO
```

### SSL/TLS Configuration

#### Let's Encrypt with Certbot

```bash
# Install Certbot
sudo apt-get install certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

#### Docker SSL Configuration

```dockerfile
# Add to Dockerfile
COPY ssl/cert.pem /etc/ssl/certs/
COPY ssl/key.pem /etc/ssl/private/
```

## 📊 Monitoring and Logging

### Application Monitoring

#### Health Check Endpoint

Create `health/views.py`:

```python
from django.http import JsonResponse
from django.db import connection
from django.core.cache import cache

def health_check(request):
    """Health check endpoint for monitoring"""
    try:
        # Check database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check cache
        cache.set('health_check', 'ok', 30)
        cache.get('health_check')
        
        return JsonResponse({
            'status': 'healthy',
            'database': 'connected',
            'cache': 'working'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy',
            'error': str(e)
        }, status=500)
```

#### Logging Configuration

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': '/var/log/fithub/django.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
}
```

### Performance Monitoring

#### Database Query Monitoring

```python
# settings.py
if DEBUG:
    LOGGING['loggers']['django.db.backends'] = {
        'level': 'DEBUG',
        'handlers': ['console'],
    }
```

#### Application Performance Monitoring

Consider integrating:
- **Sentry**: Error tracking and performance monitoring
- **New Relic**: Application performance monitoring
- **DataDog**: Infrastructure and application monitoring

## 🔧 Maintenance

### Regular Maintenance Tasks

#### Daily Tasks
- Monitor application logs
- Check database performance
- Verify backup completion

#### Weekly Tasks
- Review security logs
- Update dependencies
- Performance analysis

#### Monthly Tasks
- Security updates
- Database optimization
- Capacity planning

### Update Procedures

#### Application Updates

```bash
# Pull latest changes
git pull origin main

# Build new image
docker build -t fithub:latest .

# Deploy with zero downtime
docker-compose -f docker-compose.prod.yml up -d --no-deps web

# Run migrations
docker-compose -f docker-compose.prod.yml exec web uv run manage.py migrate

# Collect static files
docker-compose -f docker-compose.prod.yml exec web uv run manage.py collectstatic --noinput
```

#### Database Updates

```bash
# Backup before update
./scripts/backup.sh

# Apply migrations
uv run manage.py migrate

# Verify update
uv run manage.py check
```

### Troubleshooting

#### Common Issues

1. **Database Connection Issues**
   - Check database credentials
   - Verify network connectivity
   - Check database server status

2. **Static Files Not Loading**
   - Run `collectstatic` command
   - Check nginx configuration
   - Verify file permissions

3. **SSL Certificate Issues**
   - Check certificate expiration
   - Verify domain configuration
   - Renew certificate if needed

#### Log Analysis

```bash
# View application logs
docker-compose logs -f web

# View nginx logs
docker-compose logs -f nginx

# View database logs
docker-compose logs -f db
```

This deployment guide provides comprehensive instructions for deploying FitHub in various environments while maintaining security, performance, and reliability.

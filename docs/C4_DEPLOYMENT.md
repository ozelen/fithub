# FitHub C4 Deployment Diagram

## 🏗️ C4 Deployment Architecture

This document provides a C4-style deployment diagram for the FitHub fitness and nutrition tracking API.

## 📊 Deployment Diagram

```mermaid
C4Deployment
    title Deployment Diagram for FitHub API

    Deployment_Node(clientEnv, "Web App Environment", "CloudFlare"){
        Deployment_Node(webapp, "Web Application", "CF Pages/Workers"){
            Container(frontendApp, "Frontend App", "NextJS/Astro/React", "User Landing Pages")
        }
    }

    Deployment_Node(ci, "CI/CD", "GitHub Actions"){
        Container(githubActions, "CI Job", "GitHub Action", "Automated testing, linting, security checks, and Docker image building")
        Container(registry, "Docker Registry", "Docker Hub", "Stores FitHub Docker images for deployment")
    }

    Deployment_Node(vpc, "Virtual Private Cloud", "AWS VPC"){
        Deployment_Node(pubSubnet, "Public Subnet", "10.0.101.0/24, 10.0.102.0/24"){
            Container(alb, "Application Load Balancer", "AWS ALB", "Routes traffic to FitHub application instances")
        }

        Deployment_Node(prvSubnet, "Private Subnet", "10.0.1.0/24, 10.0.2.0/24"){
            Deployment_Node(cluster, "Orchestration Cluster", "AWS ECS"){
                Deployment_Node(fithubService, "FitHub Service", "ECS Service"){
                    Container(djangoApp, "Django App", "ECS Task", "Handles nutrition and goals API requests")
                    Container(djangoAppLogAgent, "Logging Agent", "Sidecar", "Handles nutrition and goals API requests")
                }
            }
            Deployment_Node(database, "Database Cluster", "AWS RDS"){
                Deployment_Node(postgres, "Primary Database", "PostgreSQL 16"){
                    ContainerDb(postgresDb, "FitHub Database", "PostgreSQL", "Stores user data, nutrition records, goals, and body measurements")
                }
            }
            Deployment_Node(elcache, "Caching Cluster", "ElastiCache") {
                ContainerDb(redis, "Redis KV", "Redis/ElastiCache", "Used as Agent short memory and Celery broker")
            }
        }

        Deployment_Node(monitoring, "Monitoring Stack", "DataDog"){
            Container(ddcollect, "Metrics Collection", "DD Collector", "Collects application and infrastructure metrics")
            Container(dddasboard, "Monitoring Dashboard", "DataDog", "Visualizes metrics and alerts")
        }
    }

    Rel(frontendApp, alb, "API Requests", "HTTPS")
    Rel(githubActions, registry, "Push Images", "Docker API")
    Rel(registry, djangoApp, "API Requests", "HTTPS")
    Rel(alb, djangoApp, "Routes Requests", "HTTP")
    Rel(djangoApp, postgresDb, "Read/Write", "PostgreSQL Protocol")
    Rel(djangoApp, redis, "Read/Write", "Redis Protocol")
    Rel(djangoAppLogAgent, djangoApp, "Collects", "HTTP")
    Rel(djangoAppLogAgent, ddcollect, "Metrics", "HTTP")
    Rel(ddcollect, dddasboard, "Data Source", "HTTP")
    
    UpdateRelStyle(frontendApp, alb, $offsetY="-40")
    UpdateRelStyle(githubActions, registry, $offsetY="-30")
    UpdateRelStyle(alb, djangoApp, $offsetY="-20", $offsetX="10")
    UpdateRelStyle(alb, fithubApp2, $offsetY="-20", $offsetX="-10")
    UpdateRelStyle(djangoApp, postgresDb, $offsetY="-10", $offsetX="5")
    UpdateRelStyle(postgresDb, postgresReplicaDb, $offsetY="-5")
    UpdateRelStyle(djangoApp, ddcollect, $offsetY="-30", $offsetX="20")
    UpdateRelStyle(ddcollect, dddasboard, $offsetY="-10")
```

## 🏗️ Local Development Deployment

```mermaid
C4Deployment
    title Local Development Deployment for FitHub

    Deployment_Node(developer, "Developer Machine", "Local Environment"){
        Deployment_Node(docker, "Docker Desktop", "Docker Engine"){
            Deployment_Node(web, "FitHub Web Container", "Docker Container"){
                Container(fithubWeb, "FitHub API", "Django + Python 3.13", "Development server with hot reload")
            }
            Deployment_Node(db, "PostgreSQL Container", "Docker Container"){
                ContainerDb(postgresLocal, "Local Database", "PostgreSQL 16", "Development database with test data")
            }
        }
        Container(devTools, "Development Tools", "Browser/Postman/IDE", "Developer tools for testing and development")
    }

    Rel(devTools, fithubWeb, "API Requests", "HTTP")
    Rel(fithubWeb, postgresLocal, "Database Operations", "PostgreSQL Protocol")
    
    UpdateRelStyle(devTools, fithubWeb, $offsetY="-20")
    UpdateRelStyle(fithubWeb, postgresLocal, $offsetY="-10")
```

## 🔄 CI/CD Pipeline

For detailed CI/CD pipeline architecture, see the dedicated CI pipeline documentation:

**📋 [CI Pipeline Architecture](CI_PIPELINE.md)**

The CI pipeline includes:
- **4-Stage Pipeline**: Code quality → Testing → Build → Deploy
- **Parallel Jobs**: Lint and security checks run simultaneously
- **Sequential Dependencies**: Each stage depends on previous stage success
- **Quality Gates**: Comprehensive code quality, security, and testing requirements
- **Multi-platform Builds**: Docker images for linux/amd64 and linux/arm64
- **Conditional Deployment**: Production deployment only on main branch

## 🔧 Technology Stack Details

### Application Layer
- **Framework**: Django 5.2+ with Django REST Framework
- **Language**: Python 3.13+
- **Package Manager**: uv (fast Python package manager)
- **Authentication**: JWT (djangorestframework-simplejwt)
- **API Documentation**: drf-spectacular (OpenAPI/Swagger)

### Database Layer
- **Primary Database**: PostgreSQL 16
- **Connection Pooling**: Built-in Django connection pooling
- **Migrations**: Django migrations with version control
- **Backup Strategy**: Automated PostgreSQL backups

### Infrastructure Layer
- **Containerization**: Docker with multi-stage builds
- **Orchestration**: Docker Compose (dev) / Docker Swarm or Kubernetes (prod)
- **Load Balancing**: Nginx or AWS Application Load Balancer
- **Monitoring**: Prometheus + Grafana
- **CI/CD**: GitHub Actions with automated testing

### Security Layer
- **HTTPS**: TLS termination at load balancer
- **Authentication**: JWT tokens with refresh mechanism
- **Authorization**: Django permissions and DRF permissions
- **Security Scanning**: Bandit and Safety in CI/CD pipeline

## 📋 Deployment Environments

### Development Environment
- **Purpose**: Local development and testing
- **Database**: PostgreSQL container with test data
- **Features**: Hot reload, debug mode, detailed error pages
- **Access**: `http://localhost:8000`

### Staging Environment
- **Purpose**: Pre-production testing
- **Database**: PostgreSQL with production-like data
- **Features**: Production-like configuration, monitoring
- **Access**: Staging URL with authentication

### Production Environment
- **Purpose**: Live application serving users
- **Database**: PostgreSQL cluster with replication
- **Features**: High availability, monitoring, backups
- **Access**: Production domain with SSL

## 🚀 Deployment Process

### Automated Deployment (CI/CD)
1. **Code Push**: Developer pushes to main branch
2. **CI Pipeline**: GitHub Actions runs tests, linting, security checks
3. **Build**: Docker image built and pushed to registry
4. **Deploy**: Automated deployment to staging/production
5. **Health Check**: Automated health checks and rollback if needed

### Manual Deployment
1. **Build Image**: `docker build -t fithub:latest .`
2. **Push to Registry**: `docker push fithub:latest`
3. **Deploy**: Update container orchestration
4. **Verify**: Check application health and logs

## 📊 Monitoring and Observability

### Metrics Collection
- **Application Metrics**: Django metrics via Prometheus
- **Database Metrics**: PostgreSQL performance metrics
- **Infrastructure Metrics**: Container and host metrics

### Logging
- **Application Logs**: Django logging with structured format
- **Access Logs**: Nginx access and error logs
- **Database Logs**: PostgreSQL query and error logs

### Alerting
- **Health Checks**: Automated health monitoring
- **Performance Alerts**: Response time and error rate monitoring
- **Resource Alerts**: CPU, memory, and disk usage monitoring

## 🔒 Security Considerations

### Network Security
- **Firewall**: Restrict access to necessary ports only
- **VPC**: Private network for database and internal services
- **SSL/TLS**: End-to-end encryption for all communications

### Application Security
- **Authentication**: JWT tokens with secure storage
- **Authorization**: Role-based access control
- **Input Validation**: Comprehensive input sanitization
- **Security Headers**: CORS, CSRF, and security headers

### Data Security
- **Encryption**: Data encryption at rest and in transit
- **Backup Security**: Encrypted backups with access controls
- **Audit Logging**: Comprehensive audit trail for all operations

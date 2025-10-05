# FitHub C4 Deployment Diagram

## 🏗️ C4 Deployment Architecture

This document provides a C4-style deployment diagram for the FitHub fitness and nutrition tracking API.

## 📊 Deployment Diagram

```mermaid
C4Deployment
    title Deployment Diagram for FitHub API

    Deployment_Node(dev, "Developer Machine", "Local Development"){
        Container(devClient, "Development Client", "Browser/Postman", "Developer testing FitHub API endpoints")
    }

    Deployment_Node(ci, "GitHub Actions", "CI/CD Pipeline"){
        Container(githubActions, "CI/CD Pipeline", "GitHub Actions", "Automated testing, linting, security checks, and Docker image building")
    }

    Deployment_Node(dockerhub, "Docker Hub", "Container Registry"){
        Container(registry, "Docker Registry", "Docker Hub", "Stores FitHub Docker images for deployment")
    }

    Deployment_Node(production, "Production Environment", "Cloud/On-Premise"){
        Deployment_Node(loadBalancer, "Load Balancer", "Nginx/ALB"){
            Container(nginx, "Reverse Proxy", "Nginx", "Routes traffic to FitHub application instances")
        }

        Deployment_Node(appCluster, "FitHub Application Cluster", "Docker Swarm/K8s"){
            Deployment_Node(app1, "FitHub App Instance 1", "Docker Container"){
                Container(fithubApp1, "FitHub API", "Django + Python 3.13", "Handles nutrition and goals API requests")
            }
            Deployment_Node(app2, "FitHub App Instance 2", "Docker Container"){
                Container(fithubApp2, "FitHub API", "Django + Python 3.13", "Handles nutrition and goals API requests")
            }
        }

        Deployment_Node(database, "Database Cluster", "PostgreSQL"){
            Deployment_Node(postgres, "Primary Database", "PostgreSQL 16"){
                ContainerDb(postgresDb, "FitHub Database", "PostgreSQL", "Stores user data, nutrition records, goals, and body measurements")
            }
            Deployment_Node(postgresReplica, "Read Replica", "PostgreSQL 16"){
                ContainerDb(postgresReplicaDb, "FitHub Read Replica", "PostgreSQL", "Read-only replica for improved performance")
            }
        }

        Deployment_Node(monitoring, "Monitoring Stack", "Prometheus/Grafana"){
            Container(prometheus, "Metrics Collection", "Prometheus", "Collects application and infrastructure metrics")
            Container(grafana, "Monitoring Dashboard", "Grafana", "Visualizes metrics and alerts")
        }
    }

    Rel(devClient, nginx, "API Requests", "HTTPS")
    Rel(githubActions, registry, "Push Images", "Docker API")
    Rel(nginx, fithubApp1, "Routes Requests", "HTTP")
    Rel(nginx, fithubApp2, "Routes Requests", "HTTP")
    Rel(fithubApp1, postgresDb, "Read/Write", "PostgreSQL Protocol")
    Rel(fithubApp2, postgresDb, "Read/Write", "PostgreSQL Protocol")
    Rel(fithubApp1, postgresReplicaDb, "Read Only", "PostgreSQL Protocol")
    Rel(fithubApp2, postgresReplicaDb, "Read Only", "PostgreSQL Protocol")
    Rel(postgresDb, postgresReplicaDb, "Replication", "PostgreSQL Streaming")
    Rel(fithubApp1, prometheus, "Metrics", "HTTP")
    Rel(fithubApp2, prometheus, "Metrics", "HTTP")
    Rel(prometheus, grafana, "Data Source", "HTTP")
    
    UpdateRelStyle(devClient, nginx, $offsetY="-40")
    UpdateRelStyle(githubActions, registry, $offsetY="-30")
    UpdateRelStyle(nginx, fithubApp1, $offsetY="-20", $offsetX="10")
    UpdateRelStyle(nginx, fithubApp2, $offsetY="-20", $offsetX="-10")
    UpdateRelStyle(fithubApp1, postgresDb, $offsetY="-10", $offsetX="5")
    UpdateRelStyle(fithubApp2, postgresDb, $offsetY="-10", $offsetX="-5")
    UpdateRelStyle(fithubApp1, postgresReplicaDb, $offsetY="-10", $offsetX="15")
    UpdateRelStyle(fithubApp2, postgresReplicaDb, $offsetY="-10", $offsetX="-15")
    UpdateRelStyle(postgresDb, postgresReplicaDb, $offsetY="-5")
    UpdateRelStyle(fithubApp1, prometheus, $offsetY="-30", $offsetX="20")
    UpdateRelStyle(fithubApp2, prometheus, $offsetY="-30", $offsetX="-20")
    UpdateRelStyle(prometheus, grafana, $offsetY="-10")
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

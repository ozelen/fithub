# FitHub CI/CD Pipeline Architecture

## 🔄 CI/CD Pipeline Overview

This document provides a detailed view of the FitHub CI/CD pipeline architecture, showing the complete flow from code commit to deployment.

## 📊 CI Pipeline Flow Diagram

```mermaid
C4Deployment
    title FitHub CI/CD Pipeline Architecture

    Deployment_Node(developer, "Developer", "Local Machine"){
        Container(dev, "Developer", "Human", "Commits code to GitHub repository")
    }

    Deployment_Node(github, "GitHub", "Code Repository"){
        Container(repo, "FitHub Repository", "Git", "Source code repository with branches")
    }

    Deployment_Node(ci, "GitHub Actions", "CI/CD Platform"){
        Deployment_Node(stage1, "Stage 1: Code Quality", "Parallel Jobs"){
            Container(lint, "Lint Job", "Ubuntu Runner", "Code quality checks: flake8, black, isort")
            Container(security, "Security Job", "Ubuntu Runner", "Security analysis: bandit, safety")
        }

        Deployment_Node(stage2, "Stage 2: Testing", "Sequential Job"){
            Container(test, "Test Job", "Ubuntu Runner + PostgreSQL", "Unit tests with PostgreSQL container")
        }

        Deployment_Node(stage3, "Stage 3: Build", "Sequential Job"){
            Container(dockerBuild, "Docker Build Job", "Ubuntu Runner", "Multi-platform Docker image build")
        }

        Deployment_Node(stage4, "Stage 4: Deploy", "Conditional Job"){
            Container(deploy, "Deploy Job", "Ubuntu Runner", "Production deployment (main branch only)")
        }
    }

    Deployment_Node(registry, "Docker Hub", "Container Registry"){
        Container(dockerRegistry, "Docker Registry", "Docker Hub", "Stores FitHub Docker images")
    }

    Deployment_Node(production, "Production Environment", "Cloud/On-Premise"){
        Container(prodApp, "Production App", "Docker Container", "Running FitHub application")
    }

    Rel(dev, repo, "Push Code", "Git")
    Rel(repo, lint, "Trigger", "GitHub Webhook")
    Rel(repo, security, "Trigger", "GitHub Webhook")
    Rel(lint, test, "Success", "Job Dependency")
    Rel(security, test, "Success", "Job Dependency")
    Rel(test, dockerBuild, "Success", "Job Dependency")
    Rel(dockerBuild, dockerRegistry, "Push Image", "Docker API")
    Rel(dockerBuild, deploy, "Success", "Job Dependency")
    Rel(deploy, prodApp, "Deploy", "Deployment API")
    
    UpdateRelStyle(dev, repo, $offsetY="-30")
    UpdateRelStyle(repo, lint, $offsetY="-20", $offsetX="10")
    UpdateRelStyle(repo, security, $offsetY="-20", $offsetX="-10")
    UpdateRelStyle(lint, test, $offsetY="-10", $offsetX="15")
    UpdateRelStyle(security, test, $offsetY="-10", $offsetX="-15")
    UpdateRelStyle(test, dockerBuild, $offsetY="-10")
    UpdateRelStyle(dockerBuild, dockerRegistry, $offsetY="-20", $offsetX="20")
    UpdateRelStyle(dockerBuild, deploy, $offsetY="-10", $offsetX="-20")
    UpdateRelStyle(deploy, prodApp, $offsetY="-30")
```

## 🔄 Detailed Pipeline Stages

### Stage 1: Code Quality Checks (Parallel)

```mermaid
flowchart TD
    A[Code Push/PR] --> B[Lint Job]
    A --> C[Security Job]
    
    B --> B1[Checkout Code]
    B1 --> B2[Setup Python 3.13]
    B2 --> B3[Install uv]
    B3 --> B4[Install Dependencies]
    B4 --> B5[Run flake8]
    B5 --> B6[Check black formatting]
    B6 --> B7[Check isort imports]
    
    C --> C1[Checkout Code]
    C1 --> C2[Setup Python 3.13]
    C2 --> C3[Install uv]
    C3 --> C4[Install Dependencies]
    C4 --> C5[Run bandit security scan]
    C5 --> C6[Run safety dependency check]
    C6 --> C7[Upload security reports]
    
    B7 --> D[Stage 1 Complete]
    C7 --> D
```

### Stage 2: Testing (Sequential)

```mermaid
flowchart TD
    A[Stage 1 Complete] --> B[Test Job]
    
    B --> B1[Checkout Code]
    B1 --> B2[Setup Python 3.13]
    B2 --> B3[Install uv]
    B3 --> B4[Install Dependencies]
    B4 --> B5[Start PostgreSQL Service]
    B5 --> B6[Wait for PostgreSQL]
    B6 --> B7[Run Django Migrations]
    B7 --> B8[Run pytest with Coverage]
    B8 --> B9[Upload Coverage to Codecov]
    B9 --> B10[Upload Coverage Reports]
    
    B10 --> C[Stage 2 Complete]
```

### Stage 3: Docker Build (Sequential)

```mermaid
flowchart TD
    A[Stage 2 Complete] --> B[Docker Build Job]
    
    B --> B1[Checkout Code]
    B1 --> B2[Setup Docker Buildx]
    B2 --> B3[Login to DockerHub]
    B3 --> B4[Extract Metadata]
    B4 --> B5[Build Multi-platform Image]
    B5 --> B6[Push to Registry]
    B6 --> B7[Test Image Locally]
    
    B7 --> C[Stage 3 Complete]
```

### Stage 4: Deployment (Conditional)

```mermaid
flowchart TD
    A[Stage 3 Complete] --> B{Main Branch?}
    B -->|Yes| C[Deploy Job]
    B -->|No| D[Skip Deployment]
    
    C --> C1[Checkout Code]
    C1 --> C2[Deploy to Production]
    C2 --> C3[Send Notifications]
    
    C3 --> E[Deployment Complete]
    D --> F[Pipeline Complete]
```

## 🛠️ Pipeline Configuration Details

### Trigger Conditions
- **Push Events**: `main` and `develop` branches
- **Pull Request Events**: Targeting `main` and `develop` branches

### Job Dependencies
```yaml
Stage 1 (Parallel):
├── lint: Code quality checks
└── security: Security analysis

Stage 2 (Sequential):
└── test: depends on [lint, security]

Stage 3 (Sequential):
└── docker-build: depends on test

Stage 4 (Conditional):
└── deploy: depends on [lint, security, test, docker-build]
    └── Only runs on main branch pushes
```

### Technology Stack

#### CI/CD Platform
- **Platform**: GitHub Actions
- **Runners**: Ubuntu Latest
- **Python Version**: 3.13
- **Package Manager**: uv (latest)

#### Code Quality Tools
- **Linting**: flake8 with complexity and line length checks
- **Formatting**: black (127 character line length)
- **Import Sorting**: isort
- **Security**: bandit (static analysis) + safety (dependency vulnerabilities)

#### Testing Infrastructure
- **Test Framework**: pytest with Django integration
- **Database**: PostgreSQL 16 (GitHub Actions service)
- **Coverage**: pytest-cov with HTML and XML reports
- **Coverage Upload**: Codecov integration

#### Container Build
- **Platform**: Docker Buildx
- **Multi-platform**: linux/amd64, linux/arm64
- **Registry**: Docker Hub
- **Caching**: GitHub Actions cache
- **Image Testing**: Local container validation

## 📊 Pipeline Metrics

### Typical Execution Times
- **Lint Job**: ~13 seconds
- **Security Job**: ~19 seconds
- **Test Job**: ~54 seconds
- **Docker Build**: ~1 minute 8 seconds
- **Deploy Job**: ~5 seconds

### Total Pipeline Time
- **Full Pipeline**: ~2 minutes 39 seconds
- **Parallel Stage 1**: ~19 seconds (longest of lint/security)
- **Sequential Stages**: ~2 minutes 20 seconds

## 🔒 Security & Quality Gates

### Code Quality Gates
- ✅ **Linting**: No flake8 errors or warnings
- ✅ **Formatting**: Code properly formatted with black
- ✅ **Imports**: Imports properly sorted with isort
- ✅ **Complexity**: Maximum complexity of 10
- ✅ **Line Length**: Maximum 127 characters

### Security Gates
- ✅ **Static Analysis**: No bandit security issues
- ✅ **Dependencies**: No known vulnerabilities (safety)
- ✅ **Timeout Protection**: 5-minute timeout on security scans

### Testing Gates
- ✅ **Test Coverage**: Minimum coverage maintained
- ✅ **All Tests Pass**: No failing unit tests
- ✅ **Database Integration**: PostgreSQL integration tests pass
- ✅ **Migration Validation**: Database migrations work correctly

### Build Gates
- ✅ **Docker Build**: Multi-platform image builds successfully
- ✅ **Image Testing**: Container starts and basic checks pass
- ✅ **Registry Push**: Image successfully pushed to Docker Hub

### Deployment Gates
- ✅ **Branch Protection**: Only main branch deploys to production
- ✅ **All Stages Pass**: All previous stages must succeed
- ✅ **Manual Approval**: Deployment requires all quality gates

## 🚀 Deployment Strategy

### Branch Strategy
- **main**: Production branch (auto-deploy on push)
- **develop**: Development branch (build and test only)
- **feature/***: Feature branches (build and test only)

### Image Tagging Strategy
- **latest**: Latest main branch build
- **main**: Current main branch
- **develop**: Current develop branch
- **pr-{number}**: Pull request builds
- **semver**: Semantic version tags

### Rollback Strategy
- **Automatic**: Failed deployments don't proceed
- **Manual**: Previous image tags available for rollback
- **Database**: Migration rollback procedures documented

## 📈 Monitoring & Observability

### Pipeline Monitoring
- **GitHub Actions**: Built-in pipeline status and logs
- **Codecov**: Test coverage tracking and trends
- **Docker Hub**: Image build and push status
- **Security Reports**: Artifact storage for security analysis

### Production Monitoring
- **Health Checks**: Container health validation
- **Logs**: Structured logging for debugging
- **Metrics**: Application performance monitoring
- **Alerts**: Deployment failure notifications

## 🔧 Local Development Integration

### Pre-commit Hooks
The same quality checks run locally via pre-commit hooks:
- **pytest**: Fast SQLite tests
- **lint**: flake8 code quality
- **format-check**: black and isort validation
- **security**: bandit security analysis

### Make Commands
Local development commands mirror CI pipeline:
```bash
make test-fast    # Fast local tests (SQLite)
make test         # Full tests (PostgreSQL)
make lint         # Code quality checks
make format       # Code formatting
make security     # Security analysis
```

This ensures that local development closely matches the CI environment, reducing the chance of CI failures.

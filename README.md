# FitHub 🏋️‍♂️

A comprehensive fitness and nutrition tracking API built with Django REST Framework, featuring goal management, meal tracking, and body measurements.

## 🚀 Features

- **Nutrition Tracking**: Track meals, ingredients, and nutritional information
- **Goal Management**: Set and monitor fitness goals with progress tracking
- **Body Measurements**: Record and analyze body composition over time
- **RESTful API**: Complete CRUD operations with filtering, searching, and pagination
- **Authentication**: Session and token-based authentication
- **Documentation**: Auto-generated OpenAPI/Swagger documentation
- **Testing**: Comprehensive test suite with PostgreSQL containers
- **CI/CD**: Automated testing, security scanning, and Docker deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    FitHub Architecture                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway   │    │   Database      │
│   (Future)      │◄──►│   Django DRF    │◄──►│   PostgreSQL    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   Docker        │
                       │   Container     │
                       └─────────────────┘
```

### Core Components

- **Django REST Framework**: API framework with authentication, permissions, and serialization
- **PostgreSQL**: Primary database for production and testing
- **Docker**: Containerized deployment with multi-platform support
- **pytest**: Testing framework with factory-boy for test data generation
- **testcontainers**: PostgreSQL containers for integration testing

## 🛠️ Tech Stack

- **Backend**: Django 5.2.7, Django REST Framework 3.16.1
- **Database**: PostgreSQL 16
- **Authentication**: Session + Token authentication
- **Documentation**: drf-spectacular (OpenAPI/Swagger)
- **Testing**: pytest, pytest-django, factory-boy, testcontainers
- **Code Quality**: black, isort, flake8, bandit, safety
- **Deployment**: Docker, GitHub Actions CI/CD

## 📦 Installation

### Prerequisites

- Python 3.13+
- PostgreSQL 16+
- Docker (optional, for containerized deployment)
- uv (recommended package manager)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd fithub
   ```

2. **Install dependencies**
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh
   
   # Install project dependencies
   uv sync --extra test
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

4. **Set up the database**
   ```bash
   # Start PostgreSQL (if not running)
   # Create database
   createdb fithub
   
   # Run migrations
   uv run manage.py migrate
   ```

5. **Create superuser**
   ```bash
   uv run manage.py createsuperuser
   ```

6. **Run the development server**
   ```bash
   uv run manage.py runserver
   ```

The API will be available at `http://localhost:8000/`

## 🧪 Testing

### Quick Tests (SQLite)
```bash
make test-fast
```

### Full Tests (PostgreSQL containers)
```bash
make test
```

### CI-style Tests with Coverage
```bash
make test-ci
```

### Individual Test Categories
```bash
# Unit tests only
uv run pytest nutrition/test_api.py goals/test_api.py

# Specific test
uv run pytest nutrition/test_api.py::NutritionAPITestCase::test_diet_create
```

## 🔧 Development Commands

```bash
# Code formatting
make format

# Linting
make lint

# Security checks
make security

# Database migrations
make migrate

# Run development server
uv run manage.py runserver

# Django shell
uv run manage.py shell

# Create new migration
uv run manage.py makemigrations
```

## 📚 API Documentation

### Interactive Documentation
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

### Authentication
The API supports both session and token authentication:

```python
# Token authentication
headers = {'Authorization': 'Token your-token-here'}

# Session authentication (for web clients)
# Include CSRF token in requests
```

### Core Endpoints

#### Nutrition API (`/api/nutrition/`)
- `GET /diets/` - List diets
- `POST /diets/` - Create diet
- `GET /meals/` - List meals
- `POST /meals/` - Create meal
- `GET /ingredients/` - List ingredients
- `POST /ingredients/` - Create ingredient

#### Goals API (`/api/goals/`)
- `GET /goals/` - List goals
- `POST /goals/` - Create goal
- `GET /body-measurements/` - List measurements
- `POST /body-measurements/` - Record measurement

### Example API Usage

```python
import requests

# Get all diets
response = requests.get('http://localhost:8000/api/nutrition/diets/')
diets = response.json()

# Create a new diet
diet_data = {
    'name': 'Weight Loss Diet',
    'description': 'Calorie deficit diet for weight loss',
    'start_date': '2025-01-01',
    'end_date': '2025-03-31'
}
response = requests.post(
    'http://localhost:8000/api/nutrition/diets/',
    json=diet_data,
    headers={'Authorization': 'Token your-token-here'}
)
```

## 🐳 Docker Deployment

### Build and Run Locally
```bash
# Build image
docker build -t fithub .

# Run with docker-compose
docker-compose up -d
```

### Production Deployment
The CI/CD pipeline automatically builds and pushes Docker images to DockerHub:
- **Image**: `zelenuk/fithub:latest`
- **Multi-platform**: linux/amd64, linux/arm64

## 🚀 CI/CD Pipeline

The project includes a comprehensive CI/CD pipeline with the following stages:

1. **Code Quality** (Parallel)
   - Linting (flake8)
   - Security scanning (bandit, safety)
   - Code formatting (black, isort)

2. **Testing**
   - Unit tests with PostgreSQL containers
   - Coverage reporting
   - 40+ test cases

3. **Docker Build**
   - Multi-platform builds
   - DockerHub push
   - Image testing

4. **Deployment**
   - Production deployment (main branch only)
   - Ready for cloud providers

## 📁 Project Structure

```
fithub/
├── .github/workflows/          # CI/CD pipeline
├── fitbot/                     # Django app (placeholder)
├── fithub/                     # Main Django project
│   ├── settings.py            # Production settings
│   ├── test_settings.py       # PostgreSQL test settings
│   ├── test_settings_sqlite.py # SQLite test settings
│   └── urls.py                # URL routing
├── goals/                      # Goals management app
│   ├── api.py                 # API viewsets
│   ├── models.py              # Goal and measurement models
│   ├── serializers.py         # API serializers
│   ├── factories.py           # Test data factories
│   └── test_api.py            # API tests
├── home/                       # Home page app
├── nutrition/                  # Nutrition tracking app
│   ├── api.py                 # API viewsets
│   ├── models.py              # Nutrition models
│   ├── serializers.py         # API serializers
│   ├── factories.py           # Test data factories
│   └── test_api.py            # API tests
├── conftest.py                # pytest configuration
├── Makefile                   # Development commands
├── pyproject.toml             # Project dependencies and config
└── README.md                  # This file
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`make test`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation as needed
- Ensure all CI checks pass

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the repository
- Check the API documentation at `/api/docs/`
- Review the test files for usage examples

## 🎯 Roadmap

- [ ] Frontend application (React/Vue.js)
- [ ] Mobile app (React Native/Flutter)
- [ ] Advanced analytics and reporting
- [ ] Social features and sharing
- [ ] Integration with fitness devices
- [ ] Machine learning recommendations

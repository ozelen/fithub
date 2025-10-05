# FitHub Development Guide

## 🔑 Key Development Decisions

### Technology Choices

1. **uv Package Manager**: Chosen over pip for significantly faster dependency resolution and installation
2. **JWT Authentication**: Primary authentication method for stateless API access
3. **PostgreSQL**: Production database with testcontainers for testing
4. **pytest + factory-boy**: Modern testing approach with realistic test data
5. **Pre-commit Hooks**: Automated code quality enforcement
6. **Docker**: Containerized deployment for consistency

### Code Quality Standards

- **Line Length**: 127 characters (black/isort configuration)
- **Python Version**: 3.13+ (latest stable)
- **Test Coverage**: Minimum 70% coverage required
- **Security**: Bandit and safety checks in CI/CD
- **Formatting**: Black + isort for consistent code style

### Testing Strategy

#### Test Database Strategy
- **Local Development**: SQLite for fast testing (`make test-fast`)
- **CI/CD**: PostgreSQL with testcontainers for realistic testing
- **Test Data**: factory-boy with faker for realistic test data generation

#### Test Types
- **Unit Tests**: Individual component testing
- **Integration Tests**: API endpoint testing with real database
- **Authentication Tests**: JWT, session, and token authentication
- **Security Tests**: Bandit security analysis

#### Test Configuration
- **pytest**: Modern testing framework with fixtures
- **testcontainers**: PostgreSQL containers for integration tests
- **factory-boy**: Test data factories for consistent test data
- **Coverage**: HTML and XML coverage reports

## 👥 For Human Developers

### 🚀 Quick Start

1. **Clone and Setup**
   ```bash
   git clone <repository-url>
   cd fithub
   uv sync --extra test
   ```

2. **Environment Setup**
   ```bash
   cp .env.example .env
   # Edit .env with your database credentials
   ```

3. **Database Setup**
   ```bash
   createdb fithub
   uv run manage.py migrate
   uv run manage.py createsuperuser
   ```

4. **Run Development Server**
   ```bash
   uv run manage.py runserver
   ```

### 🛠️ Development Workflow

#### Daily Development Commands

```bash
# Start development
make install          # Install dependencies
make migrate          # Run migrations
uv run manage.py runserver  # Start server

# Code quality
make format           # Format code
make lint             # Check code quality
make security         # Security checks

# Testing
make test-fast        # Quick SQLite tests
make test             # Full PostgreSQL tests
make test-ci          # CI-style tests with coverage
```

#### Pre-commit Hooks

The project uses pre-commit hooks to ensure code quality:

```bash
# Install pre-commit hooks (one-time setup)
uv run pre-commit install

# Run hooks manually
uv run pre-commit run --all-files

# Skip hooks (not recommended)
git commit --no-verify -m "message"
```

**Pre-commit checks:**
- ✅ **pytest**: All tests must pass
- ✅ **lint**: Code must pass flake8 checks
- ✅ **format-check**: Code must be properly formatted
- ✅ **security**: Security analysis with bandit

**Benefits:**
- Prevents broken code from being committed
- Enforces consistent code style
- Catches security issues early
- Maintains high code quality standards

#### Git Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/amazing-feature
   ```

2. **Make Changes and Test**
   ```bash
   make format
   make test
   ```

3. **Commit and Push**
   ```bash
   git add .
   git commit -m "Add amazing feature"
   git push origin feature/amazing-feature
   ```

4. **Create Pull Request**
   - All CI checks must pass
   - Code review required
   - Update documentation if needed

### 🏗️ Adding New Features

#### 1. Create New Django App
```bash
uv run manage.py startapp new_feature
```

#### 2. Define Models
```python
# new_feature/models.py
from django.db import models
from django.contrib.auth.models import User

class NewFeature(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
```

#### 3. Create Serializers
```python
# new_feature/serializers.py
from rest_framework import serializers
from .models import NewFeature

class NewFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewFeature
        fields = ['id', 'name', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']
```

#### 4. Create API Views
```python
# new_feature/api.py
from rest_framework import viewsets, permissions
from .models import NewFeature
from .serializers import NewFeatureSerializer

class NewFeatureViewSet(viewsets.ModelViewSet):
    queryset = NewFeature.objects.all()
    serializer_class = NewFeatureSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
```

#### 5. Add URL Routing
```python
# new_feature/api_urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import NewFeatureViewSet

router = DefaultRouter()
router.register(r'new-features', NewFeatureViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
```

#### 6. Include in Main URLs
```python
# fithub/urls.py
urlpatterns = [
    # ... existing patterns
    path('api/new-feature/', include('new_feature.api_urls')),
]
```

#### 7. Create Tests
```python
# new_feature/test_api.py
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from django.contrib.auth.models import User
from .models import NewFeature

class NewFeatureAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_new_feature(self):
        data = {'name': 'Test Feature'}
        response = self.client.post('/api/new-feature/new-features/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewFeature.objects.count(), 1)
```

#### 8. Create Factories for Testing
```python
# new_feature/factories.py
import factory
from django.contrib.auth.models import User
from .models import NewFeature

class NewFeatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewFeature
    
    name = factory.Sequence(lambda n: f"Feature {n}")
    user = factory.SubFactory('django.contrib.auth.models.User')
```

### 🧪 Testing Guidelines

#### Test Structure
```python
class FeatureAPITestCase(APITestCase):
    def setUp(self):
        """Set up test data"""
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    def test_feature_create(self):
        """Test feature creation"""
        # Arrange
        data = {'name': 'Test Feature'}
        
        # Act
        response = self.client.post('/api/features/', data)
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Feature.objects.count(), 1)
    
    def test_feature_list(self):
        """Test feature listing"""
        # Arrange
        FeatureFactory.create_batch(3, user=self.user)
        
        # Act
        response = self.client.get('/api/features/')
        
        # Assert
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
```

#### Test Categories
- **Unit Tests**: Test individual components
- **Integration Tests**: Test API endpoints
- **Model Tests**: Test model methods and properties
- **Serializer Tests**: Test data validation and transformation

### 🔧 Code Quality Standards

#### Code Style
- **Formatting**: Use `black` and `isort`
- **Linting**: Follow `flake8` guidelines
- **Line Length**: 127 characters maximum
- **Imports**: Group and sort imports properly

#### Documentation
- **Docstrings**: Document all classes and methods
- **Comments**: Explain complex logic
- **Type Hints**: Use type hints for function parameters and returns

#### Example Well-Formatted Code
```python
from datetime import date, timedelta
from decimal import Decimal
from typing import Dict, List, Optional

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .models import Diet, Meal


class DietSerializer(serializers.ModelSerializer):
    """
    Serializer for Diet model with validation and custom fields.
    """
    
    class Meta:
        model = Diet
        fields = [
            'id', 'name', 'description', 'user', 'start_date',
            'end_date', 'is_active', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def validate_start_date(self, value: date) -> date:
        """
        Validate that start date is not in the past.
        
        Args:
            value: The start date to validate
            
        Returns:
            The validated start date
            
        Raises:
            ValidationError: If start date is in the past
        """
        if value < date.today():
            raise serializers.ValidationError(
                "Start date cannot be in the past."
            )
        return value


class DietViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing diets with full CRUD operations.
    
    Provides endpoints for creating, reading, updating, and deleting diets.
    Includes custom actions for activating diets and getting active diets.
    """
    
    queryset = Diet.objects.all()
    serializer_class = DietSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = ['is_active', 'start_date', 'end_date']
    search_fields = ['name', 'description']
    ordering_fields = ['created_at', 'start_date', 'name']
    ordering = ['-created_at']
    
    def perform_create(self, serializer: DietSerializer) -> None:
        """
        Set the user when creating a new diet.
        
        Args:
            serializer: The diet serializer instance
        """
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk: Optional[int] = None) -> Response:
        """
        Activate a specific diet.
        
        Args:
            request: The HTTP request
            pk: The primary key of the diet to activate
            
        Returns:
            Response with activation status
        """
        diet = self.get_object()
        diet.is_active = True
        diet.save()
        return Response({'status': 'diet activated'})
```

## 🤖 For AI Assistants

### 🎯 Project Context

FitHub is a Django REST Framework API for fitness and nutrition tracking. The project emphasizes:
- **Clean Architecture**: Well-structured Django apps with clear separation of concerns
- **Comprehensive Testing**: Full test coverage with PostgreSQL containers
- **Code Quality**: Automated formatting, linting, and security scanning
- **CI/CD**: Automated testing and deployment pipeline

### 🤖 AI Development Guidelines

#### 1. Follow the Documentation

**CRITICAL**: Always read and follow the existing documentation before making changes:

- **📚 [Architecture](ARCHITECTURE.md)**: Understand system design, dependencies, and data models
- **🔌 [API Reference](API.md)**: Follow API patterns and authentication methods
- **👨‍💻 [Development Guide](DEVELOPMENT.md)**: Follow coding standards and workflow
- **🚀 [Deployment](DEPLOYMENT.md)**: Understand deployment requirements
- **📊 [ER Diagram](ER_DIAGRAM.md)**: Understand database relationships

**Before starting any task:**
1. Read relevant documentation sections
2. Understand existing patterns and conventions
3. Check similar implementations in the codebase
4. Follow established naming conventions and structures

#### 2. Make Atomic Feature-Based Commits

**Commit Strategy:**
- **One feature per commit**: Each commit should implement a single, complete feature
- **Descriptive commit messages**: Use conventional commit format
- **Include tests**: Every feature commit must include relevant tests
- **Update documentation**: Update docs if the feature affects API or architecture

**Commit Message Format:**
```
type(scope): brief description

Detailed explanation of what was implemented:
- Feature 1
- Feature 2
- Tests added
- Documentation updated

Closes #issue-number (if applicable)
```

**Examples:**
```bash
# Good: Single feature with tests
git commit -m "feat(nutrition): add meal scheduling with recurrence

- Add recurrence_type field to Meal model
- Implement daily, weekly, and custom recurrence patterns
- Add recurrence validation in MealSerializer
- Add tests for all recurrence types
- Update API documentation with scheduling examples"

# Good: Bug fix with test
git commit -m "fix(goals): correct body measurement calculation

- Fix BMI calculation formula in BodyMeasurement model
- Add validation for measurement values
- Add tests for edge cases (zero weight, negative values)
- Update API docs with calculation examples"

# Bad: Multiple unrelated changes
git commit -m "fix various issues and add new features"
```

#### 3. Pre-Feature Workflow

**Before starting any new feature:**

1. **Commit Current Changes**
   ```bash
   # Stage all changes
   git add .
   
   # Commit with descriptive message
   git commit -m "feat(scope): implement current feature"
   
   # Push to current branch
   git push origin current-branch
   ```

2. **Pull and Rebase Latest Changes**
   ```bash
   # Switch to main branch
   git checkout main
   
   # Pull latest changes
   git pull origin main
   
   # Switch back to feature branch
   git checkout feature-branch
   
   # Rebase on latest main
   git rebase main
   
   # Resolve any conflicts if they occur
   # git add . && git rebase --continue
   ```

3. **Verify Everything Works**
   ```bash
   # Run tests to ensure nothing is broken
   make test-fast
   
   # Run linting and formatting
   make format
   make lint
   ```

4. **Start New Feature**
   ```bash
   # Create new feature branch from main
   git checkout main
   git checkout -b feature/new-feature-name
   ```

#### 4. Code Quality Requirements

**Every commit must pass:**
- ✅ **Tests**: All tests must pass (`make test-fast`)
- ✅ **Linting**: Code must pass flake8 checks (`make lint`)
- ✅ **Formatting**: Code must be properly formatted (`make format`)
- ✅ **Security**: Security analysis must pass (`make security`)

**Pre-commit hooks will enforce these automatically.**

#### 5. Testing Requirements

**For every feature:**
- Add unit tests for new functionality
- Add integration tests for API endpoints
- Test edge cases and error conditions
- Ensure test coverage doesn't decrease
- Use factory-boy for test data generation

**Test Structure:**
```python
def test_feature_name(self):
    """Test description of what this test verifies"""
    # Arrange: Set up test data
    user = UserFactory()
    # Act: Perform the action
    response = self.client.post(url, data)
    # Assert: Verify the result
    self.assertEqual(response.status_code, 201)
```

#### 6. Documentation Updates

**Update documentation when:**
- Adding new API endpoints
- Changing existing API behavior
- Adding new dependencies
- Modifying architecture or data models
- Adding new development workflows

**Documentation files to consider:**
- `docs/API.md` - API endpoint changes
- `docs/ARCHITECTURE.md` - System changes
- `docs/DEVELOPMENT.md` - Workflow changes
- `README.md` - Major feature additions

#### 7. Error Handling

**Always handle errors gracefully:**
- Use appropriate HTTP status codes
- Provide meaningful error messages
- Log errors for debugging
- Add tests for error conditions

**Example:**
```python
try:
    # Operation that might fail
    result = perform_operation()
    return Response(result, status=status.HTTP_200_OK)
except ValidationError as e:
    return Response(
        {'error': 'Validation failed', 'details': str(e)},
        status=status.HTTP_400_BAD_REQUEST
    )
except Exception as e:
    logger.error(f"Unexpected error: {e}")
    return Response(
        {'error': 'Internal server error'},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR
    )
```

#### 8. Security Considerations

**Always consider security:**
- Validate all user input
- Use proper authentication and authorization
- Sanitize data before database operations
- Follow Django security best practices
- Add security tests for sensitive operations

#### 9. Performance Considerations

**Optimize for performance:**
- Use database queries efficiently (avoid N+1 problems)
- Add database indexes for frequently queried fields
- Use pagination for large datasets
- Consider caching for expensive operations
- Profile and test performance-critical code

#### 10. AI-Specific Best Practices

**When working on this project:**
- **Read first, code second**: Always understand existing patterns
- **Ask for clarification**: If requirements are unclear, ask questions
- **Propose solutions**: Explain your approach before implementing
- **Test thoroughly**: Don't assume code works without testing
- **Document decisions**: Explain why you chose a particular approach
- **Follow conventions**: Match existing code style and patterns
- **Be atomic**: Make small, focused changes that are easy to review

### 🏗️ Architecture Patterns

#### Django App Structure
Each Django app follows this pattern:
```
app_name/
├── models.py           # Database models
├── serializers.py      # API serializers  
├── api.py             # API viewsets
├── api_urls.py        # API URL routing
├── factories.py       # Test data factories
├── test_api.py        # API tests
├── admin.py           # Django admin
└── migrations/        # Database migrations
```

#### API Design Patterns
- **ViewSets**: Use `ModelViewSet` for full CRUD operations
- **Serializers**: Handle validation and data transformation
- **Permissions**: `IsAuthenticated` for all endpoints
- **Filtering**: DjangoFilterBackend, SearchFilter, OrderingFilter
- **Custom Actions**: Use `@action` decorator for custom endpoints

#### Testing Patterns
- **APITestCase**: For API endpoint testing
- **Factory Pattern**: Use factory-boy for test data generation
- **Container Tests**: Use testcontainers for PostgreSQL integration tests

### 🔧 Development Guidelines for AI

#### When Adding New Features

1. **Follow Existing Patterns**
   - Use the same structure as existing apps (nutrition, goals)
   - Follow the same naming conventions
   - Use the same testing patterns

2. **Code Quality Requirements**
   - Format code with `black` and `isort`
   - Pass `flake8` linting
   - Write comprehensive tests
   - Add proper docstrings

3. **API Design Principles**
   - RESTful endpoints
   - Proper HTTP status codes
   - Consistent error handling
   - User ownership of data

#### Example: Adding a New Feature

When asked to add a new feature, follow this template:

```python
# 1. Create the model
class NewFeature(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']

# 2. Create the serializer
class NewFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = NewFeature
        fields = ['id', 'name', 'user', 'created_at']
        read_only_fields = ['user', 'created_at']

# 3. Create the API viewset
class NewFeatureViewSet(viewsets.ModelViewSet):
    queryset = NewFeature.objects.all()
    serializer_class = NewFeatureSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['created_at', 'name']
    ordering = ['-created_at']
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# 4. Create the factory
class NewFeatureFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = NewFeature
    
    name = factory.Sequence(lambda n: f"Feature {n}")
    user = factory.SubFactory('django.contrib.auth.models.User')

# 5. Create the tests
class NewFeatureAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = UserFactory()
        self.client.force_authenticate(user=self.user)
    
    def test_create_new_feature(self):
        data = {'name': 'Test Feature'}
        response = self.client.post('/api/new-features/', data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(NewFeature.objects.count(), 1)
```

#### Common Tasks and Solutions

**Adding a New API Endpoint:**
1. Add method to existing ViewSet or create new ViewSet
2. Add URL pattern to `api_urls.py`
3. Write tests for the endpoint
4. Update API documentation

**Adding a New Model Field:**
1. Add field to model
2. Create and run migration
3. Update serializer
4. Update tests
5. Update factories

**Adding Custom Business Logic:**
1. Add method to model or create service class
2. Add custom action to ViewSet
3. Write tests for the logic
4. Document the functionality

#### Testing Requirements

Always include these test types:
- **CRUD Tests**: Create, Read, Update, Delete operations
- **Authentication Tests**: Ensure proper authentication
- **Permission Tests**: Ensure user can only access their data
- **Validation Tests**: Test serializer validation
- **Custom Action Tests**: Test any custom ViewSet actions

#### Code Quality Checklist

Before submitting code, ensure:
- [ ] Code is formatted with `black` and `isort`
- [ ] Passes `flake8` linting
- [ ] All tests pass (`make test`)
- [ ] Security checks pass (`make security`)
- [ ] Proper docstrings and comments
- [ ] Follows existing patterns and conventions

### 🚨 Common Issues and Solutions

#### Database Issues
- **Migration Conflicts**: Use `--merge` flag or resolve manually
- **Test Database**: Use `--reuse-db` flag for faster tests
- **Container Tests**: Ensure PostgreSQL container is running

#### API Issues
- **Authentication**: Always include proper authentication headers
- **Permissions**: Ensure user ownership of data
- **Validation**: Use serializers for input validation
- **Error Handling**: Return proper HTTP status codes

#### Testing Issues
- **Factory Dependencies**: Use `SubFactory` for foreign keys
- **Test Isolation**: Use `setUp` method for test data
- **Container Tests**: Use `conftest.py` for container setup

### 📚 Key Files to Understand

1. **`fithub/settings.py`**: Main Django settings
2. **`nutrition/api.py`**: Example API implementation
3. **`nutrition/test_api.py`**: Example test implementation
4. **`conftest.py`**: Test configuration and fixtures
5. **`.github/workflows/ci.yml`**: CI/CD pipeline
6. **`Makefile`**: Development commands

### 🎯 Best Practices

1. **Consistency**: Follow existing patterns and conventions
2. **Testing**: Write comprehensive tests for all functionality
3. **Documentation**: Add docstrings and comments
4. **Security**: Ensure proper authentication and authorization
5. **Performance**: Use efficient database queries
6. **Error Handling**: Provide meaningful error messages
7. **Code Quality**: Maintain high code quality standards

This guide should help both human developers and AI assistants work effectively with the FitHub codebase while maintaining consistency and quality standards.

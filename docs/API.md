# FitHub API Documentation

## 🔗 Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com`

## 🔐 Authentication

FitHub API supports multiple authentication methods with JWT as the primary method for API clients:

### Authentication Strategy

The API implements a **multi-method authentication strategy** to support different client types:

1. **JWT Authentication** (Primary): Stateless, scalable for API clients
2. **Session Authentication**: For web browser clients with CSRF protection
3. **Token Authentication**: Simple DRF tokens for server-to-server communication

### JWT Configuration

- **Access Token Lifetime**: 60 minutes
- **Refresh Token Lifetime**: 7 days
- **Token Rotation**: Enabled for security
- **Blacklist**: Refresh tokens are blacklisted after rotation
- **Algorithm**: HS256 with project secret key

### 1. JWT Authentication (Recommended for API clients)

```http
Authorization: Bearer your-jwt-token-here
```

**Getting JWT Tokens:**
```bash
curl -X POST http://localhost:8000/api/auth/jwt/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

**Response:**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

**Refreshing JWT Token:**
```bash
curl -X POST http://localhost:8000/api/auth/jwt/token/refresh/ \
  -H "Content-Type: application/json" \
  -d '{"refresh": "your-refresh-token"}'
```

### 2. Token Authentication (DRF Tokens)

```http
Authorization: Token your-token-here
```

**Getting a Token:**
```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your-username", "password": "your-password"}'
```

**Response:**
```json
{
  "token": "your-authentication-token",
  "user_id": 1,
  "username": "your-username",
  "email": "your-email@example.com",
  "is_staff": false,
  "is_superuser": false
}
```

### 3. Session Authentication (For web clients)

Include CSRF token in requests:
```http
X-CSRFToken: your-csrf-token-here
```

## 📊 API Endpoints Overview

### Nutrition API (`/api/nutrition/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/diets/` | GET, POST | List/create diets |
| `/diets/{id}/` | GET, PUT, PATCH, DELETE | Diet details |
| `/diets/{id}/activate/` | POST | Activate diet |
| `/diets/active/` | GET | Get active diet |
| `/meals/` | GET, POST | List/create meals |
| `/meals/{id}/` | GET, PUT, PATCH, DELETE | Meal details |
| `/meals/{id}/ingredients/` | GET | Get meal ingredients |
| `/meals/{id}/add_ingredient/` | POST | Add ingredient to meal |
| `/meals/{id}/nutrition_summary/` | GET | Get meal nutrition |
| `/ingredients/` | GET, POST | List/create ingredients |
| `/ingredients/{id}/` | GET, PUT, PATCH, DELETE | Ingredient details |
| `/ingredients/search/` | GET | Search ingredients |
| `/ingredients/personal/` | GET | Get personal ingredients |
| `/categories/` | GET, POST | List/create categories |
| `/meal-records/` | GET, POST | List/create meal records |
| `/meal-records/today/` | GET | Get today's records |
| `/meal-records/nutrition_summary/` | GET | Get nutrition summary |
| `/meal-preferences/` | GET, POST | List/create preferences |
| `/meal-preferences/by_type/` | GET | Get preferences by type |
| `/meal-ingredients/` | GET, POST | List/create meal ingredients |

### Goals API (`/api/goals/`)

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/goals/` | GET, POST | List/create goals |
| `/goals/{id}/` | GET, PUT, PATCH, DELETE | Goal details |
| `/goals/{id}/activate/` | POST | Activate goal |
| `/goals/{id}/deactivate/` | POST | Deactivate goal |
| `/goals/active/` | GET | Get active goals |
| `/goals/upcoming/` | GET | Get upcoming goals |
| `/goals/overdue/` | GET | Get overdue goals |
| `/goals/{id}/progress/` | GET | Get goal progress |
| `/body-measurements/` | GET, POST | List/create measurements |
| `/body-measurements/{id}/` | GET, PUT, PATCH, DELETE | Measurement details |
| `/body-measurements/latest/` | GET | Get latest measurements |
| `/body-measurements/trends/` | GET | Get measurement trends |
| `/body-measurements/summary/` | GET | Get measurement summary |
| `/body-measurements/bulk_create/` | POST | Create multiple measurements |

## 🍎 Nutrition API Details

### Diets

#### Create a Diet
```http
POST /api/nutrition/diets/
Content-Type: application/json
Authorization: Token your-token-here

{
  "name": "Weight Loss Diet",
  "description": "Calorie deficit diet for weight loss",
  "start_date": "2025-01-01",
  "end_date": "2025-03-31"
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Weight Loss Diet",
  "description": "Calorie deficit diet for weight loss",
  "user": 1,
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

#### List Diets with Filtering
```http
GET /api/nutrition/diets/?is_active=true&ordering=-created_at
Authorization: Token your-token-here
```

### Meals

#### Create a Meal
```http
POST /api/nutrition/meals/
Content-Type: application/json
Authorization: Token your-token-here

{
  "name": "Breakfast Bowl",
  "meal_type": "breakfast",
  "diet": 1,
  "description": "Healthy breakfast with oats and fruits"
}
```

#### Add Ingredient to Meal
```http
POST /api/nutrition/meals/1/add_ingredient/
Content-Type: application/json
Authorization: Token your-token-here

{
  "ingredient_id": 5,
  "quantity": 100,
  "unit": "g"
}
```

### Ingredients

#### Create an Ingredient
```http
POST /api/nutrition/ingredients/
Content-Type: application/json
Authorization: Token your-token-here

{
  "name": "Chicken Breast",
  "category": 1,
  "calories_per_100g": 165.0,
  "protein_per_100g": 31.0,
  "carbs_per_100g": 0.0,
  "fat_per_100g": 3.6,
  "fiber_per_100g": 0.0,
  "sugar_per_100g": 0.0,
  "sodium_per_100g": 74.0,
  "is_personal": false
}
```

#### Search Ingredients
```http
GET /api/nutrition/ingredients/search/?q=chicken
Authorization: Token your-token-here
```

### Meal Records

#### Record a Meal
```http
POST /api/nutrition/meal-records/
Content-Type: application/json
Authorization: Token your-token-here

{
  "meal": 1,
  "timestamp": "2025-01-01T08:00:00Z",
  "calories": 450.0
}
```

#### Get Today's Records
```http
GET /api/nutrition/meal-records/today/
Authorization: Token your-token-here
```

#### Get Nutrition Summary
```http
GET /api/nutrition/meal-records/nutrition_summary/?days=7
Authorization: Token your-token-here
```

**Response:**
```json
{
  "period_days": 7,
  "total_calories": 10500.0,
  "average_daily_calories": 1500.0,
  "record_count": 21,
  "calories_by_day": [
    {"date": "2025-01-01", "calories": 1500.0},
    {"date": "2025-01-02", "calories": 1600.0}
  ]
}
```

## 🎯 Goals API Details

### Goals

#### Create a Goal
```http
POST /api/goals/goals/
Content-Type: application/json
Authorization: Token your-token-here

{
  "title": "Lose 10kg",
  "description": "Weight loss goal for summer",
  "goal_type": "weight_loss",
  "target_value": 70.0,
  "start_date": "2025-01-01",
  "target_date": "2025-06-01"
}
```

#### Get Goal Progress
```http
GET /api/goals/goals/1/progress/
Authorization: Token your-token-here
```

**Response:**
```json
{
  "goal": {
    "id": 1,
    "title": "Lose 10kg",
    "target_value": 70.0,
    "start_date": "2025-01-01",
    "target_date": "2025-06-01"
  },
  "current_value": 75.0,
  "progress_percentage": 50.0,
  "days_remaining": 90,
  "estimated_completion": "2025-04-15"
}
```

### Body Measurements

#### Record a Measurement
```http
POST /api/goals/body-measurements/
Content-Type: application/json
Authorization: Token your-token-here

{
  "metric": "weight",
  "value": 75.5,
  "unit": "kg",
  "timestamp": "2025-01-01T08:00:00Z"
}
```

#### Get Latest Measurements
```http
GET /api/goals/body-measurements/latest/
Authorization: Token your-token-here
```

#### Get Measurement Trends
```http
GET /api/goals/body-measurements/trends/?metric=weight&days=30
Authorization: Token your-token-here
```

**Response:**
```json
{
  "metric": "weight",
  "unit": "kg",
  "period_days": 30,
  "measurements": [
    {"date": "2025-01-01", "value": 75.5},
    {"date": "2025-01-02", "value": 75.2}
  ],
  "trend": "decreasing",
  "change": -0.3,
  "change_percentage": -0.4
}
```

#### Bulk Create Measurements
```http
POST /api/goals/body-measurements/bulk_create/
Content-Type: application/json
Authorization: Token your-token-here

{
  "measurements": [
    {
      "metric": "weight",
      "value": 75.5,
      "unit": "kg",
      "timestamp": "2025-01-01T08:00:00Z"
    },
    {
      "metric": "body_fat",
      "value": 15.2,
      "unit": "%",
      "timestamp": "2025-01-01T08:00:00Z"
    }
  ]
}
```

## 🔍 Filtering, Searching, and Pagination

### Filtering

All list endpoints support filtering by model fields:

```http
# Filter diets by active status
GET /api/nutrition/diets/?is_active=true

# Filter meals by type
GET /api/nutrition/meals/?meal_type=breakfast

# Filter goals by type
GET /api/goals/goals/?goal_type=weight_loss

# Filter measurements by metric
GET /api/goals/body-measurements/?metric=weight
```

### Searching

Search endpoints support text search:

```http
# Search ingredients
GET /api/nutrition/ingredients/search/?q=chicken

# Search meals
GET /api/nutrition/meals/?search=breakfast

# Search goals
GET /api/goals/goals/?search=weight
```

### Ordering

All list endpoints support ordering:

```http
# Order by creation date (newest first)
GET /api/nutrition/diets/?ordering=-created_at

# Order by name (alphabetical)
GET /api/nutrition/meals/?ordering=name

# Order by date (oldest first)
GET /api/goals/body-measurements/?ordering=timestamp
```

### Pagination

All list endpoints are paginated:

```http
# Get first page (default: 20 items)
GET /api/nutrition/diets/

# Get specific page
GET /api/nutrition/diets/?page=2

# Custom page size
GET /api/nutrition/diets/?page_size=50
```

**Pagination Response:**
```json
{
  "count": 100,
  "next": "http://localhost:8000/api/nutrition/diets/?page=2",
  "previous": null,
  "results": [...]
}
```

## 📝 Data Models

### Diet Model
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "user": 1,
  "start_date": "2025-01-01",
  "end_date": "2025-03-31",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### Meal Model
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "meal_type": "breakfast|lunch|dinner|snack",
  "diet": 1,
  "user": 1,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### Ingredient Model
```json
{
  "id": 1,
  "name": "string",
  "category": 1,
  "calories_per_100g": 165.0,
  "protein_per_100g": 31.0,
  "carbs_per_100g": 0.0,
  "fat_per_100g": 3.6,
  "fiber_per_100g": 0.0,
  "sugar_per_100g": 0.0,
  "sodium_per_100g": 74.0,
  "is_personal": false,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### Goal Model
```json
{
  "id": 1,
  "title": "string",
  "description": "string",
  "goal_type": "weight_loss|muscle_gain|endurance|strength",
  "target_value": 70.0,
  "user": 1,
  "start_date": "2025-01-01",
  "target_date": "2025-06-01",
  "is_active": true,
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

### BodyMeasurement Model
```json
{
  "id": 1,
  "metric": "weight|body_fat|muscle_mass|waist|chest|arms|legs",
  "value": 75.5,
  "unit": "kg|g|lb|%|cm|in",
  "user": 1,
  "timestamp": "2025-01-01T08:00:00Z",
  "created_at": "2025-01-01T00:00:00Z",
  "updated_at": "2025-01-01T00:00:00Z"
}
```

## ⚠️ Error Handling

### Standard Error Response
```json
{
  "field_name": ["Error message"],
  "non_field_errors": ["General error message"]
}
```

### Common HTTP Status Codes

- **200 OK**: Successful GET, PUT, PATCH
- **201 Created**: Successful POST
- **204 No Content**: Successful DELETE
- **400 Bad Request**: Invalid request data
- **401 Unauthorized**: Authentication required
- **403 Forbidden**: Permission denied
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Example Error Responses

#### Validation Error (400)
```json
{
  "name": ["This field is required."],
  "start_date": ["Date has wrong format. Use one of these formats instead: YYYY-MM-DD."]
}
```

#### Authentication Error (401)
```json
{
  "detail": "Authentication credentials were not provided."
}
```

#### Permission Error (403)
```json
{
  "detail": "You do not have permission to perform this action."
}
```

#### Not Found Error (404)
```json
{
  "detail": "Not found."
}
```

## 🧪 Testing the API

### Using cURL

```bash
# Get all diets
curl -H "Authorization: Token your-token-here" \
     http://localhost:8000/api/nutrition/diets/

# Create a new diet
curl -X POST \
     -H "Authorization: Token your-token-here" \
     -H "Content-Type: application/json" \
     -d '{"name": "Test Diet", "start_date": "2025-01-01"}' \
     http://localhost:8000/api/nutrition/diets/
```

### Using Python requests

```python
import requests

# Set up authentication
headers = {'Authorization': 'Token your-token-here'}

# Get all diets
response = requests.get('http://localhost:8000/api/nutrition/diets/', headers=headers)
diets = response.json()

# Create a new diet
diet_data = {
    'name': 'Test Diet',
    'start_date': '2025-01-01'
}
response = requests.post(
    'http://localhost:8000/api/nutrition/diets/',
    json=diet_data,
    headers=headers
)
```

### Using JavaScript fetch

```javascript
// Set up authentication
const headers = {
  'Authorization': 'Token your-token-here',
  'Content-Type': 'application/json'
};

// Get all diets
fetch('http://localhost:8000/api/nutrition/diets/', { headers })
  .then(response => response.json())
  .then(data => console.log(data));

// Create a new diet
const dietData = {
  name: 'Test Diet',
  start_date: '2025-01-01'
};

fetch('http://localhost:8000/api/nutrition/diets/', {
  method: 'POST',
  headers,
  body: JSON.stringify(dietData)
})
.then(response => response.json())
.then(data => console.log(data));
```

## 📚 Interactive Documentation

Visit the interactive API documentation:
- **Swagger UI**: `http://localhost:8000/api/docs/`
- **ReDoc**: `http://localhost:8000/api/redoc/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

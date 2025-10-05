# FitHub Entity Relationship Diagram

## Database Schema Overview

This document contains the Entity Relationship (ER) diagram for the FitHub database schema, showing all entities and their relationships.

## Mermaid ER Diagram

```mermaid
erDiagram
    USER ||--o{ DIET : creates
    USER ||--o{ INGREDIENT : "creates personal"
    USER ||--o{ MEAL_RECORD : logs
    USER ||--o{ MEAL_PREFERENCE : has
    USER ||--o{ GOAL : sets
    USER ||--o{ BODY_MEASUREMENT : records
    
    DIET ||--o{ MEAL : contains
    DIET {
        int id PK
        string name
        int user_id FK
        float day_proteins_g
        float day_fats_g
        float day_carbohydrates_g
        float day_calories_kcal
        boolean is_active
        date start_date
        date end_date
        text notes
        datetime created_at
        datetime updated_at
    }
    
    MEAL ||--o{ MEAL_INGREDIENT : contains
    MEAL ||--o{ MEAL_RECORD : "can be logged as"
    MEAL {
        int id PK
        string name
        text description
        int diet_id FK
        boolean is_scheduled
        date start_date
        date end_date
        time start_time
        int duration_minutes
        string recurrence_type
        date recurrence_until
        string google_calendar_event_id
        datetime last_synced_to_calendar
        string meal_type
        datetime created_at
        datetime updated_at
    }
    
    CATEGORY ||--o{ CATEGORY : "has parent"
    CATEGORY ||--o{ INGREDIENT : contains
    CATEGORY {
        int id PK
        string name
        int parent_id FK
        datetime created_at
        datetime updated_at
    }
    
    INGREDIENT ||--o{ MEAL_INGREDIENT : "used in"
    INGREDIENT ||--o{ MEAL_PREFERENCE : "has preference"
    INGREDIENT {
        int id PK
        string name
        int category_id FK
        float proteins
        float fats
        float carbs
        float calories
        float fibers
        float sugars
        text description
        boolean is_personal
        int created_by_id FK
        datetime created_at
        datetime updated_at
    }
    
    MEAL_INGREDIENT {
        int id PK
        int meal_id FK
        int ingredient_id FK
        string barcode
        float quantity
        string unit
        datetime created_at
        datetime updated_at
    }
    
    MEAL_RECORD {
        int id PK
        int meal_id FK
        int user_id FK
        string meal_name
        float quantity_grams
        float calories
        float proteins
        float carbs
        float fats
        datetime timestamp
        string photo
        text feedback
        datetime created_at
        datetime updated_at
    }
    
    MEAL_PREFERENCE {
        int id PK
        int user_id FK
        int ingredient_id FK
        string barcode
        text description
        string preference_type
        datetime created_at
        datetime updated_at
    }
    
    GOAL {
        uuid id PK
        int user_id FK
        string goal_type
        date target_date
        text notes
        boolean is_active
        datetime created_at
        datetime updated_at
    }
    
    BODY_MEASUREMENT {
        int id PK
        int user_id FK
        string metric
        string measurement_type
        float value
        datetime timestamp
        datetime created_at
        datetime updated_at
    }
    
    USER {
        int id PK
        string username
        string email
        string first_name
        string last_name
        boolean is_active
        datetime date_joined
    }
```

## Entity Descriptions

### Core Entities

1. **USER**: Django's built-in User model for authentication and user management
2. **DIET**: User's dietary plans with nutritional targets
3. **MEAL**: Individual meals within a diet, with scheduling capabilities
4. **INGREDIENT**: Food items with nutritional information
5. **CATEGORY**: Hierarchical categorization of ingredients
6. **MEAL_INGREDIENT**: Junction table linking meals to ingredients with quantities
7. **MEAL_RECORD**: Logged meal consumption (planned or unplanned)
8. **MEAL_PREFERENCE**: User preferences for ingredients (love, like, dislike, etc.)
9. **GOAL**: User's fitness goals with target dates
10. **BODY_MEASUREMENT**: Physical measurements for progress tracking

### Key Relationships

- **User Ownership**: All user-specific entities have a foreign key to USER
- **Diet Hierarchy**: DIET → MEAL → MEAL_INGREDIENT → INGREDIENT
- **Category Hierarchy**: CATEGORY can have parent categories (self-referencing)
- **Meal Logging**: MEAL_RECORD can reference either a planned MEAL or be standalone
- **Ingredient Preferences**: MEAL_PREFERENCE links users to ingredients with preference types
- **Goal Tracking**: BODY_MEASUREMENT tracks progress toward GOALs

### Design Patterns

- **User Isolation**: All user data is isolated by user_id foreign keys
- **Flexible Meal Recording**: MEAL_RECORD supports both planned meals and ad-hoc logging
- **Hierarchical Categories**: Self-referencing CATEGORY model for nested categorization
- **Preference System**: MEAL_PREFERENCE allows users to express ingredient preferences
- **Goal Progress**: BODY_MEASUREMENT enables tracking progress toward fitness goals

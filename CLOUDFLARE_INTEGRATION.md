# Cloudflare Workers Integration Guide

This guide explains how to integrate your Cloudflare Workers frontend with the Django FitHub backend authentication system.

## 🚀 **Authentication Endpoints**

### **Base URL**
```
https://your-django-domain.com
```

### **Web Authentication Endpoints**

#### **1. User Registration**
```http
POST /auth/register/
Content-Type: application/json

{
  "username": "newuser",
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "password": "securepass123",
  "password_confirm": "securepass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-10-12T17:46:28.154931Z",
    "is_active": true
  },
  "redirect_url": "/dashboard/"
}
```

#### **2. User Login**
```http
POST /auth/login/
Content-Type: application/json

{
  "username": "newuser",
  "password": "securepass123"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "user": {
    "id": 1,
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-10-12T17:46:28.154931Z",
    "is_active": true
  },
  "redirect_url": "/dashboard/"
}
```

#### **3. Check Authentication Status**
```http
GET /auth/auth-status/
```

**Response (Authenticated):**
```json
{
  "success": true,
  "is_authenticated": true,
  "user": {
    "id": 1,
    "username": "newuser",
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "date_joined": "2025-10-12T17:46:28.154931Z",
    "is_active": true
  }
}
```

**Response (Not Authenticated):**
```json
{
  "success": true,
  "is_authenticated": false,
  "user": null
}
```

#### **4. Get User Info**
```http
GET /auth/user-info/
```

#### **5. Update Profile**
```http
POST /auth/update-profile/
Content-Type: application/json

{
  "email": "newemail@example.com",
  "first_name": "Jane",
  "last_name": "Smith"
}
```

#### **6. Logout**
```http
POST /auth/logout/
```

## 🔧 **Cloudflare Workers Implementation**

### **Basic Authentication Service**

```javascript
// auth-service.js
class AuthService {
  constructor(baseUrl) {
    this.baseUrl = baseUrl;
  }

  async register(userData) {
    const response = await fetch(`${this.baseUrl}/auth/register/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
      body: JSON.stringify(userData)
    });
    
    return await response.json();
  }

  async login(username, password) {
    const response = await fetch(`${this.baseUrl}/auth/login/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include', // Important for session cookies
      body: JSON.stringify({ username, password })
    });
    
    return await response.json();
  }

  async logout() {
    const response = await fetch(`${this.baseUrl}/auth/logout/`, {
      method: 'POST',
      credentials: 'include'
    });
    
    return await response.json();
  }

  async getAuthStatus() {
    const response = await fetch(`${this.baseUrl}/auth/auth-status/`, {
      credentials: 'include'
    });
    
    return await response.json();
  }

  async getUserInfo() {
    const response = await fetch(`${this.baseUrl}/auth/user-info/`, {
      credentials: 'include'
    });
    
    return await response.json();
  }

  async updateProfile(profileData) {
    const response = await fetch(`${this.baseUrl}/auth/update-profile/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify(profileData)
    });
    
    return await response.json();
  }
}

// Usage
const authService = new AuthService('https://your-django-domain.com');
```

### **Cloudflare Workers Handler**

```javascript
// worker.js
import { AuthService } from './auth-service.js';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const authService = new AuthService(env.DJANGO_BASE_URL);

    // Handle authentication routes
    if (url.pathname === '/api/auth/register') {
      return handleRegister(request, authService);
    }
    
    if (url.pathname === '/api/auth/login') {
      return handleLogin(request, authService);
    }
    
    if (url.pathname === '/api/auth/logout') {
      return handleLogout(request, authService);
    }
    
    if (url.pathname === '/api/auth/status') {
      return handleAuthStatus(request, authService);
    }

    // Serve your frontend app
    return new Response('Your frontend app', {
      headers: { 'Content-Type': 'text/html' }
    });
  }
};

async function handleRegister(request, authService) {
  try {
    const userData = await request.json();
    const result = await authService.register(userData);
    
    return new Response(JSON.stringify(result), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true'
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ 
      success: false, 
      error: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function handleLogin(request, authService) {
  try {
    const { username, password } = await request.json();
    const result = await authService.login(username, password);
    
    return new Response(JSON.stringify(result), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true'
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ 
      success: false, 
      error: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function handleLogout(request, authService) {
  try {
    const result = await authService.logout();
    
    return new Response(JSON.stringify(result), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true'
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ 
      success: false, 
      error: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

async function handleAuthStatus(request, authService) {
  try {
    const result = await authService.getAuthStatus();
    
    return new Response(JSON.stringify(result), {
      headers: { 
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Credentials': 'true'
      }
    });
  } catch (error) {
    return new Response(JSON.stringify({ 
      success: false, 
      error: error.message 
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
```

### **Frontend Integration Example**

```javascript
// frontend.js
class FitHubApp {
  constructor() {
    this.authService = new AuthService('https://your-django-domain.com');
    this.currentUser = null;
  }

  async init() {
    // Check if user is already authenticated
    const authStatus = await this.authService.getAuthStatus();
    
    if (authStatus.is_authenticated) {
      this.currentUser = authStatus.user;
      this.showAuthenticatedUI();
    } else {
      this.showLoginUI();
    }
  }

  async handleLogin(event) {
    event.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
    try {
      const result = await this.authService.login(username, password);
      
      if (result.success) {
        this.currentUser = result.user;
        this.showAuthenticatedUI();
      } else {
        this.showError(result.error);
      }
    } catch (error) {
      this.showError('Login failed. Please try again.');
    }
  }

  async handleRegister(event) {
    event.preventDefault();
    
    const formData = new FormData(event.target);
    const userData = Object.fromEntries(formData.entries());
    
    try {
      const result = await this.authService.register(userData);
      
      if (result.success) {
        this.currentUser = result.user;
        this.showAuthenticatedUI();
      } else {
        this.showError(result.errors || 'Registration failed');
      }
    } catch (error) {
      this.showError('Registration failed. Please try again.');
    }
  }

  async handleLogout() {
    try {
      await this.authService.logout();
      this.currentUser = null;
      this.showLoginUI();
    } catch (error) {
      this.showError('Logout failed');
    }
  }

  showAuthenticatedUI() {
    document.getElementById('login-form').style.display = 'none';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
    
    document.getElementById('user-name').textContent = 
      `${this.currentUser.first_name} ${this.currentUser.last_name}`;
  }

  showLoginUI() {
    document.getElementById('login-form').style.display = 'block';
    document.getElementById('register-form').style.display = 'none';
    document.getElementById('dashboard').style.display = 'none';
  }

  showError(message) {
    const errorDiv = document.getElementById('error-message');
    errorDiv.textContent = message;
    errorDiv.style.display = 'block';
  }
}

// Initialize the app
const app = new FitHubApp();
app.init();
```

## 🔒 **Security Considerations**

### **CORS Configuration**
Your Django backend is already configured to allow requests from Cloudflare Workers domains:
- `*.workers.dev`
- `*.pages.dev`

### **Session Management**
- Sessions are managed via HTTP cookies
- Make sure to include `credentials: 'include'` in your fetch requests
- CSRF protection is handled automatically by Django

### **Environment Variables**
Set these in your Cloudflare Workers environment:
```bash
DJANGO_BASE_URL=https://your-django-domain.com
```

## 📱 **API Endpoints Summary**

| Endpoint | Method | Purpose | Auth Required |
|----------|--------|---------|---------------|
| `/auth/register/` | POST | User registration | No |
| `/auth/login/` | POST | User login | No |
| `/auth/logout/` | POST | User logout | Yes |
| `/auth/auth-status/` | GET | Check auth status | No |
| `/auth/user-info/` | GET | Get user info | Yes |
| `/auth/update-profile/` | POST | Update profile | Yes |
| `/auth/signup/` | GET | Registration page | No |
| `/auth/signin/` | GET | Login page | No |

## 🧪 **Testing**

You can test the endpoints directly:

```bash
# Register a new user
curl -X POST https://your-django-domain.com/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "first_name": "Test",
    "last_name": "User",
    "password": "testpass123",
    "password_confirm": "testpass123"
  }'

# Login
curl -X POST https://your-django-domain.com/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "testpass123"
  }'
```

## 🚀 **Deployment**

1. Deploy your Django backend with the new authentication endpoints
2. Update your Cloudflare Workers with the authentication service
3. Set the `DJANGO_BASE_URL` environment variable
4. Test the authentication flow

Your Cloudflare Workers frontend can now seamlessly authenticate users with your Django backend! 🎉

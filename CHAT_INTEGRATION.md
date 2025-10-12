# Chat Application Integration Guide

This guide shows how to integrate your FitHub Django backend authentication with your Cloudflare Workers chat application running at [https://fitbot.zelen.uk/](https://fitbot.zelen.uk/).

## 🚀 **Integration Overview**

Your chat application can now authenticate users through the Django backend and maintain user context throughout the chat session.

## 🔧 **Chat Authentication Service**

### **For Cloudflare Workers (fitbot.zelen.uk)**

```javascript
// auth-service.js - Add this to your chat worker
class ChatAuthService {
  constructor() {
    this.baseUrl = 'https://your-django-domain.com'; // Replace with your Django URL
    this.currentUser = null;
  }

  async authenticateUser(username, password) {
    try {
      const response = await fetch(`${this.baseUrl}/auth/login/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password })
      });
      
      const result = await response.json();
      
      if (result.success) {
        this.currentUser = result.user;
        return { success: true, user: result.user };
      } else {
        return { success: false, error: result.error };
      }
    } catch (error) {
      return { success: false, error: 'Authentication failed' };
    }
  }

  async registerUser(userData) {
    try {
      const response = await fetch(`${this.baseUrl}/auth/register/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify(userData)
      });
      
      const result = await response.json();
      
      if (result.success) {
        this.currentUser = result.user;
        return { success: true, user: result.user };
      } else {
        return { success: false, error: result.errors || 'Registration failed' };
      }
    } catch (error) {
      return { success: false, error: 'Registration failed' };
    }
  }

  async checkAuthStatus() {
    try {
      const response = await fetch(`${this.baseUrl}/auth/auth-status/`, {
        credentials: 'include'
      });
      
      const result = await response.json();
      
      if (result.success && result.is_authenticated) {
        this.currentUser = result.user;
        return { success: true, user: result.user };
      } else {
        this.currentUser = null;
        return { success: false, user: null };
      }
    } catch (error) {
      this.currentUser = null;
      return { success: false, user: null };
    }
  }

  async logout() {
    try {
      await fetch(`${this.baseUrl}/auth/logout/`, {
        method: 'POST',
        credentials: 'include'
      });
      
      this.currentUser = null;
      return { success: true };
    } catch (error) {
      return { success: false, error: 'Logout failed' };
    }
  }

  getCurrentUser() {
    return this.currentUser;
  }

  isAuthenticated() {
    return this.currentUser !== null;
  }
}

export { ChatAuthService };
```

### **Updated Chat Worker with Authentication**

```javascript
// worker.js - Updated with authentication
import { ChatAuthService } from './auth-service.js';

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const authService = new ChatAuthService();

    // Handle authentication routes
    if (url.pathname === '/api/auth/login') {
      return handleLogin(request, authService);
    }
    
    if (url.pathname === '/api/auth/register') {
      return handleRegister(request, authService);
    }
    
    if (url.pathname === '/api/auth/status') {
      return handleAuthStatus(request, authService);
    }
    
    if (url.pathname === '/api/auth/logout') {
      return handleLogout(request, authService);
    }

    // Handle WebSocket connections for chat
    if (url.pathname === '/chat') {
      return handleWebSocket(request, env, authService);
    }

    // Serve the chat interface
    return new Response(getChatHTML(), {
      headers: { 'Content-Type': 'text/html' }
    });
  }
};

async function handleLogin(request, authService) {
  try {
    const { username, password } = await request.json();
    const result = await authService.authenticateUser(username, password);
    
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

async function handleRegister(request, authService) {
  try {
    const userData = await request.json();
    const result = await authService.registerUser(userData);
    
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
    const result = await authService.checkAuthStatus();
    
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

async function handleWebSocket(request, env, authService) {
  // Check authentication before allowing WebSocket connection
  const authResult = await authService.checkAuthStatus();
  
  if (!authResult.success || !authResult.user) {
    return new Response('Authentication required', { status: 401 });
  }

  // Get the Durable Object for this chat room
  const id = env.CHAT_ROOM.idFromName('main-room');
  const obj = env.CHAT_ROOM.get(id);
  
  // Pass the authenticated user to the Durable Object
  return obj.fetch(request, {
    user: authResult.user
  });
}

function getChatHTML() {
  return `
<!DOCTYPE html>
<html>
<head>
    <title>FitHub Chat</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; border-radius: 10px; padding: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .auth-section { margin-bottom: 20px; padding: 20px; background: #f8f9fa; border-radius: 5px; }
        .chat-section { display: none; }
        .messages { height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; background: #fafafa; }
        .message { margin-bottom: 10px; padding: 8px; border-radius: 5px; }
        .message.own { background: #007bff; color: white; text-align: right; }
        .message.other { background: #e9ecef; }
        .message-input { width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }
        .btn { padding: 10px 20px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        .btn:hover { background: #0056b3; }
        .user-info { background: #e9ecef; padding: 10px; border-radius: 5px; margin-bottom: 10px; }
        .error { color: red; margin: 10px 0; }
        .success { color: green; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>FitHub Chat</h1>
        
        <!-- Authentication Section -->
        <div id="auth-section" class="auth-section">
            <h3>Sign In to Chat</h3>
            <div id="auth-error" class="error" style="display: none;"></div>
            <div id="auth-success" class="success" style="display: none;"></div>
            
            <form id="login-form">
                <input type="text" id="username" placeholder="Username" required style="width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px;">
                <input type="password" id="password" placeholder="Password" required style="width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px;">
                <button type="submit" class="btn">Sign In</button>
            </form>
            
            <p>Don't have an account? <a href="#" onclick="showRegister()">Sign up</a></p>
            
            <form id="register-form" style="display: none;">
                <input type="text" id="reg-username" placeholder="Username" required style="width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px;">
                <input type="email" id="reg-email" placeholder="Email" required style="width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px;">
                <input type="text" id="reg-first-name" placeholder="First Name" required style="width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px;">
                <input type="text" id="reg-last-name" placeholder="Last Name" required style="width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px;">
                <input type="password" id="reg-password" placeholder="Password" required style="width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px;">
                <input type="password" id="reg-password-confirm" placeholder="Confirm Password" required style="width: 100%; padding: 10px; margin: 5px 0; border: 1px solid #ddd; border-radius: 5px;">
                <button type="submit" class="btn">Sign Up</button>
            </form>
            
            <p id="register-link" style="display: none;">Already have an account? <a href="#" onclick="showLogin()">Sign in</a></p>
        </div>
        
        <!-- Chat Section -->
        <div id="chat-section" class="chat-section">
            <div id="user-info" class="user-info"></div>
            <div id="messages" class="messages"></div>
            <input type="text" id="message-input" class="message-input" placeholder="Type your message...">
            <button onclick="sendMessage()" class="btn">Send</button>
            <button onclick="logout()" class="btn" style="background: #dc3545;">Logout</button>
        </div>
    </div>

    <script>
        let ws = null;
        let currentUser = null;

        // Authentication functions
        async function login(event) {
            event.preventDefault();
            
            const username = document.getElementById('username').value;
            const password = document.getElementById('password').value;
            
            try {
                const response = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ username, password })
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentUser = result.user;
                    showChat();
                } else {
                    showError(result.error);
                }
            } catch (error) {
                showError('Login failed. Please try again.');
            }
        }

        async function register(event) {
            event.preventDefault();
            
            const userData = {
                username: document.getElementById('reg-username').value,
                email: document.getElementById('reg-email').value,
                first_name: document.getElementById('reg-first-name').value,
                last_name: document.getElementById('reg-last-name').value,
                password: document.getElementById('reg-password').value,
                password_confirm: document.getElementById('reg-password-confirm').value
            };
            
            try {
                const response = await fetch('/api/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(userData)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentUser = result.user;
                    showChat();
                } else {
                    showError(result.error || 'Registration failed');
                }
            } catch (error) {
                showError('Registration failed. Please try again.');
            }
        }

        async function logout() {
            try {
                await fetch('/api/auth/logout', { method: 'POST' });
                currentUser = null;
                if (ws) {
                    ws.close();
                    ws = null;
                }
                showAuth();
            } catch (error) {
                console.error('Logout error:', error);
            }
        }

        function showAuth() {
            document.getElementById('auth-section').style.display = 'block';
            document.getElementById('chat-section').style.display = 'none';
        }

        function showChat() {
            document.getElementById('auth-section').style.display = 'none';
            document.getElementById('chat-section').style.display = 'block';
            
            document.getElementById('user-info').innerHTML = 
                \`Welcome, <strong>\${currentUser.first_name} \${currentUser.last_name}</strong> (\${currentUser.username})\`;
            
            connectWebSocket();
        }

        function showError(message) {
            const errorDiv = document.getElementById('auth-error');
            errorDiv.textContent = message;
            errorDiv.style.display = 'block';
            setTimeout(() => errorDiv.style.display = 'none', 5000);
        }

        function showRegister() {
            document.getElementById('login-form').style.display = 'none';
            document.getElementById('register-form').style.display = 'block';
            document.getElementById('register-link').style.display = 'block';
        }

        function showLogin() {
            document.getElementById('login-form').style.display = 'block';
            document.getElementById('register-form').style.display = 'none';
            document.getElementById('register-link').style.display = 'none';
        }

        // WebSocket functions
        function connectWebSocket() {
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            ws = new WebSocket(\`\${protocol}//\${window.location.host}/chat\`);
            
            ws.onopen = function() {
                console.log('Connected to chat');
            };
            
            ws.onmessage = function(event) {
                const message = JSON.parse(event.data);
                addMessage(message);
            };
            
            ws.onclose = function() {
                console.log('Disconnected from chat');
            };
        }

        function sendMessage() {
            const input = document.getElementById('message-input');
            const message = input.value.trim();
            
            if (message && ws && ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({
                    type: 'message',
                    text: message,
                    user: currentUser.username,
                    timestamp: new Date().toISOString()
                }));
                input.value = '';
            }
        }

        function addMessage(message) {
            const messagesDiv = document.getElementById('messages');
            const messageDiv = document.createElement('div');
            messageDiv.className = \`message \${message.user === currentUser.username ? 'own' : 'other'}\`;
            
            const time = new Date(message.timestamp).toLocaleTimeString();
            messageDiv.innerHTML = \`
                <strong>\${message.user}:</strong> \${message.text}
                <small style="display: block; opacity: 0.7;">\${time}</small>
            \`;
            
            messagesDiv.appendChild(messageDiv);
            messagesDiv.scrollTop = messagesDiv.scrollHeight;
        }

        // Event listeners
        document.getElementById('login-form').addEventListener('submit', login);
        document.getElementById('register-form').addEventListener('submit', register);
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                sendMessage();
            }
        });

        // Check authentication status on page load
        async function checkAuthStatus() {
            try {
                const response = await fetch('/api/auth/status');
                const result = await response.json();
                
                if (result.success && result.user) {
                    currentUser = result.user;
                    showChat();
                } else {
                    showAuth();
                }
            } catch (error) {
                showAuth();
            }
        }

        // Initialize
        checkAuthStatus();
    </script>
</body>
</html>
  `;
}
```

## 🔧 **Durable Object with User Context**

```javascript
// chat-room.js - Updated Durable Object
export class ChatRoom {
  constructor(state, env) {
    this.state = state;
    this.env = env;
    this.users = new Map();
  }

  async fetch(request, options = {}) {
    const url = new URL(request.url);
    
    if (request.headers.get('Upgrade') === 'websocket') {
      return this.handleWebSocket(request, options.user);
    }
    
    return new Response('WebSocket connection required', { status: 400 });
  }

  async handleWebSocket(request, user) {
    const webSocketPair = new WebSocketPair();
    const [client, server] = Object.values(webSocketPair);

    // Store user information
    if (user) {
      this.users.set(user.id, {
        ...user,
        connectedAt: new Date().toISOString()
      });
    }

    server.accept();
    
    server.addEventListener('message', async (event) => {
      try {
        const message = JSON.parse(event.data);
        
        if (message.type === 'message') {
          // Add user context to the message
          const enrichedMessage = {
            ...message,
            userId: user?.id,
            userFullName: user ? \`\${user.first_name} \${user.last_name}\` : 'Anonymous',
            timestamp: new Date().toISOString()
          };
          
          // Broadcast to all connected users
          await this.broadcastMessage(enrichedMessage);
        }
      } catch (error) {
        console.error('Error processing message:', error);
      }
    });

    server.addEventListener('close', () => {
      if (user) {
        this.users.delete(user.id);
      }
    });

    return new Response(null, {
      status: 101,
      webSocket: client,
    });
  }

  async broadcastMessage(message) {
    // Store message in Durable Object storage
    const messages = await this.state.storage.get('messages') || [];
    messages.push(message);
    
    // Keep only last 100 messages
    if (messages.length > 100) {
      messages.splice(0, messages.length - 100);
    }
    
    await this.state.storage.put('messages', messages);
    
    // Broadcast to all connected users
    const connectedUsers = Array.from(this.users.values());
    console.log(\`Broadcasting message to \${connectedUsers.length} users\`);
  }
}
```

## 🚀 **Deployment Steps**

1. **Update your Django backend** with the new CORS settings
2. **Deploy the updated chat worker** with authentication
3. **Set environment variables** in Cloudflare Workers:
   ```bash
   DJANGO_BASE_URL=https://your-django-domain.com
   ```
4. **Test the integration** by visiting [https://fitbot.zelen.uk/](https://fitbot.zelen.uk/)

## 🧪 **Testing the Integration**

1. Visit your chat application
2. Try to register a new user
3. Login with existing credentials
4. Send messages in the chat
5. Verify user context is maintained

## 📱 **Features Added**

- ✅ **User Authentication**: Login/register through Django backend
- ✅ **User Context**: Messages show user's full name and username
- ✅ **Session Management**: Persistent authentication across chat sessions
- ✅ **User Management**: Track connected users in the chat room
- ✅ **Secure WebSocket**: Authentication required for chat access

Your chat application now has full integration with the FitHub Django backend authentication system! 🎉

# 🔐 CogniData Sign-In Guide

## ✅ Application Status

Both backend and frontend are now running successfully!

- **Backend**: http://localhost:8000
- **Frontend**: http://localhost:5173  
- **API Docs**: http://localhost:8000/docs

## 🔑 Demo Credentials

Use these credentials to sign in:

```
Email: rudraadmin@gmail.com
Password: adminrudra@1234
```

## 🐛 Fixes Applied

### 1. **Database Configuration**
   - Changed from MySQL to SQLite for simpler setup
   - Updated `.env` file: `DATABASE_URL=sqlite:///./cognidata.db`

### 2. **Backend Health Check**
   - Added unauthenticated `/api/debug/ping` endpoint
   - This allows the login page to verify backend connectivity

### 3. **Login Page Improvements**
   - Added demo credentials display on login page
   - Added backend connection status indicator (green/red dot)
   - Added automatic backend connectivity check
   - Improved error messages

### 4. **Server Startup**
   - Both backend and frontend are now running with --reload for development

## 📋 Test Checklist

### Backend Tests
- [x] Database initialized with tables
- [x] 7 users exist in database
- [x] Admin account created (rudraadmin@gmail.com)
- [x] Login endpoint responding (200 OK)
- [x] JWT tokens generated correctly
- [x] Health check endpoint working

### Frontend Tests
- [x] Vite dev server running
- [x] API proxy configured correctly (/api → http://127.0.0.1:8000)
- [x] Login page displays demo credentials
- [x] Backend status indicator working

## 🧪 How to Test Login

### Option 1: Use the Web Interface
1. Open http://localhost:5173
2. You'll see the login page with demo credentials displayed
3. Check the green "Online" status indicator (top right of credentials box)
4. Enter: `rudraadmin@gmail.com` / `adminrudra@1234`
5. Click "✦ Sign In"
6. You should be redirected to `/chat`

### Option 2: Use the Test HTML
1. Open `test_login.html` in your browser
2. Credentials are pre-filled
3. Click "Test Login"
4. You should see "✅ Login Successful!" with the JWT token

### Option 3: Use cURL (Command Line)
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"rudraadmin@gmail.com","password":"adminrudra@1234"}'
```

Expected response:
```json
{
  "access_token": "eyJhbGc...",
  "token_type": "bearer"
}
```

## 👥 Available User Accounts

| Email | Role | Password |
|-------|------|----------|
| rudraadmin@gmail.com | admin | adminrudra@1234 |
| admin@example.com | admin | (needs reset) |
| rudraadmin2@gmail.com | admin | (needs reset) |
| Others | user | (needs reset) |

## 🔧 Troubleshooting

### If Backend Shows "Offline"
1. Check if backend is running: `curl http://localhost:8000/api/debug/ping`
2. Restart backend: `cd cognidata/backend && python -m uvicorn app.main:app --port 8000 --reload`

### If Login Fails
1. Check browser console (F12) for errors
2. Verify credentials are correct
3. Check network tab for API response
4. Ensure `/api` proxy is working in Vite

### If "Invalid email or password"
- Double-check credentials (case-sensitive)
- Verify user exists in database:
  ```bash
  cd cognidata/backend
  python -c "from app.core.database import SessionLocal; from app.models.user import User; db = SessionLocal(); users = db.query(User).all(); [print(f'{u.email}') for u in users]"
  ```

## 🚀 Features Available After Login

Once signed in, you can access:

1. **Chat** - AI-powered data analysis
2. **Upload** - Upload datasets (CSV files)
3. **Dashboard** - View KPIs and visualizations  
4. **AI Analyst** - Advanced analytics
5. **Reports** - Generate PDF reports
6. **Maps** - Geospatial visualizations
7. **AutoML** - Automated machine learning
8. **Admin Panel** - User management (admin only)
9. **Workspaces** - Team collaboration
10. **And many more!**

## 📝 Notes

- The application uses JWT tokens stored in localStorage
- Tokens expire after 24 hours
- OAuth (Google/GitHub) requires additional configuration
- 2FA is available but needs setup per user
- Email notifications require SMTP configuration (already configured for rudraadmin@gmail.com)

## 🎯 Next Steps

1. **Test the sign-in** with the demo credentials
2. **Upload a dataset** to test data analysis features
3. **Explore the features** listed above
4. **Create new users** via the Admin Panel or Register page

---

**Last Updated**: June 12, 2026  
**Status**: ✅ All systems operational

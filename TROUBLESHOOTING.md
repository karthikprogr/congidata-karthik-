# 🔧 CogniData Troubleshooting Guide

Common issues and solutions for CogniData platform.

---

## 📤 Dataset Upload Issues

### Issue: "Upload failed" without details

**Solution:**
1. Check file format: Only CSV, Excel (.xlsx/.xls), JSON are supported
2. Check file size: Maximum 200MB per file
3. Check encoding: Use UTF-8, Latin-1, or ISO-8859-1 for CSV files
4. Check browser console (F12) for detailed error

### Issue: "Could not decode CSV file"

**Solution:**
```bash
# Save CSV with UTF-8 encoding in Excel:
File → Save As → Tools → Web Options → Encoding → UTF-8

# Or convert with Python:
import pandas as pd
df = pd.read_csv('file.csv', encoding='latin1')
df.to_csv('file_utf8.csv', encoding='utf-8', index=False)
```

### Issue: .xls files not uploading

**Solution:**
Ensure `xlrd` is installed:
```bash
cd cognidata/backend
pip install xlrd>=2.0.1
```

### Issue: "File is empty"

**Causes:**
- File actually has no data
- File has only headers
- File upload was interrupted

**Solution:**
1. Open file in Excel/text editor to verify content
2. Ensure file has at least one data row
3. Try re-uploading

---

## 🔐 Authentication Issues

### Issue: "Invalid credentials"

**Solutions:**
1. Check if user exists (default: admin@cognidata.com / admin123)
2. Reset database:
   ```bash
   cd cognidata/backend
   rm cognidata.db
   python -m app.seed
   ```
3. Check email/password spelling
4. Clear browser cache and cookies

### Issue: "Token expired"

**Solution:**
- Log out and log back in
- Token expires after 30 minutes (configurable in .env)

### Issue: 2FA not working

**Solutions:**
1. Check system time is synchronized
2. Use authenticator app (Google Authenticator, Authy)
3. Verify QR code is scanned correctly
4. Disable and re-enable 2FA if needed

---

## 🚀 Startup Issues

### Issue: Backend won't start

**Error: "ModuleNotFoundError: No module named 'fastapi'"**

**Solution:**
```bash
cd cognidata/backend
pip install -r requirements.txt
```

**Error: "Address already in use (Port 8000)"**

**Solution:**
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill the process (replace PID with actual number)
taskkill /PID <PID> /F

# Or change port in run.ps1
```

**Error: "DATABASE_URL not set"**

**Solution:**
Create `.env` file in `cognidata/backend/`:
```env
DATABASE_URL=sqlite:///./cognidata.db
SECRET_KEY=your-secret-key-at-least-32-chars
OPENAI_API_KEY=sk-your-key-here
```

### Issue: Frontend won't start

**Error: "Cannot find module 'react'"**

**Solution:**
```bash
cd cognidata/frontend
npm install
```

**Error: "Port 5173 already in use"**

**Solution:**
```powershell
# Find and kill process
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

**Error: "Network error when calling backend"**

**Solution:**
1. Ensure backend is running on http://localhost:8000
2. Check CORS settings in `cognidata/backend/app/main.py`
3. Check firewall settings

---

## 🤖 AI/LLM Issues

### Issue: "OpenAI API error"

**Error: "Incorrect API key provided"**

**Solution:**
1. Get API key from https://platform.openai.com/api-keys
2. Add to `.env`:
   ```env
   OPENAI_API_KEY=sk-...your-key...
   ```
3. Restart backend

**Error: "Rate limit exceeded"**

**Solution:**
1. Wait a few minutes
2. Upgrade OpenAI plan
3. Implement request throttling

**Error: "Model not found"**

**Solution:**
1. Check model availability in your OpenAI account
2. Update model name in `cognidata/backend/services/agents/model_resolver.py`
3. Default models: gpt-4, gpt-3.5-turbo

### Issue: AI responses are slow

**Solutions:**
1. Use streaming mode (already implemented)
2. Reduce context window size
3. Use faster model (gpt-3.5-turbo vs gpt-4)
4. Check network connection

---

## 📊 Visualization Issues

### Issue: Charts not rendering

**Solutions:**
1. Check browser console for errors
2. Ensure Plotly.js is loaded
3. Check dataset is uploaded and active
4. Try refreshing the page
5. Clear browser cache

### Issue: "No numeric columns found"

**Solution:**
- Dataset must have at least one numeric column for most chart types
- Check column types in Upload → Column Info tab
- Convert string numbers to numeric in data cleaning

---

## 🗺️ Map Issues

### Issue: Maps not loading

**Solutions:**
1. Check internet connection (maps load tiles from online sources)
2. Check browser console for errors
3. Ensure latitude/longitude columns exist
4. Column names should contain "lat", "lon", "latitude", or "longitude"

### Issue: "Invalid coordinates"

**Solutions:**
1. Latitude must be between -90 and 90
2. Longitude must be between -180 and 180
3. Check for null/NaN values
4. Use data cleaning to fix invalid values

---

## 💾 Database Issues

### Issue: "Database is locked"

**Solution:**
```bash
# Stop all backend processes
taskkill /F /IM python.exe

# Delete lock files
cd cognidata/backend
del cognidata.db-shm
del cognidata.db-wal

# Restart backend
```

### Issue: Database corruption

**Solution:**
```bash
# Backup current database
cd cognidata/backend
copy cognidata.db cognidata.db.backup

# Create fresh database
del cognidata.db
python -m app.seed

# Restore users if needed (manual SQL)
```

---

## 🌐 Network Issues

### Issue: CORS errors in browser

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/...' from origin 'http://localhost:5173' has been blocked by CORS policy
```

**Solution:**
Check `cognidata/backend/app/main.py`:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Add your frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue: Slow API responses

**Diagnostics:**
1. Check Debug → System page
2. Check network tab in browser (F12)
3. Check backend logs

**Solutions:**
1. Optimize queries
2. Add caching
3. Reduce dataset size
4. Use pagination
5. Check system resources (RAM, CPU)

---

## 📧 Email Issues

### Issue: "Email sending failed"

**Solutions:**
1. Check SMTP settings in `.env`:
   ```env
   SMTP_HOST=smtp.gmail.com
   SMTP_PORT=587
   SMTP_USER=your-email@gmail.com
   SMTP_PASSWORD=your-app-password  # Not regular password!
   SMTP_FROM=your-email@gmail.com
   ```

2. For Gmail, enable "App Passwords":
   - Go to Google Account settings
   - Security → 2-Step Verification → App passwords
   - Generate new app password
   - Use that password in .env

3. Check firewall allows outbound SMTP

---

## 🔧 Development Issues

### Issue: Changes not reflecting

**Solutions:**
1. **Backend**: Restart uvicorn (it auto-reloads, but sometimes needs restart)
2. **Frontend**: Clear vite cache:
   ```bash
   rm -rf cognidata/frontend/node_modules/.vite
   ```
3. Hard refresh browser (Ctrl+Shift+R)
4. Check file was saved

### Issue: Import errors

**Solution:**
```bash
# Backend
cd cognidata/backend
pip install -r requirements.txt --upgrade

# Frontend
cd cognidata/frontend
npm install
```

---

## 🧪 Testing Issues

### Issue: Tests failing

**Solution:**
```bash
cd cognidata/backend

# Run specific test
pytest tests/test_data.py -v

# Run with verbose output
pytest -vv

# Run with print statements
pytest -s

# Clear cache
pytest --cache-clear
```

---

## 🐛 General Debugging

### Get detailed logs

**Backend:**
```bash
cd cognidata/backend
uvicorn app.main:app --log-level debug
```

**Frontend:**
- Open browser console (F12)
- Check Network tab for API calls
- Check Console tab for JavaScript errors

### Check system resources

**Windows:**
```powershell
# Memory usage
tasklist | findstr python
tasklist | findstr node

# Port usage
netstat -ano | findstr :8000
netstat -ano | findstr :5173
```

### Reset everything

```bash
# Backend
cd cognidata/backend
rm cognidata.db
rm -rf __pycache__
rm -rf .pytest_cache
pip install -r requirements.txt --force-reinstall

# Frontend
cd cognidata/frontend
rm -rf node_modules
rm -rf dist
npm install

# Restart
powershell -ExecutionPolicy Bypass -File cognidata/run.ps1
```

---

## 📞 Getting Help

If issues persist:

1. **Check logs:**
   - Backend terminal output
   - Browser console (F12)
   - Network tab in DevTools

2. **Search existing issues:**
   - GitHub Issues: https://github.com/shivakumar0001/Cognidata_mainfinal/issues

3. **Create new issue:**
   - Include error messages
   - Include steps to reproduce
   - Include system info (OS, Python version, Node version)
   - Include relevant logs

4. **Documentation:**
   - README.md - Setup guide
   - FIXES_APPLIED.md - Recent fixes
   - API Docs - http://localhost:8000/docs

---

## 🔍 Common Error Codes

| Code | Meaning | Common Cause |
|------|---------|--------------|
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Not logged in or token expired |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist (e.g., no dataset uploaded) |
| 413 | Payload Too Large | File exceeds 200MB |
| 422 | Unprocessable Entity | Invalid file format or corrupt data |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Backend error (check logs) |

---

## ✅ Quick Fixes Checklist

Before asking for help, try:

- [ ] Restart backend
- [ ] Restart frontend  
- [ ] Clear browser cache
- [ ] Check .env file exists and has correct values
- [ ] Check Python packages installed (`pip list`)
- [ ] Check npm packages installed (`npm list`)
- [ ] Check ports 8000 and 5173 are not in use
- [ ] Check internet connection (for AI features and maps)
- [ ] Check OpenAI API key is valid
- [ ] Check dataset is uploaded (for data-related features)
- [ ] Check browser console for errors (F12)
- [ ] Try different browser
- [ ] Try incognito/private mode

---

**Still having issues?** Open an issue on GitHub with:
1. Error message (full text)
2. Steps to reproduce
3. Expected vs actual behavior
4. System info (OS, versions)
5. Screenshots if applicable

---

*Last Updated: June 29, 2026*

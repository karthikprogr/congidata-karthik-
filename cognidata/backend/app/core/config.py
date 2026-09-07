import os
from dotenv import load_dotenv
load_dotenv()

OPENAI_API_KEY  = os.getenv("OPENAI_API_KEY", "")
GEMINI_API_KEY  = os.getenv("GEMINI_API_KEY", "")
SECRET_KEY      = os.getenv("SECRET_KEY", "dev-secret-change-me")
DATABASE_URL    = os.getenv("DATABASE_URL", "sqlite:///./cognidata.db")
FRONTEND_URL    = os.getenv("FRONTEND_URL", "http://localhost:5173")
GOOGLE_CLIENT_ID     = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
GITHUB_CLIENT_ID     = os.getenv("GITHUB_CLIENT_ID", "")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET", "")
ALGORITHM       = "HS256"
TOKEN_EXPIRE_HOURS = 24

# SMTP
SMTP_HOST     = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
ADMIN_EMAIL   = os.getenv("ADMIN_EMAIL", "")
ALERT_EMAIL_ENABLED = os.getenv("ALERT_EMAIL_ENABLED", "false").lower() == "true"


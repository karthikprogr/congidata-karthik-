"""Seed system — runs once on startup to create admin account and welcome notifications."""
import os
from sqlalchemy.orm import Session
from app.core.database import SessionLocal, Base, engine
from app.models.user import User
from app.models.workspace import Workspace, WorkspaceMember, Invitation
from app.services.auth_service import create_user, get_user
from app.services.notification_service import send

def seed():
    """Initialize DB and create admin account from env vars."""
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        admin_email = os.getenv("ADMIN_EMAIL", "admin@cognidata.ai")
        admin_password = os.getenv("ADMIN_PASSWORD", "admin123")
        
        existing = get_user(db, admin_email)
        if existing:
            # Upgrade to admin if needed
            if existing.role != "admin":
                existing.role = "admin"
                db.commit()
                print(f"✅ Upgraded {admin_email} to admin")
            else:
                print(f"✅ Admin account already exists: {admin_email}")
            return
        
        # Create admin
        user = create_user(db, admin_email, admin_password)
        user.role = "admin"
        db.commit()
        print(f"✅ Admin account created: {admin_email}")
        
        # Send welcome notifications
        send(admin_email, "Welcome to COGNIDATA!", "Your platform is ready. Upload a dataset to get started.", "success")
        send(admin_email, "Admin Account Ready", f"You are logged in as admin. Visit the Admin Panel to manage users.", "info")
        print("✅ Welcome notifications sent")
        
    except Exception as e:
        print(f"⚠️ Seed error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed()

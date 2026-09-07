from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.core.database import Base

class Workspace(Base):
    __tablename__ = "workspaces"
    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(255), nullable=False)
    description = Column(String(1000), default="")
    owner_id    = Column(Integer, ForeignKey("users.id"))
    created_at  = Column(String(64))

class WorkspaceMember(Base):
    __tablename__ = "workspace_members"
    id           = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    user_id      = Column(Integer, ForeignKey("users.id"))
    role         = Column(String(50), default="viewer")

class Invitation(Base):
    __tablename__ = "invitations"
    id           = Column(Integer, primary_key=True)
    token        = Column(String(64), unique=True, index=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    email        = Column(String(255))
    role         = Column(String(50), default="viewer")
    status       = Column(String(20), default="pending")
    expires_at   = Column(String(64))
    created_at   = Column(String(64))

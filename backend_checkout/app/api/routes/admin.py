import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.document import Document
from app.db.models.chunk import Chunk
from app.db.models.query_session import QuerySession
from app.auth.dependencies import require_role

router = APIRouter()

class UserAdminResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    role: str
    is_active: bool
    created_at: str

class RoleUpdateRequest(BaseModel):
    role: str

class SystemUsageResponse(BaseModel):
    total_users: int
    total_knowledge_bases: int
    total_documents: int
    total_chunks: int
    total_queries: int

@router.get("/users", response_model=List[UserAdminResponse])
def get_users(
    limit: int = 20, 
    offset: int = 0, 
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("admin"))
):
    users = db.query(User).order_by(User.created_at.desc()).offset(offset).limit(limit).all()
    return [
        UserAdminResponse(
            user_id=str(u.id),
            email=u.email,
            full_name=u.full_name,
            role=u.role.value,
            is_active=u.is_active,
            created_at=u.created_at.isoformat()
        ) for u in users
    ]

@router.patch("/users/{user_id}/role")
def update_user_role(
    user_id: str, 
    request: RoleUpdateRequest,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("admin"))
):
    if user_id == str(admin_user.id):
        raise HTTPException(status_code=400, detail="Cannot change your own role")
        
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
        
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        new_role = UserRole(request.role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role: {request.role}")
        
    user.role = new_role
    db.commit()
    
    return {"message": "Role updated successfully"}

@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
    user_id: str,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("admin"))
):
    if user_id == str(admin_user.id):
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")
        
    try:
        user_uuid = uuid.UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format")
        
    user = db.query(User).filter(User.id == user_uuid).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user.is_active = False
    db.commit()
    
    return {"message": "User deactivated successfully"}

@router.get("/usage", response_model=SystemUsageResponse)
def get_usage_stats(
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role("admin"))
):
    return SystemUsageResponse(
        total_users=db.query(User).count(),
        total_knowledge_bases=db.query(KnowledgeBase).count(),
        total_documents=db.query(Document).count(),
        total_chunks=db.query(Chunk).count(),
        total_queries=db.query(QuerySession).count()
    )

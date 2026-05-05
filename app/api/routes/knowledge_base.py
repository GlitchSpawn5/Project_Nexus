from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.db.database import get_db
from app.db.models.knowledge_base import KnowledgeBase
from app.db.models.user import User, UserRole
from app.auth.dependencies import get_current_active_user

router = APIRouter()

class KnowledgeBaseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    owner_id: str
    created_at: str

@router.post("/", response_model=KnowledgeBaseResponse)
def create_knowledge_base(
    request: KnowledgeBaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    kb = KnowledgeBase(
        name=request.name,
        description=request.description,
        owner_id=current_user.id
    )
    db.add(kb)
    db.commit()
    db.refresh(kb)
    return KnowledgeBaseResponse(
        id=str(kb.id),
        name=kb.name,
        description=kb.description,
        owner_id=str(kb.owner_id),
        created_at=kb.created_at.isoformat()
    )

@router.get("/", response_model=List[KnowledgeBaseResponse])
def list_knowledge_bases(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    if current_user.role.value == UserRole.admin.value:
        kbs = db.query(KnowledgeBase).all()
    else:
        kbs = db.query(KnowledgeBase).filter(KnowledgeBase.owner_id == current_user.id).all()
        
    return [
        KnowledgeBaseResponse(
            id=str(kb.id),
            name=kb.name,
            description=kb.description,
            owner_id=str(kb.owner_id),
            created_at=kb.created_at.isoformat()
        ) for kb in kbs
    ]

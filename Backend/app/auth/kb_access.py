import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.user import User, UserRole
from app.db.models.knowledge_base import KnowledgeBase
from app.auth.dependencies import get_current_active_user

def verify_kb_access(
    kb_id: str, 
    current_user: Annotated[User, Depends(get_current_active_user)], 
    db: Session = Depends(get_db)
) -> KnowledgeBase:
    """
    Ensure the user is authorized to access the requested Knowledge Base.
    Admins can access everything. Other roles can only access KBs they own.
    """
    try:
        kb_uuid = uuid.UUID(kb_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid KB ID format")

    kb = db.query(KnowledgeBase).filter(KnowledgeBase.id == kb_uuid).first()
    if not kb:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Knowledge Base not found")

    if current_user.role.value == UserRole.admin.value:
        return kb

    if kb.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Access denied to this knowledge base"
        )
        
    return kb

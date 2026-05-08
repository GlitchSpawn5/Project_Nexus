from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from sqlalchemy.orm import Session
import uuid

from app.graph.graph_store import graph_store
from app.db.database import get_db
from app.db.models.chunk import Chunk
from app.auth.dependencies import get_current_active_user
from app.auth.kb_access import verify_kb_access
from app.db.models.user import User

router = APIRouter()

@router.get("/{kb_id}")
async def get_kb_graph(
    kb_id: str,
    db: Session = Depends(get_db),
    kb: None = Depends(verify_kb_access)
) -> Dict[str, Any]:
    """Returns the full knowledge base graph in D3.js-compatible format."""
    try:
        graph_data = graph_store.get_kb_graph(kb_id)
        return graph_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chain/{chunk_id}")
async def get_evidence_chain(
    chunk_id: str, 
    depth: int = 2,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """Returns the evidence chain subgraph rooted at a specific chunk."""
    try:
        chunk_uuid = uuid.UUID(chunk_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid chunk ID")
        
    chunk_rec = db.query(Chunk).filter(Chunk.id == chunk_uuid).first()
    if chunk_rec:
        verify_kb_access(str(chunk_rec.kb_id), current_user, db)
    try:
        chain_data = graph_store.get_evidence_chain(chunk_id, depth=depth)
        return chain_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{kb_id}/stats")
async def get_kb_graph_stats(
    kb_id: str,
    db: Session = Depends(get_db),
    kb: None = Depends(verify_kb_access)
) -> Dict[str, Any]:
    """Returns graph statistics."""
    try:
        graph_data = graph_store.get_kb_graph(kb_id)
        nodes = graph_data["nodes"]
        links = graph_data["links"]
        
        semantic_links = sum(1 for l in links if l.get("link_type") == "semantic")
        entity_links = sum(1 for l in links if l.get("link_type") == "entity")
        temporal_links = sum(1 for l in links if l.get("link_type") == "temporal")
        
        most_connected_chunk_id = None
        if nodes and links:
            from collections import defaultdict
            degrees = defaultdict(int)
            for link in links:
                degrees[link["source"]] += 1
                degrees[link["target"]] += 1
            if degrees:
                most_connected_chunk_id = max(degrees, key=degrees.get)
        
        return {
            "total_nodes": len(nodes),
            "total_edges": len(links),
            "semantic_links": semantic_links,
            "entity_links": entity_links,
            "temporal_links": temporal_links,
            "most_connected_chunk_id": most_connected_chunk_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

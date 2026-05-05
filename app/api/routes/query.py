"""
Query Router
============
POST /query — Retrieve top matching chunks for a query from the vector store.
"""

from typing import Optional, List
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.chunk import Chunk
from app.db.models.document import Document
from app.embeddings import embedding_service
from app.vectorstore import chroma_store
from app.auth.dependencies import get_current_active_user
from app.auth.kb_access import verify_kb_access
from app.db.models.user import User

router = APIRouter()

class QueryRequest(BaseModel):
    kb_id: str
    query: str
    top_k: int = 10
    modality_filter: str = "all"
    exclude_modalities: Optional[List[str]] = None
    expand_evidence_chains: bool = False
    generate_answer: bool = False

class QueryResult(BaseModel):
    chunk_id: str
    text: str
    score: float
    document_id: str
    filename: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    modality: str
    chunk_index: int
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    language: Optional[str] = None

class LinkedChunk(BaseModel):
    chunk_id: str
    modality: str
    link_type: str
    strength: float
    text_preview: str
    filename: str
    timestamp_start: Optional[float] = None
    page_number: Optional[int] = None

class EvidenceChain(BaseModel):
    root_chunk_id: str
    root_modality: str
    linked_chunks: List[LinkedChunk]

class AnswerCitation(BaseModel):
    chunk_id: str
    citation_label: str
    modality: str
    filename: str
    page_number: Optional[int] = None
    timestamp_start: Optional[float] = None
    timestamp_end: Optional[float] = None
    section_heading: Optional[str] = None

class AnswerResponse(BaseModel):
    text: str
    annotated_text: str
    citations: List[AnswerCitation]
    citation_list: str
    confidence_score: float
    insufficient_evidence: bool
    llm_provider: str
    session_id: str

class QueryResponse(BaseModel):
    kb_id: str
    query: str
    results: List[QueryResult]
    total_results: int
    evidence_chains: Optional[List[EvidenceChain]] = None
    answer: Optional[AnswerResponse] = None

@router.post("/", response_model=QueryResponse)
async def query_knowledge_base(
    request: QueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Retrieve semantically similar chunks from the knowledge base."""
    # Authorize access
    verify_kb_access(request.kb_id, current_user, db)
    
    from app.embeddings import clip_service
    
    # 1. Embed the query string based on modalities
    query_embedding_dict = {}
    
    if request.modality_filter in ("text", "all"):
        query_embedding_dict["text"] = embedding_service.embed_text(request.query)
        
    if request.modality_filter in ("image", "all"):
        query_embedding_dict["image"] = clip_service.embed_text_for_image_search(request.query)
    
    # 2. Prepare filters
    filters = None
    
    # 3. Search ChromaDB
    try:
        chroma_results = chroma_store.query(
            kb_id=request.kb_id,
            query_embedding_dict=query_embedding_dict,
            top_k=request.top_k,
            filters=filters,
            modality=request.modality_filter
        )
    except ValueError as e:
        # Collection might not exist yet if empty
        return QueryResponse(
            kb_id=request.kb_id,
            query=request.query,
            results=[],
            total_results=0
        )
        
    if not chroma_results:
        return QueryResponse(
            kb_id=request.kb_id,
            query=request.query,
            results=[],
            total_results=0
        )
        
    # 4. Fetch full DB records to enrich the response
    chunk_ids_str = [res["chunk_id"] for res in chroma_results]
    chunk_uuids = [uuid.UUID(cid) for cid in chunk_ids_str]
    
    # Query Chunks and join with Documents to get filename
    db_chunks = db.query(Chunk, Document.filename, Document.language)\
                  .join(Document, Chunk.document_id == Document.id)\
                  .filter(Chunk.id.in_(chunk_uuids))\
                  .all()
                  
    # Map for O(1) lookup
    db_chunk_map = {
        str(chunk.id): {"chunk": chunk, "filename": filename, "language": language}
        for chunk, filename, language in db_chunks
    }
    
    # 5. Build the exclude set (if any)
    exclude_set = set(request.exclude_modalities) if request.exclude_modalities else set()
    
    # 6. Format results
    final_results = []
    for res in chroma_results:
        chunk_id = res["chunk_id"]
        db_data = db_chunk_map.get(chunk_id)
        
        if not db_data:
            # Chunk is in Chroma but missing from DB (should not happen normally)
            continue
            
        chunk_record = db_data["chunk"]
        filename = db_data["filename"]
        doc_language = db_data["language"]
        
        # Apply exclude_modalities filter
        if chunk_record.modality.value in exclude_set:
            continue
        
        # Merge metadata from DB
        final_results.append(QueryResult(
            chunk_id=chunk_id,
            text=res["text"],
            score=res["score"],
            document_id=str(chunk_record.document_id),
            filename=filename,
            page_number=chunk_record.page_number,
            section_heading=chunk_record.metadata_json.get("section_heading") if chunk_record.metadata_json else None,
            modality=chunk_record.modality.value,
            chunk_index=chunk_record.chunk_index,
            timestamp_start=chunk_record.timestamp_start,
            timestamp_end=chunk_record.timestamp_end,
            language=doc_language,
        ))
        
    # 7. Expand evidence chains if requested
    evidence_chains = []
    if request.expand_evidence_chains:
        from app.graph.graph_store import graph_store
        
        # Collect all neighbour IDs to fetch from DB in one go
        neighbour_map = {} # root_id -> list of neighbours
        all_neighbour_ids = set()
        
        for res in final_results:
            neighbours = graph_store.get_neighbours(res.chunk_id, min_strength=0.5)
            if neighbours:
                neighbour_map[res.chunk_id] = neighbours
                all_neighbour_ids.update(n["chunk_id"] for n in neighbours)
                
        if all_neighbour_ids:
            # Fetch all neighbour details from DB
            n_uuids = [uuid.UUID(nid) for nid in all_neighbour_ids]
            n_db_chunks = db.query(Chunk, Document.filename)\
                            .join(Document, Chunk.document_id == Document.id)\
                            .filter(Chunk.id.in_(n_uuids))\
                            .all()
            
            n_db_map = {str(c.id): {"chunk": c, "filename": fname} for c, fname in n_db_chunks}
            
            # Build the evidence_chains payload
            for root_id, root_modality in [(r.chunk_id, r.modality) for r in final_results]:
                if root_id in neighbour_map:
                    linked_chunks = []
                    for n in neighbour_map[root_id]:
                        nid = n["chunk_id"]
                        if nid in n_db_map:
                            c_data = n_db_map[nid]
                            c_rec = c_data["chunk"]
                            
                            # Filter excluded modalities in neighbours too
                            if c_rec.modality.value in exclude_set:
                                continue
                                
                            linked_chunks.append(LinkedChunk(
                                chunk_id=nid,
                                modality=c_rec.modality.value,
                                link_type=n["link_type"],
                                strength=n["strength"],
                                text_preview=c_rec.content_text[:100] if c_rec.content_text else "",
                                filename=c_data["filename"],
                                timestamp_start=c_rec.timestamp_start,
                                page_number=c_rec.page_number
                            ))
                            
                    if linked_chunks:
                        evidence_chains.append(EvidenceChain(
                            root_chunk_id=root_id,
                            root_modality=root_modality,
                            linked_chunks=linked_chunks
                        ))
        
        
    # 8. Generate answer if requested
    answer_block = None
    if request.generate_answer:
        from app.llm.answer_service import AnswerService
        
        # Convert final_results back to a list of dicts for PromptBuilder
        chunks_for_prompt = []
        for r in final_results:
            chunks_for_prompt.append({
                "chunk_id": r.chunk_id,
                "text": r.text,
                "score": r.score,
                "modality": r.modality,
                "filename": r.filename,
                "page_number": r.page_number,
                "section_heading": r.section_heading,
                "timestamp_start": r.timestamp_start,
                "timestamp_end": r.timestamp_end
            })
            
        evidence_chains_for_prompt = []
        if evidence_chains:
            for ec in evidence_chains:
                evidence_chains_for_prompt.append(ec.model_dump())
                
        answer_svc = AnswerService()
        answer_dict = answer_svc.generate(
            query=request.query,
            chunks=chunks_for_prompt,
            evidence_chains=evidence_chains_for_prompt,
            kb_id=request.kb_id,
            db=db
        )
        
        answer_block = AnswerResponse(
            text=answer_dict["answer"],
            annotated_text=answer_dict["annotated_answer"],
            citations=[AnswerCitation(**c) for c in answer_dict["citations"]],
            citation_list=answer_dict["citation_list"],
            confidence_score=answer_dict["confidence_score"],
            insufficient_evidence=answer_dict["insufficient_evidence"],
            llm_provider=answer_dict["llm_provider"],
            session_id=answer_dict["session_id"]
        )
        
    return QueryResponse(
        kb_id=request.kb_id,
        query=request.query,
        results=final_results,
        total_results=len(final_results),
        evidence_chains=evidence_chains if request.expand_evidence_chains else None,
        answer=answer_block
    )

from app.db.models.query_session import QuerySession
from sqlalchemy import desc

class SessionHistoryResponse(BaseModel):
    session_id: str
    query_text: str
    answer_preview: str
    confidence_score: Optional[float]
    citation_count: int
    insufficient_evidence: bool
    llm_provider: str
    created_at: str

class QueryHistoryResponse(BaseModel):
    kb_id: str
    total: int
    sessions: List[SessionHistoryResponse]

@router.get("/history", response_model=QueryHistoryResponse)
def get_query_history(
    kb_id: str,
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
    kb: None = Depends(verify_kb_access)
):
    """Retrieve past query sessions for a knowledge base."""
    total = db.query(QuerySession).filter(QuerySession.kb_id == kb_id).count()
    
    sessions = db.query(QuerySession)\
                 .filter(QuerySession.kb_id == kb_id)\
                 .order_by(desc(QuerySession.created_at))\
                 .offset(offset)\
                 .limit(limit)\
                 .all()
                 
    session_responses = []
    for s in sessions:
        preview = s.final_answer[:200] if s.final_answer else ""
        session_responses.append(SessionHistoryResponse(
            session_id=str(s.id),
            query_text=s.query_text,
            answer_preview=preview,
            confidence_score=s.confidence_score,
            citation_count=s.citation_count,
            insufficient_evidence=s.insufficient_evidence,
            llm_provider=s.llm_provider,
            created_at=s.created_at.isoformat()
        ))
        
    return QueryHistoryResponse(
        kb_id=kb_id,
        total=total,
        sessions=session_responses
    )


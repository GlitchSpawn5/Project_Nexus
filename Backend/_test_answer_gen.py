from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db.database import Base
from app.db.models.query_session import QuerySession
from app.llm.prompt_builder import PromptBuilder
from app.llm.citation_parser import CitationParser
from app.llm.answer_service import AnswerService
import os

print("=== Testing Answer Generation Component Logic ===")

# Create in-memory DB
engine = create_engine("sqlite:///:memory:")
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

# 1. Test Prompt Builder
pb = PromptBuilder()
chunks = [
    {"chunk_id": "111", "text": "The sky is blue.", "modality": "text", "filename": "doc1.txt", "page_number": 1, "score": 0.95},
    {"chunk_id": "222", "text": "Apples are red.", "modality": "text", "filename": "doc2.txt", "section_heading": "Fruits", "score": 0.85},
    {"chunk_id": "333", "text": "Grass is green.", "modality": "text", "filename": "doc3.txt", "score": 0.75}
]
evidence_chains = [
    {
        "root_chunk_id": "111",
        "linked_chunks": [
            {"chunk_id": "444", "modality": "image", "link_type": "semantic", "strength": 0.88, "text_preview": "A photo of a blue sky", "filename": "sky.jpg"}
        ]
    }
]

prompt = pb.build_user_prompt("What colors are the sky and apples?", chunks, evidence_chains)
print("PROMPT:")
print(prompt)

# 2. Test Citation Parser
cp = CitationParser()
raw_answer = "The sky is blue [SOURCE: 111]. Also, apples are red [SOURCE: 222]. I don't know about grass."
parsed = cp.parse(raw_answer, chunks)

print("\nPARSED CITATIONS:")
for c in parsed["cited_chunks"]:
    print(c)
print(f"Annotated: {parsed['annotated_answer']}")
print(f"List:\n{cp.format_citation_list(parsed['cited_chunks'])}")

# 3. Test Insufficient Evidence
raw_answer_ins = "INSUFFICIENT_EVIDENCE"
parsed_ins = cp.parse(raw_answer_ins, chunks)
assert parsed_ins["insufficient_evidence"] is True
assert parsed_ins["citation_count"] == 0

# 4. Mock AnswerService and test Database Insertion
class MockAnswerService(AnswerService):
    def generate(self, query: str, chunks: list[dict], evidence_chains: list[dict] | None, kb_id: str, db) -> dict:
        parsed = cp.parse(raw_answer, chunks)
        
        cited_chunk_ids = {c["chunk_id"] for c in parsed["cited_chunks"]}
        cited_scores = [c.get("score", 0.0) for c in chunks if c.get("chunk_id") in cited_chunk_ids]

        if cited_scores:
            confidence_score = round(sum(cited_scores) / len(cited_scores), 3)
        else:
            confidence_score = 0.0
            
        session_record = QuerySession(
            kb_id=kb_id,
            query_text=query,
            llm_provider="mock_groq",
            raw_llm_response=raw_answer,
            final_answer=parsed["annotated_answer"],
            confidence_score=confidence_score,
            citation_count=parsed["citation_count"],
            insufficient_evidence=parsed["insufficient_evidence"],
            retrieved_chunk_ids=[c.get("chunk_id") for c in chunks]
        )
        db.add(session_record)
        db.commit()
        db.refresh(session_record)
        
        return {"session_id": str(session_record.id), "confidence": confidence_score}

svc = MockAnswerService()
res = svc.generate("Query?", chunks, evidence_chains, "kb1", db)
print("\nGenerated Session ID:", res["session_id"])
print("Confidence Score (should be (0.95+0.85)/2 = 0.900):", res["confidence"])
assert res["confidence"] == 0.900

# Fetch from DB
saved_session = db.query(QuerySession).first()
print("Saved query_text:", saved_session.query_text)
print("Saved final_answer:", saved_session.final_answer)

print("\n=== All Answer Generation Tests Passed ===")

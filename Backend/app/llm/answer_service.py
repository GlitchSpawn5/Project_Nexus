from sqlalchemy.orm import Session
from app.llm.prompt_builder import PromptBuilder
from app.llm.citation_parser import CitationParser
from app.llm.factory import complete_with_fallback
from app.db.models.query_session import QuerySession

class AnswerService:
    def __init__(self):
        self.prompt_builder = PromptBuilder()
        self.citation_parser = CitationParser()

    def generate(self, query: str, chunks: list[dict], evidence_chains: list[dict] | None, kb_id: str, db: Session) -> dict:
        # Build prompts
        system_prompt = self.prompt_builder.build_system_prompt()
        user_prompt = self.prompt_builder.build_user_prompt(query, chunks, evidence_chains)

        # Call LLM with fallback
        raw_answer, provider_name = complete_with_fallback(system_prompt, user_prompt, max_tokens=1500)

        # Parse citations
        parsed = self.citation_parser.parse(raw_answer, chunks)

        # Compute confidence score based ONLY on cited chunks
        cited_chunk_ids = {c["chunk_id"] for c in parsed["cited_chunks"]}
        cited_scores = [c.get("score", 0.0) for c in chunks if c.get("chunk_id") in cited_chunk_ids]

        if cited_scores:
            confidence_score = round(sum(cited_scores) / len(cited_scores), 3)
        else:
            confidence_score = 0.0

        # Create QuerySession record
        session_record = QuerySession(
            kb_id=kb_id,
            query_text=query,
            llm_provider=provider_name,
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

        return {
            "answer": parsed["answer_text"],
            "annotated_answer": parsed["annotated_answer"],
            "citations": parsed["cited_chunks"],
            "citation_list": self.citation_parser.format_citation_list(parsed["cited_chunks"]),
            "insufficient_evidence": parsed["insufficient_evidence"],
            "confidence_score": confidence_score,
            "llm_provider": provider_name,
            "session_id": str(session_record.id)
        }

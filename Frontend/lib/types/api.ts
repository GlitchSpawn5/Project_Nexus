// Hand-written types matching the NEXUS FastAPI backend schema

export type UserRole = "admin" | "owner" | "editor" | "viewer";
export type DocumentStatus = "pending" | "processing" | "ready" | "error" | "complete" | "failed";
export type JobStatus = "queued" | "processing" | "complete" | "failed";
export type Modality = "text" | "image" | "audio";
export type ModalityFilter = "all" | "text" | "image" | "audio";
export type LinkType = "semantic" | "entity" | "temporal";

// ── Auth ──────────────────────────────────────────────────────────────────
export interface User {
  user_id: string;
  id: string; // aliased from user_id in API layer
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  role: string;
  user_id: string;
}

export interface LoginRequest {
  username: string; // email (OAuth2 form field)
  password: string;
}

export interface RegisterRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// ── Knowledge Base ────────────────────────────────────────────────────────
export interface KnowledgeBase {
  id: string;
  name: string;
  description: string;
  owner_id: string;
  created_at: string;
}

export interface CreateKBRequest {
  name: string;
  description?: string;
}

// ── Documents & Ingestion ─────────────────────────────────────────────────
export interface Document {
  id: string;
  kb_id: string;
  filename: string;
  file_type: string;
  file_path: string;
  status: DocumentStatus;
  language?: string;
  page_count?: number;
  duration_seconds?: number;
  created_at: string;
}

export interface IngestionJob {
  job_id: string;
  document_id: string;
  status: JobStatus;
  progress_pct: number;
  error_message?: string;
  started_at?: string;
  completed_at?: string;
  total_chunks?: number;
  language?: string;
  page_count?: number;
}

export interface UploadResponse {
  job_id: string;
  document_id: string;
  status: JobStatus;
}

export interface Transcript {
  document_id: string;
  filename: string;
  duration_seconds?: number;
  language?: string;
  chunks: Array<{
    chunk_index: number;
    text: string;
    timestamp_start?: number;
    timestamp_end?: number;
  }>;
}

// ── Query ─────────────────────────────────────────────────────────────────
export interface QueryRequest {
  kb_id: string;
  query: string;
  top_k?: number;
  modality_filter?: ModalityFilter;
  exclude_modalities?: Modality[];
  expand_evidence_chains?: boolean;
  generate_answer?: boolean;
}

export interface QueryResult {
  chunk_id: string;
  text: string;
  score: number;
  document_id: string;
  filename: string;
  page_number?: number;
  section_heading?: string;
  modality: Modality;
  chunk_index: number;
  timestamp_start?: number;
  timestamp_end?: number;
  language?: string;
}

export interface AnswerCitation {
  chunk_id: string;
  citation_label: string;
  modality: string;
  filename: string;
  page_number?: number;
  timestamp_start?: number;
  timestamp_end?: number;
  section_heading?: string;
}

export interface AnswerResponse {
  text: string;
  annotated_text: string;
  citations: AnswerCitation[];
  citation_list: string;
  confidence_score: number;
  insufficient_evidence: boolean;
  llm_provider: string;
  session_id: string;
}

export interface QueryResponse {
  kb_id: string;
  query: string;
  results: QueryResult[];
  total_results: number;
  answer?: AnswerResponse;
}

export interface QuerySession {
  id: string; // aliased from session_id in API layer
  session_id: string;
  query_text: string;
  answer_preview: string;
  confidence_score?: number;
  citation_count: number;
  insufficient_evidence: boolean;
  llm_provider: string;
  created_at: string;
}

// ── Graph ─────────────────────────────────────────────────────────────────
export interface GraphNode {
  id: string;
  modality: Modality;
  text_preview?: string;
  document_id?: string;
  chunk_index?: number;
  page_number?: number;
  timestamp_start?: number;
  [key: string]: unknown;
}

export interface GraphEdge {
  source: string;
  target: string;
  link_type: LinkType;
  weight?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphEdge[];
}

export interface GraphStats {
  total_nodes: number;
  total_edges: number;
  semantic_links: number;
  entity_links: number;
  temporal_links: number;
  most_connected_chunk_id?: string;
}

// ── Admin ─────────────────────────────────────────────────────────────────
export interface AdminUser {
  user_id: string;
  id: string; // aliased from user_id in API layer
  email: string;
  full_name: string;
  role: UserRole;
  is_active: boolean;
  created_at: string;
}

export interface UsageStats {
  total_users: number;
  total_knowledge_bases: number;
  total_documents: number;
  total_chunks: number;
  total_queries: number;
}

export interface SetRoleRequest {
  role: UserRole;
}

// ── LLM ──────────────────────────────────────────────────────────────────
export interface ProviderStatus {
  provider: string;
  available: boolean;
  configured: boolean;
  status: string;
}

export interface LLMStatus {
  primary_provider: string;
  primary_status: string;
  auto_fallback_enabled: boolean;
  fallback_chain: string[];
  providers: ProviderStatus[];
}

import type {
  AdminUser,
  CreateKBRequest,
  Document,
  GraphData,
  GraphStats,
  IngestionJob,
  KnowledgeBase,
  LLMStatus,
  LoginRequest,
  QueryRequest,
  QueryResponse,
  QuerySession,
  TokenResponse,
  Transcript,
  UploadResponse,
  User,
} from "../types/api";

export const useMockApi = import.meta.env.VITE_USE_MOCK_API !== "false";

const now = new Date().toISOString();

const mockUser: User = {
  user_id: "global-admin",
  id: "global-admin",
  email: "admin@nexus.global",
  full_name: "NEXUS Administrator",
  role: "admin",
  is_active: true,
  created_at: now,
};

let knowledgeBases: KnowledgeBase[] = [
  {
    id: "kb-demo",
    name: "Global Policy Intelligence",
    description: "Company-wide policies, operating procedures, and regional compliance guidance.",
    owner_id: mockUser.user_id,
    created_at: now,
  },
];

let documents: Document[] = [
  {
    id: "doc-demo",
    kb_id: "kb-demo",
    filename: "global-compliance-handbook.pdf",
    file_type: "pdf",
    file_path: "/library/global-compliance-handbook.pdf",
    status: "ready",
    language: "en",
    page_count: 4,
    created_at: now,
  },
];

function delay<T>(value: T, ms = 200): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

export const mockApi = {
  async login(data: LoginRequest): Promise<TokenResponse> {
    if (!data.username || !data.password) {
      throw new Error("Enter your email and password to continue.");
    }

    return delay({
      access_token: "development-token",
      token_type: "bearer",
      role: mockUser.role,
      user_id: mockUser.user_id,
    });
  },

  async register(): Promise<User> {
    return delay(mockUser);
  },

  async getMe(): Promise<User> {
    return delay(mockUser);
  },

  async changePassword(): Promise<void> {
    return delay(undefined);
  },

  async listKBs(): Promise<KnowledgeBase[]> {
    return delay([...knowledgeBases]);
  },

  async createKB(data: CreateKBRequest): Promise<KnowledgeBase> {
    const kb: KnowledgeBase = {
      id: `kb-${Date.now()}`,
      name: data.name,
      description: data.description ?? "",
      owner_id: mockUser.user_id,
      created_at: new Date().toISOString(),
    };
    knowledgeBases = [kb, ...knowledgeBases];
    return delay(kb);
  },

  async uploadFile(kbId: string, file: File, onProgress?: (pct: number) => void): Promise<UploadResponse> {
    onProgress?.(100);
    const document: Document = {
      id: `doc-${Date.now()}`,
      kb_id: kbId,
      filename: file.name,
      file_type: file.name.split(".").pop() ?? "file",
      file_path: `/uploads/${file.name}`,
      status: "ready",
      language: "en",
      page_count: 1,
      created_at: new Date().toISOString(),
    };
    documents = [document, ...documents];
    return delay({
      job_id: `job-${Date.now()}`,
      document_id: document.id,
      status: "complete",
    });
  },

  async getJob(jobId: string): Promise<IngestionJob> {
    return delay({
      job_id: jobId,
      document_id: "doc-demo",
      status: "complete",
      progress_pct: 100,
      completed_at: now,
      total_chunks: 8,
      language: "en",
      page_count: 4,
    });
  },

  async getDocuments(kbId: string): Promise<Document[]> {
    return delay(documents.filter((document) => document.kb_id === kbId));
  },

  async deleteDocument(docId: string): Promise<void> {
    documents = documents.filter((document) => document.id !== docId);
    return delay(undefined);
  },

  async getTranscript(docId: string): Promise<Transcript> {
    const document = documents.find((item) => item.id === docId);
    return delay({
      document_id: docId,
      filename: document?.filename ?? "leadership-briefing.wav",
      language: "en",
      duration_seconds: 64,
      chunks: [
        {
          chunk_index: 0,
          text: "Regional leaders reviewed compliance priorities, customer commitments, and evidence requirements for the quarter.",
          timestamp_start: 0,
          timestamp_end: 12,
        },
      ],
    });
  },

  async ask(data: QueryRequest): Promise<QueryResponse> {
    return delay({
      kb_id: data.kb_id,
      query: data.query,
      total_results: 1,
      results: [
        {
          chunk_id: "chunk-demo",
          text: "NEXUS connects policies, reports, images, and audio transcripts into governed evidence networks for global teams.",
          score: 0.92,
          document_id: "doc-demo",
          filename: "global-compliance-handbook.pdf",
          page_number: 1,
          section_heading: "Overview",
          modality: "text",
          chunk_index: 0,
          language: "en",
        },
      ],
      answer: {
        text: "NEXUS provides governed multimodal search with cited AI answers, helping global teams find trustworthy evidence across distributed content.",
        annotated_text: "NEXUS provides governed multimodal search with cited AI answers [1], helping global teams find trustworthy evidence across distributed content.",
        citations: [
          {
            chunk_id: "chunk-demo",
            citation_label: "[1]",
            modality: "text",
            filename: "global-compliance-handbook.pdf",
            page_number: 1,
            section_heading: "Overview",
          },
        ],
        citation_list: "[1] global-compliance-handbook.pdf, page 1",
        confidence_score: 0.86,
        insufficient_evidence: false,
        llm_provider: "enterprise-routing",
        session_id: `session-${Date.now()}`,
      },
    });
  },

  async getQueryHistory(): Promise<QuerySession[]> {
    return delay([
      {
        id: "session-demo",
        session_id: "session-demo",
        query_text: "What is this app?",
        answer_preview: "A governed knowledge intelligence platform for global evidence discovery.",
        confidence_score: 0.86,
        citation_count: 1,
        insufficient_evidence: false,
        llm_provider: "enterprise-routing",
        created_at: now,
      },
    ]);
  },

  async getGraph(): Promise<GraphData> {
    return delay({
      nodes: [
        { id: "chunk-demo", modality: "text", text_preview: "Global compliance evidence", document_id: "doc-demo", chunk_index: 0 },
        { id: "chunk-related", modality: "image", text_preview: "Related regional operating evidence", document_id: "doc-demo", chunk_index: 1 },
      ],
      links: [{ source: "chunk-demo", target: "chunk-related", link_type: "semantic", weight: 0.8 }],
    });
  },

  async getGraphStats(): Promise<GraphStats> {
    return delay({
      total_nodes: 2,
      total_edges: 1,
      semantic_links: 1,
      entity_links: 0,
      temporal_links: 0,
      most_connected_chunk_id: "chunk-demo",
    });
  },

  async listUsers(): Promise<AdminUser[]> {
    return delay([mockUser]);
  },

  async getUsageStats() {
    return delay({
      total_users: 1,
      total_knowledge_bases: knowledgeBases.length,
      total_documents: documents.length,
      total_chunks: 8,
      total_queries: 1,
    });
  },

  async getLLMStatus(): Promise<LLMStatus> {
    return delay({
      primary_provider: "groq",
      primary_status: "ok",
      auto_fallback_enabled: true,
      fallback_chain: ["groq", "gemini", "ollama"],
      providers: [
        { provider: "groq", available: true, configured: true, status: "ok" },
        { provider: "gemini", available: true, configured: true, status: "standby" },
        { provider: "ollama", available: true, configured: true, status: "standby" },
      ],
    });
  },
};

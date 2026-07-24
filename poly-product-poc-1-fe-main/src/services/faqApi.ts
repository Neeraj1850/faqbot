import api from '@/lib/axios';
import { FAQ } from '@/types/faq';

// Response types from API
export interface ApiFaq {
  id: string;
  section: string;
  question: string;
  answer: string;
  created_at?: string;
  updated_at?: string;
}

export interface ChatQueryResponse {
  conversation_id: string | null;
  query: string;
  results: ApiFaq[];
  message?: string;
}

export interface ApiConversation {
  id: string;
  user_id: string;
  created_at: string;
  updated_at: string;
}

export interface ApiMessage {
  id: string;
  conversation_id: string;
  user_id: string;
  role: "user" | "agent";
  content: string;
  source: string;
  timestamp: string;
}

export interface IngestResponse {
  success: boolean;
  message: string;
  faqs_created?: number;
}

// Transform API response to app format
const transformFaq = (apiFaq: ApiFaq): FAQ => ({
  id: apiFaq.id,
  section: apiFaq.section,
  question: apiFaq.question,
  answer: apiFaq.answer,
  createdAt: apiFaq.created_at ? new Date(apiFaq.created_at) : new Date(),
  updatedAt: apiFaq.updated_at ? new Date(apiFaq.updated_at) : new Date(),
});

// FAQ API endpoints
export const faqApi = {
  // GET /faq - Fetch all FAQs
  getAll: async (): Promise<FAQ[]> => {
    const response = await api.get<ApiFaq[]>('/faq');
    return response.data.map(transformFaq);
  },

  // POST /faq - Create a new FAQ
  create: async (data: { section: string; question: string; answer: string }): Promise<FAQ> => {
    const response = await api.post<ApiFaq>('/faq', data);
    return transformFaq(response.data);
  },

  // PUT /faq/:id - Update an FAQ
  update: async (id: string, data: { section?: string; question?: string; answer?: string }): Promise<FAQ> => {
    const response = await api.put<ApiFaq>(`/faq/${id}`, data);
    return transformFaq(response.data);
  },

  // DELETE /faq/:id - Delete an FAQ
  delete: async (id: string): Promise<void> => {
    await api.delete(`/faq/${id}`);
  },
};

// Chat API endpoints
export const chatApi = {
  // POST /chat/query - Query for relevant FAQs. Omit conversationId to start
  // a new chat (the backend creates one); pass one back to continue it.
  query: async (query: string, conversationId?: string | null): Promise<ChatQueryResponse> => {
    const response = await api.post<ChatQueryResponse>('/chat/query', {
      query,
      conversation_id: conversationId ?? null,
    });
    return {
      ...response.data,
      results: response.data.results.map(transformFaq),
    };
  },

  // GET /chat/conversations - This user's conversations, most recent first.
  listConversations: async (): Promise<ApiConversation[]> => {
    const response = await api.get<ApiConversation[]>('/chat/conversations');
    return response.data;
  },

  // GET /chat/conversations/:id/messages - Full history for one conversation.
  getMessages: async (conversationId: string): Promise<ApiMessage[]> => {
    const response = await api.get<ApiMessage[]>(`/chat/conversations/${conversationId}/messages`);
    return response.data;
  },
};

// Ingest API endpoints
export const ingestApi = {
  // POST /ingest/pdf - Upload PDF for ingestion
  uploadPdf: async (file: File, onProgress?: (progress: number) => void): Promise<IngestResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<IngestResponse>('/ingest/pdf', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: (progressEvent) => {
        if (onProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total);
          onProgress(progress);
        }
      },
    });

    return response.data;
  },
};

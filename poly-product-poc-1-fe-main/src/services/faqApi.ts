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
  query: string;
  results: ApiFaq[];
  message?: string;
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
  // POST /chat/query - Query for relevant FAQs
  query: async (query: string): Promise<ChatQueryResponse> => {
    const response = await api.post<ChatQueryResponse>('/chat/query', { query });
    return {
      ...response.data,
      results: response.data.results.map(transformFaq),
    };
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

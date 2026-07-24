export interface FAQ {
  id: string;
  section: string;
  question: string;
  answer: string;
  createdAt: Date;
  updatedAt: Date;
}

export interface Section {
  id: string;
  name: string;
  faqCount: number;
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  faqs?: FAQ[];
  timestamp: Date;
}

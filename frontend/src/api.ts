export interface Source {
  song_id: number;
  title: string;
  movie: string | null;
  matched_text: string | null;
  score: number | null;
  source_type: string;
}

export interface ChatResponse {
  answer: string;
  sources: Source[];
  retrieval_type: string;
  latency_ms: number;
}

export interface ChatRequest {
  question: string;
  top_k?: number;
}

export const fetchChatResponse = async (query: string): Promise<ChatResponse> => {
  // If VITE_API_URL is set (Production), it uses that (e.g. https://railway.app).
  // If not set (Local dev), it defaults to '/api' which uses the Vite proxy!
  const apiUrl = import.meta.env.VITE_API_URL || '/api';
  const response = await fetch(`${apiUrl}/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ question: query, top_k: 5 }),
  });

  if (!response.ok) {
    throw new Error('Failed to fetch response from server');
  }

  return response.json();
};

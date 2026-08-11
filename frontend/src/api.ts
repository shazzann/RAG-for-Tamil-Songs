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
  const response = await fetch('/api/chat/', {
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

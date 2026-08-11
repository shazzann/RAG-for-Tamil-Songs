import React, { useState } from 'react';
import { Send, Sparkles } from 'lucide-react';
import './QueryInput.css';

interface QueryInputProps {
  onSend: (query: string) => void;
  isLoading: boolean;
}

const EXAMPLES = [
  "Which songs describe missing someone?",
  "Who composed Roja Janapathi?",
  "காதல் பாடல்கள்", // "Love songs" in Tamil
  "Songs by Anirudh from 2022"
];

export const QueryInput: React.FC<QueryInputProps> = ({ onSend, isLoading }) => {
  const [query, setQuery] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (query.trim() && !isLoading) {
      onSend(query.trim());
      setQuery('');
    }
  };

  const handleExampleClick = (example: string) => {
    if (!isLoading) {
      onSend(example);
    }
  };

  return (
    <div className="query-input-container">
      <div className="examples-container">
        {EXAMPLES.map((example, idx) => (
          <button
            key={idx}
            className="example-chip glass-panel glass-panel-hover"
            onClick={() => handleExampleClick(example)}
            disabled={isLoading}
          >
            <Sparkles size={12} className="text-primary" />
            <span>{example}</span>
          </button>
        ))}
      </div>
      
      <form onSubmit={handleSubmit} className="input-form glass-panel">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about Tamil songs, lyrics, or composers..."
          className="query-textarea"
          rows={1}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSubmit(e);
            }
          }}
          disabled={isLoading}
        />
        <button 
          type="submit" 
          className="send-button"
          disabled={!query.trim() || isLoading}
        >
          <Send size={18} />
        </button>
      </form>
    </div>
  );
};

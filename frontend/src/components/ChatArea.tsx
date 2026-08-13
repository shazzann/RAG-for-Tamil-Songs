import React from 'react';
import { Bot, User } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import './ChatArea.css';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

interface ChatAreaProps {
  messages: Message[];
  isLoading: boolean;
  error: string | null;
}

export const ChatArea: React.FC<ChatAreaProps> = ({ messages, isLoading, error }) => {
  return (
    <div className="chat-area-container glass-panel">
      {messages.length === 0 ? (
        <div className="empty-state">
          <Bot size={48} className="text-primary mb-4" />
          <h2 className="text-gradient">Tamil Song RAG</h2>
          <p className="text-muted">Ask a question about Tamil songs, lyrics, or metadata!</p>
        </div>
      ) : (
        <div className="messages-list">
          {messages.map((msg, idx) => (
            <div key={idx} className={`message ${msg.role} animate-entrance`} style={{ animationDelay: `${idx * 0.05}s` }}>
              <div className="message-avatar">
                {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
              </div>
              <div className="message-content">
                {msg.role === 'assistant' ? (
                  <ReactMarkdown>{msg.content}</ReactMarkdown>
                ) : (
                  <p>{msg.content}</p>
                )}
              </div>
            </div>
          ))}
          
          {isLoading && (
            <div className="message assistant loading animate-entrance">
              <div className="message-avatar">
                <Bot size={18} />
              </div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span><span></span><span></span>
                </div>
              </div>
            </div>
          )}
          
          {error && (
            <div className="error-banner">
              <p>{error}</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

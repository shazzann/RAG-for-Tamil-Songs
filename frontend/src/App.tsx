import { useState } from 'react';
import './App.css';
import { QueryInput } from './components/QueryInput';
import { ChatArea } from './components/ChatArea';
import type { Message } from './components/ChatArea';
import { SourceCard } from './components/SourceCard';
import { fetchChatResponse } from './api';
import type { Source } from './api';

function App() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [sources, setSources] = useState<Source[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSendQuery = async (query: string) => {
    // Optimistically add the user message
    setMessages(prev => [...prev, { role: 'user', content: query }]);
    setIsLoading(true);
    setError(null);
    setSources([]);

    try {
      const response = await fetchChatResponse(query);
      
      setMessages(prev => [...prev, { role: 'assistant', content: response.answer }]);
      if (response.sources && response.sources.length > 0) {
        setSources(response.sources);
      }
    } catch (err) {
      console.error(err);
      setError("Failed to reach the Tamil Song RAG backend. Is it running?");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1 className="text-gradient">Tamil Song Finder</h1>
        <p className="text-muted">Ask questions about songs, movies, or lyrics in Tanglish or Tamil.</p>
      </header>

      <main className="main-content">
        <section className="chat-section">
          <ChatArea 
            messages={messages} 
            isLoading={isLoading} 
            error={error} 
          />
          <QueryInput 
            onSend={handleSendQuery} 
            isLoading={isLoading} 
          />
        </section>

        {sources.length > 0 && (
          <aside className="sources-section glass-panel">
            <h3 style={{ marginBottom: '1rem', padding: '0 0.5rem' }}>Retrieved Context</h3>
            {sources.map((source, idx) => (
              <SourceCard key={idx} source={source} />
            ))}
          </aside>
        )}
      </main>
    </div>
  );
}

export default App;

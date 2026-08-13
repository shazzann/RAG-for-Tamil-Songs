import React from 'react';
import type { Source } from '../api';
import { Film, AlignLeft } from 'lucide-react';
import './SourceCard.css';

interface SourceCardProps {
  source: Source;
}

export const SourceCard: React.FC<SourceCardProps> = ({ source }) => {
  return (
    <div className="source-card glass-panel glass-panel-hover animate-entrance">
      <div className="source-card-header">
        <h4 className="source-title text-gradient">{source.title}</h4>
        <span className="source-badge">{source.source_type}</span>
      </div>
      
      <div className="source-card-body">
        {source.movie && (
          <div className="source-meta">
            <Film size={14} className="text-muted" />
            <span className="text-muted">{source.movie}</span>
          </div>
        )}
        
        {source.matched_text && (
          <div className="source-lyric">
            <AlignLeft size={14} className="text-muted lyric-icon" />
            <p className="lyric-text">"{source.matched_text}"</p>
          </div>
        )}
      </div>
      
      {source.score !== null && source.score !== undefined && (
        <div className="source-card-footer">
          <div className="score-bar-container">
            <div 
              className="score-bar-fill" 
              style={{ width: `${Math.min(100, Math.max(0, source.score * 100))}%` }}
            ></div>
          </div>
          <span className="score-text">Match: {(source.score * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
};

import { useState } from 'react';
import type { Severity, AIExplanation } from '../types';

interface CheckItemProps {
  name: string;
  passed: boolean;
  detail: string;
  severity: Severity;
  aiExplanation?: AIExplanation;
}

const TRUNCATE_LENGTH = 80;

function getStatusColor(severity: Severity): string {
  const map: Record<Severity, string> = {
    ok: 'var(--status-ok)',
    warning: 'var(--status-warning)',
    critical: 'var(--status-critical)',
  };
  return map[severity];
}

function getStatusLabel(severity: Severity): string {
  const map: Record<Severity, string> = {
    ok: 'OK',
    warning: 'WARNING',
    critical: 'CRITICAL',
  };
  return map[severity];
}

export default function CheckItem({ name, passed, detail, severity, aiExplanation }: CheckItemProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const color = getStatusColor(severity);
  const needsTruncation = detail.length > TRUNCATE_LENGTH;
  const displayDetail = (!isExpanded && needsTruncation)
    ? detail.slice(0, TRUNCATE_LENGTH) + '...'
    : detail;

  return (
    <div
      className="check-item"
      onClick={() => setIsExpanded(!isExpanded)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          setIsExpanded(!isExpanded);
        }
      }}
    >
      {/* Header row */}
      <div className="check-item-header">
        <div
          className="check-indicator"
          style={{ backgroundColor: color }}
        />
        <span className="check-name">{name}</span>
        <span className="check-status" style={{ color }}>
          {getStatusLabel(severity)}
        </span>
      </div>

      {/* Detail text */}
      <div className="check-detail">
        {displayDetail}
        {needsTruncation && !isExpanded && (
          <button
            className="check-show-toggle"
            onClick={(e) => {
              e.stopPropagation();
              setIsExpanded(true);
            }}
          >
            SHOW MORE →
          </button>
        )}
      </div>

      {/* Expanded content */}
      {isExpanded && aiExplanation && (
        <div className="check-expanded">
          {/* AI insight */}
          <div className="check-ai-section">
            <div className="check-ai-label">AI INSIGHT</div>
            <div className="check-ai-text">{aiExplanation.explanation}</div>
          </div>

          {/* Fix suggestion */}
          {aiExplanation.fix_suggestion && (
            <div className="check-fix-box">
              <div className="check-fix-label">HOW TO FIX</div>
              <div className="check-fix-text">{aiExplanation.fix_suggestion}</div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

import { useState, FormEvent } from 'react';

interface ScanFormProps {
  onSubmit: (url: string) => void;
  isLoading: boolean;
}

export default function ScanForm({ onSubmit, isLoading }: ScanFormProps) {
  const [url, setUrl] = useState('');
  const [error, setError] = useState('');

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError('');

    let normalizedUrl = url.trim();
    if (!normalizedUrl) {
      setError('Please enter a URL');
      return;
    }

    if (!normalizedUrl.startsWith('http://') && !normalizedUrl.startsWith('https://')) {
      normalizedUrl = `https://${normalizedUrl}`;
    }

    try {
      new URL(normalizedUrl);
    } catch {
      setError('Please enter a valid URL');
      return;
    }

    setUrl(normalizedUrl);
    onSubmit(normalizedUrl);
  }

  return (
    <form onSubmit={handleSubmit} style={{ width: '100%', maxWidth: 640 }}>
      <div className="scan-input-group">
        <input
          id="scan-url-input"
          type="text"
          value={url}
          onChange={(e) => {
            setUrl(e.target.value);
            if (error) setError('');
          }}
          placeholder="https://example.com"
          className="scan-input"
          disabled={isLoading}
          autoComplete="url"
          autoFocus
        />

        <button
          id="scan-submit-btn"
          type="submit"
          disabled={isLoading}
          className={`scan-btn ${isLoading ? 'scan-btn-scanning' : ''}`}
        >
          {isLoading ? (
            <>SCANNING<span className="blink-cursor">_</span></>
          ) : (
            'SCAN →'
          )}
        </button>
      </div>

      {error && (
        <p className="error-msg" style={{ marginTop: 12 }}>
          {error}
        </p>
      )}
    </form>
  );
}

import { useState, useEffect } from 'react';
import './App.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function SearchIcon() {
  return (
    <svg className="search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
    </svg>
  );
}

function ClockIcon() {
  return (
    <svg className="result-item-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10" /><path d="M12 6v6l4 2" />
    </svg>
  );
}

function ArrowIcon() {
  return (
    <svg className="result-item-arrow" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M7 17 17 7M7 7h10v10" />
    </svg>
  );
}

function App() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState([]);
  const [history, setHistory] = useState(
    () => JSON.parse(localStorage.getItem('searchHistory') || '[]')
  );

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }
    const t = setTimeout(async () => {
      try {
        const res = await fetch(`${API}/search?q=${encodeURIComponent(query)}`);
        setResults(await res.json());
      } catch {
        setResults([]);
      }
    }, 150);
    return () => clearTimeout(t);
  }, [query]);

  const saveToHistory = (title) => {
    setHistory(prev => {
      const next = [title, ...prev.filter(h => h !== title)].slice(0, 10);
      localStorage.setItem('searchHistory', JSON.stringify(next));
      return next;
    });
  };

  const showHistory = !query.trim() && history.length > 0;
  const showResults = query.trim() && results.length > 0;

  return (
    <div className="page">
      <div className="logo">
        <svg className="logo-icon" viewBox="0 0 40 40" fill="none">
          <circle cx="20" cy="20" r="20" fill="#4285f4" opacity="0.1"/>
          <circle cx="20" cy="20" r="10" fill="none" stroke="#4285f4" strokeWidth="2.5"/>
          <path d="M28 28l-4-4" stroke="#4285f4" strokeWidth="2.5" strokeLinecap="round"/>
        </svg>
        <div className="logo-text">
          <span>W</span><span>i</span><span>k</span><span>i</span><span>p</span><span>e</span><span>d</span><span>i</span><span>a</span>
        </div>
      </div>

      <div className="search-wrapper">
        <div className="search-box">
          <SearchIcon />
          <input
            type="text"
            value={query}
            onChange={e => setQuery(e.target.value)}
            placeholder="Search Wikipedia..."
            autoFocus
          />
          {query && (
            <button className="clear-btn" onClick={() => setQuery('')} aria-label="Clear">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M18 6 6 18M6 6l12 12"/>
              </svg>
            </button>
          )}
        </div>

        {showHistory && (
          <div className="dropdown">
            <p className="dropdown-label">Recent searches</p>
            {history.map(title => (
              <a
                key={title}
                href={`https://en.wikipedia.org/wiki/${title.replace(/ /g, '_')}`}
                target="_blank"
                rel="noopener noreferrer"
                className="result-item"
                onClick={() => saveToHistory(title)}
              >
                <ClockIcon />
                <span className="result-item-text">{title}</span>
                <ArrowIcon />
              </a>
            ))}
          </div>
        )}

        {showResults && (
          <div className="dropdown">
            {results.map(({ title, url }) => (
              <a
                key={title}
                href={url}
                target="_blank"
                rel="noopener noreferrer"
                className="result-item"
                onClick={() => saveToHistory(title)}
              >
                <SearchIcon />
                <span className="result-item-text">{title}</span>
                <ArrowIcon />
              </a>
            ))}
          </div>
        )}
      </div>

      {!query && !showHistory && (
        <p className="hint">Start typing to search 7 million Wikipedia titles</p>
      )}
    </div>
  );
}

export default App;

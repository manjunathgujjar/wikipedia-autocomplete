import { useState, useEffect } from 'react';
import './App.css';

const API = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
  const showResults = results.length > 0;

  return (
    <div className="container">
      <h1>Wikipedia Search</h1>
      <input
        type="text"
        value={query}
        onChange={e => setQuery(e.target.value)}
        placeholder="Search Wikipedia titles..."
        autoFocus
      />
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
              <span className="history-icon">&#x1F552;</span> {title}
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
              {title}
            </a>
          ))}
        </div>
      )}
    </div>
  );
}

export default App;

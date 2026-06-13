import { useState, useRef, useEffect } from 'react';
import { MagnifyingGlassIcon } from '@heroicons/react/24/outline';
import { useSearch } from '../../hooks/useSearch';
import { Link } from 'react-router-dom';

export default function SearchBar({ onFocus }) {
  const [query, setQuery] = useState('');
  const [open, setOpen] = useState(false);
  const inputRef = useRef();
  const { results, loading, performSearch } = useSearch();

  useEffect(() => {
    performSearch(query);
  }, [query, performSearch]);

  const handleFocus = () => {
    setOpen(true);
    if (onFocus) onFocus();
  };

  return (
    <div className="relative">
      <div className="relative">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-gray-400" />
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={handleFocus}
          onBlur={() => setTimeout(() => setOpen(false), 200)}
          placeholder="Search patients, isolates, reports... (⌘K)"
          className="pl-9 pr-4 py-2 w-80 rounded-full border-0 bg-gray-100/70 focus:bg-white focus:ring-2 focus:ring-primary-500/30 text-sm transition-all"
        />
      </div>
      {open && query && (
        <div className="absolute top-full left-0 mt-1 w-80 bg-white rounded-xl shadow-lg border p-2 z-50">
          {loading && <div className="p-2 text-sm text-gray-500">Searching...</div>}
          {!loading && results.length === 0 && <div className="p-2 text-sm text-gray-500">No results</div>}
          {results.map(r => (
            <Link key={r.url} to={r.url} className="block px-3 py-2 hover:bg-gray-100 rounded">
              <span className="text-xs text-gray-400">{r.type}</span>
              <p className="text-sm font-medium">{r.name}</p>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
import { useState, useCallback, useRef } from 'react';
import { debounce } from 'lodash';

export function useSearch() {
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);

  const performSearch = useCallback(
    debounce(async (term) => {
      if (!term.trim()) {
        setResults([]);
        return;
      }
      setLoading(true);
      try {
        // TODO: Replace with actual backend endpoint: /search?q=term
        // For now, mock results
        const mock = [
          { type: 'Pathogen', name: term.toUpperCase(), url: `/pathogen-explorer?pathogen=${term}` },
          { type: 'County', name: term, url: `/analytics?county=${term}` },
        ];
        setResults(mock);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }, 300),
    []
  );

  return { results, loading, performSearch };
}
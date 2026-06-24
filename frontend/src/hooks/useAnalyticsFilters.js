import { useState, useEffect, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';

export function useAnalyticsFilters() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [filters, setFilters] = useState({
    startDate: searchParams.get('start') || '',
    endDate: searchParams.get('end') || '',
    county: searchParams.get('county') || '',
    pathogen: searchParams.get('pathogen') || '',
    autoRefresh: searchParams.get('auto') === 'true' || false,
  });

  const updateFilters = useCallback((updates) => {
    setFilters(prev => ({ ...prev, ...updates }));
  }, []);

  useEffect(() => {
    const params = new URLSearchParams();
    if (filters.startDate) params.set('start', filters.startDate);
    if (filters.endDate) params.set('end', filters.endDate);
    if (filters.county) params.set('county', filters.county);
    if (filters.pathogen) params.set('pathogen', filters.pathogen);
    if (filters.autoRefresh) params.set('auto', 'true');
    setSearchParams(params, { replace: true });
  }, [filters, setSearchParams]);

  return { filters, updateFilters };
}
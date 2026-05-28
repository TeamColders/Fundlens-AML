import { useState, useEffect, useCallback } from 'react';
import { fetchGraph } from '../api/client';
import type { Subgraph } from '../api/types';

export function useGraphData(caseId: string | null) {
  const [graphData, setGraphData] = useState<Subgraph | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchGraph(caseId);
      setGraphData(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => { load(); }, [load]);

  return { graphData, loading, error, refetch: load };
}

import { useCallback, useEffect, useState } from 'react';
import { fetchMobileDashboard } from '../api/client';
import type { MobileDashboard } from '../api/types';

export function useMobileDashboard(caseId: string | null) {
  const [data, setData] = useState<MobileDashboard | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const dashboard = await fetchMobileDashboard(caseId);
      setData(dashboard);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => {
    load();
  }, [load]);

  return { data, loading, error, refetch: load };
}

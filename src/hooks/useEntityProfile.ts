import { useState, useEffect, useCallback } from 'react';
import { fetchEntity } from '../api/client';
import type { EntityProfile } from '../api/types';

export function useEntityProfile(accountId: string | null) {
  const [entity, setEntity] = useState<EntityProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!accountId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchEntity(accountId);
      setEntity(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [accountId]);

  useEffect(() => { load(); }, [load]);

  return { entity, loading, error, refetch: load };
}

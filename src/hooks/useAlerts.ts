import { useState, useEffect, useCallback } from 'react';
import { fetchAlerts, fetchAlert } from '../api/client';
import type { AlertListItem, AlertDetail, AlertsResponse } from '../api/types';

export function useAlerts(status?: string) {
  const [alerts, setAlerts] = useState<AlertListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data: AlertsResponse = await fetchAlerts({ status });
      setAlerts(data.alerts);
      setTotal(data.total);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [status]);

  useEffect(() => { load(); }, [load]);

  return { alerts, total, loading, error, refetch: load };
}

export function useAlertDetail(caseId: string | null) {
  const [detail, setDetail] = useState<AlertDetail | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await fetchAlert(caseId);
      setDetail(data);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => { load(); }, [load]);

  return { detail, loading, error, refetch: load };
}

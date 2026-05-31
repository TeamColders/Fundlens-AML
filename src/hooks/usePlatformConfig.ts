import { useCallback, useEffect, useState } from 'react';
import { fetchConfigAuditLog, fetchPlatformConfig } from '../api/client';
import type { AuditLogEntry, PlatformConfig } from '../api/types';

export function usePlatformConfig() {
  const [config, setConfig] = useState<PlatformConfig | null>(null);
  const [auditLog, setAuditLog] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [cfg, log] = await Promise.all([
        fetchPlatformConfig(),
        fetchConfigAuditLog(40),
      ]);
      setConfig(cfg);
      setAuditLog(log.entries);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return { config, auditLog, loading, error, refetch: load, setConfig };
}

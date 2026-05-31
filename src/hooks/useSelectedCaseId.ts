import { useEffect, useMemo, useState } from 'react';
import { useSearchParams } from 'react-router';
import { useAlerts } from './useAlerts';
import { getStoredCaseId, setStoredCaseId } from '../lib/selectedCase';

/**
 * Active investigation case: URL ?case= → session (from dashboard) → first alert from API.
 */
export function useSelectedCaseId(): {
  caseId: string;
  setCaseId: (id: string) => void;
  loading: boolean;
} {
  const [searchParams, setSearchParams] = useSearchParams();
  const caseFromUrl = searchParams.get('case');
  const { alerts, loading } = useAlerts();
  const [stored, setStored] = useState(() => getStoredCaseId() || '');

  const caseId = useMemo(() => {
    if (caseFromUrl) return caseFromUrl;
    if (stored) return stored;
    return alerts[0]?.case_id || '';
  }, [caseFromUrl, stored, alerts]);

  useEffect(() => {
    if (caseFromUrl) {
      setStoredCaseId(caseFromUrl);
      setStored(caseFromUrl);
    }
  }, [caseFromUrl]);

  useEffect(() => {
    if (!caseFromUrl && !stored && alerts[0]?.case_id) {
      setStoredCaseId(alerts[0].case_id);
      setStored(alerts[0].case_id);
    }
  }, [alerts, caseFromUrl, stored]);

  const setCaseId = (id: string) => {
    setStoredCaseId(id);
    setStored(id);
    setSearchParams({ case: id }, { replace: true });
  };

  return { caseId, setCaseId, loading };
}

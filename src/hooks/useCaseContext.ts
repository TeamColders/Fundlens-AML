import { useEffect } from 'react';
import type { AlertDetail } from '../api/types';
import { setStoredCaseId, setStoredOriginAccountId } from '../lib/selectedCase';

/** Persist case + origin account when alert detail loads (for breadcrumbs / dev nav). */
export function usePersistCaseContext(caseId: string | null, detail: AlertDetail | null) {
  useEffect(() => {
    if (!caseId) return;
    setStoredCaseId(caseId);
    if (!detail?.subgraph?.nodes) return;
    const origin = detail.subgraph.nodes.find((n) => n.is_origin);
    const fallback = detail.subgraph.nodes[0];
    const accountId = origin?.id || fallback?.id;
    if (accountId && accountId !== 'EXTERNAL') {
      setStoredOriginAccountId(accountId);
    }
  }, [caseId, detail]);
}

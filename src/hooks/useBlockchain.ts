import { useState, useEffect, useCallback } from 'react';
import { fetchBlockchain, verifyBlockchain } from '../api/client';
import type { BlockchainData, ChainVerification } from '../api/types';

export function useBlockchain(caseId: string | null) {
  const [chain, setChain] = useState<BlockchainData | null>(null);
  const [verification, setVerification] = useState<ChainVerification | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    if (!caseId) return;
    setLoading(true);
    setError(null);
    try {
      const [chainData, verifyData] = await Promise.all([
        fetchBlockchain(caseId),
        verifyBlockchain(caseId),
      ]);
      setChain(chainData);
      setVerification(verifyData);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [caseId]);

  useEffect(() => { load(); }, [load]);

  return { chain, verification, loading, error, refetch: load };
}

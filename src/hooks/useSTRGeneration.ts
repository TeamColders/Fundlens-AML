import { useState, useCallback, useRef } from 'react';
import { streamSTRGeneration } from '../api/client';
import type { STRProgressEvent, STRReport } from '../api/types';

export function useSTRGeneration() {
  const [stage, setStage] = useState<string | null>(null);
  const [message, setMessage] = useState('');
  const [progress, setProgress] = useState(0);
  const [report, setReport] = useState<STRReport | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState(false);
  const cancelRef = useRef<(() => void) | null>(null);

  const generate = useCallback((caseId: string) => {
    setGenerating(true);
    setError(null);
    setReport(null);
    setStage(null);
    setProgress(0);

    cancelRef.current = streamSTRGeneration(
      caseId,
      (event: STRProgressEvent) => {
        setStage(event.stage);
        setMessage(event.message);
        setProgress(event.progress);
        if (event.stage === 'complete' && event.report) {
          setReport(event.report);
          setGenerating(false);
        }
        if (event.stage === 'error') {
          setError(event.error || event.message);
          setGenerating(false);
        }
      },
      (err: Error) => {
        setError(err.message);
        setGenerating(false);
      },
    );
  }, []);

  const cancel = useCallback(() => {
    cancelRef.current?.();
    setGenerating(false);
  }, []);

  return { stage, message, progress, report, error, generating, generate, cancel };
}

import { Loader2, Send } from 'lucide-react';
import { useCallback, useMemo, useRef, useState } from 'react';
import { queryGraph } from '../../api/client';
import type { NLQueryResult } from '../../api/types';
import { useAlertDetail } from '../../hooks/useAlerts';
import { useSelectedCaseId } from '../../hooks/useSelectedCaseId';
import NLQueryResults from '../components/NLQueryResults';

type ChatMessage =
  | { id: string; role: 'user'; text: string }
  | { id: string; role: 'assistant'; result: NLQueryResult; showCypher: boolean }
  | { id: string; role: 'error'; text: string };

function newId() {
  return `${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
}

export default function NLQuery() {
  const [query, setQuery] = useState('');
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { caseId } = useSelectedCaseId();
  const { detail } = useAlertDetail(caseId || null);

  const originAccountId = useMemo(
    () => detail?.subgraph?.nodes?.find((n) => n.is_origin)?.id,
    [detail],
  );

  const suggestedQueries = useMemo(
    () => [
      originAccountId
        ? `Show me all accounts connected to ${originAccountId}`
        : 'Show accounts in the active investigation case',
      caseId ? `List all accounts in case ${caseId}` : 'Which accounts act as transaction hubs?',
      'Which accounts received transfers from dormant accounts?',
      'Find structuring patterns above ₹10L',
      caseId
        ? `Explain why case ${caseId} was flagged and what to investigate next`
        : 'Explain the typology pattern in the highest-risk open case',
    ],
    [originAccountId, caseId],
  );

  const scrollToBottom = useCallback(() => {
    requestAnimationFrame(() => {
      scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    });
  }, []);

  const sendQuery = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isTyping) return;

      setQuery('');
      setMessages((prev) => [...prev, { id: newId(), role: 'user', text: trimmed }]);
      setIsTyping(true);
      scrollToBottom();

      try {
        const data = await queryGraph(trimmed, caseId);
        setMessages((prev) => [
          ...prev,
          { id: newId(), role: 'assistant', result: data, showCypher: false },
        ]);
      } catch (e) {
        setMessages((prev) => [
          ...prev,
          { id: newId(), role: 'error', text: (e as Error).message || 'Query failed' },
        ]);
      } finally {
        setIsTyping(false);
        scrollToBottom();
      }
    },
    [caseId, isTyping, scrollToBottom],
  );

  const toggleCypher = (messageId: string) => {
    setMessages((prev) =>
      prev.map((m) =>
        m.role === 'assistant' && m.id === messageId ? { ...m, showCypher: !m.showCypher } : m,
      ),
    );
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      <div className="p-6 border-b border-gray-200 shrink-0">
        <h1 className="text-gray-900 text-2xl font-bold mb-2" style={{ fontFamily: 'Syne' }}>
          Natural Language Query
        </h1>
        <p className="text-gray-700 text-sm">
          Ask about accounts, fund flows, and typologies — answers come from your case database
          {caseId ? (
            <>
              {' '}
              (active case <span style={{ fontFamily: 'DM Mono' }}>{caseId}</span>)
            </>
          ) : null}
        </p>
      </div>

      <div ref={scrollRef} className="flex-1 overflow-auto p-6 space-y-6 pb-4">
        {messages.length === 0 && (
          <div className="max-w-xl mx-auto text-center py-16">
            <p className="text-gray-600 text-sm mb-2">No messages yet</p>
            <p className="text-gray-500 text-xs">
              Try a suggested query below or ask in plain English. When Neo4j is available, queries
              run as Cypher; otherwise FundLens uses the SQL investigation store.
            </p>
          </div>
        )}

        {messages.map((msg) => {
          if (msg.role === 'user') {
            return (
              <div key={msg.id} className="flex justify-end">
                <div className="bg-[#E31E24] rounded-2xl rounded-tr-sm px-5 py-3 max-w-2xl">
                  <p className="text-white text-sm font-medium">{msg.text}</p>
                </div>
              </div>
            );
          }

          if (msg.role === 'error') {
            return (
              <div key={msg.id} className="flex justify-start">
                <div className="max-w-3xl bg-red-50 border border-red-200 rounded-2xl p-4 text-sm text-red-800">
                  {msg.text}
                </div>
              </div>
            );
          }

          const { result } = msg;
          return (
            <div key={msg.id} className="flex justify-start">
              <div className="max-w-3xl w-full">
                <div className="flex items-center gap-2 mb-3 flex-wrap">
                  <div className="w-8 h-8 rounded-full bg-white border border-[#E31E24] flex items-center justify-center text-[#E31E24] text-xs font-bold">
                    FL
                  </div>
                  <span className="text-xs text-gray-700">FundLens AI</span>
                  <span className="px-2 py-1 bg-[#3B82F6] text-white rounded text-[10px] font-semibold">
                    {result.source === 'neo4j'
                      ? 'Neo4j'
                      : result.source === 'gemini'
                        ? 'Gemini'
                        : result.source === 'gemini+sql'
                          ? 'SQL + Gemini'
                          : result.source === 'neo4j+gemini'
                            ? 'Neo4j + Gemini'
                            : 'SQL'}
                  </span>
                  {result.model_used && result.model_used !== 'fallback-template' && (
                    <span className="text-[10px] text-gray-500">{result.model_used}</span>
                  )}
                  <span className="text-xs text-gray-400">{result.execution_ms}ms</span>
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm p-5">
                  <NLQueryResults
                    result={result}
                    showCypher={msg.showCypher}
                    onToggleCypher={() => toggleCypher(msg.id)}
                    caseId={caseId}
                  />
                </div>
              </div>
            </div>
          );
        })}

        {isTyping && (
          <div className="flex justify-start">
            <div className="flex items-center gap-2 text-gray-500 text-sm">
              <Loader2 className="w-4 h-4 animate-spin text-[#E31E24]" />
              Running query…
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-gray-200 bg-white p-6 shrink-0">
        <div className="mb-4 flex flex-wrap gap-2">
          {suggestedQueries.map((suggested) => (
            <button
              key={suggested}
              type="button"
              onClick={() => sendQuery(suggested)}
              disabled={isTyping}
              className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-full text-xs text-gray-700 hover:border-[#E31E24] hover:text-gray-900 transition-colors disabled:opacity-50"
            >
              {suggested}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-50 border border-gray-200 rounded-full px-5 py-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  sendQuery(query);
                }
              }}
              placeholder="Ask about accounts, entities, or transaction patterns…"
              disabled={isTyping}
              className="w-full bg-transparent text-gray-900 text-[15px] placeholder:text-gray-400 outline-none disabled:opacity-60"
            />
          </div>
          <button
            type="button"
            onClick={() => sendQuery(query)}
            disabled={isTyping || !query.trim()}
            className="w-10 h-10 bg-[#E31E24] rounded-full flex items-center justify-center hover:bg-[#d4183d] transition-colors disabled:opacity-50"
            aria-label="Send query"
          >
            {isTyping ? (
              <Loader2 className="w-5 h-5 text-white animate-spin" />
            ) : (
              <Send className="w-5 h-5 text-white" />
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

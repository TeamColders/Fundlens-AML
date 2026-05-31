import { Mic, Send, ChevronDown, ExternalLink, Loader2 } from 'lucide-react';
import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router';
import { api } from '../../services/api';

interface Message {
  role: 'user' | 'assistant';
  text: string;
  loading?: boolean;
}

const SUGGESTED = [
  'Show me all accounts connected to ACC-0041',
  'Which accounts had sudden activity after 6+ months of dormancy?',
  'Find all structuring patterns above ₹10L this week',
];

export default function NLQuery() {
  const navigate = useNavigate();
  const [query, setQuery]       = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [showCypher, setShowCypher] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendQuery = async (text: string) => {
    if (!text.trim()) return;
    const userMsg: Message = { role: 'user', text };
    const loadingMsg: Message = { role: 'assistant', text: '', loading: true };
    setMessages(prev => [...prev, userMsg, loadingMsg]);
    setQuery('');

    try {
      const result = await api.runQuery(text);
      const reply = typeof result.message === 'string'
        ? result.message
        : JSON.stringify(result, null, 2);
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', text: reply },
      ]);
    } catch {
      setMessages(prev => [
        ...prev.slice(0, -1),
        { role: 'assistant', text: 'Query failed — backend may be unavailable.' },
      ]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') sendQuery(query);
  };

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-gray-900 text-2xl font-bold mb-2" style={{ fontFamily: 'Syne' }}>
          Natural Language Query
        </h1>
        <p className="text-gray-700 text-sm">Ask anything about accounts, entities, or transaction patterns</p>
      </div>

      {/* Conversation Area */}
      <div className="flex-1 overflow-auto p-6 space-y-6 pb-32">

        {/* Static demo conversation shown when no messages yet */}
        {messages.length === 0 && (
          <>
            {/* Demo query 1 */}
            <div className="flex justify-end">
              <div className="bg-[#E31E24] rounded-2xl rounded-tr-sm px-5 py-3 max-w-2xl">
                <p className="text-white text-sm font-medium">
                  Show me all accounts that received transfers from dormant accounts this week
                </p>
              </div>
            </div>
            <div className="flex justify-start">
              <div className="max-w-3xl">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-full bg-white border border-[#E31E24] flex items-center justify-center text-[#E31E24] text-xs font-bold">FL</div>
                  <span className="text-xs text-gray-700">FundLens AI</span>
                  <span className="px-2 py-1 bg-[#3B82F6] text-white rounded text-[10px] font-semibold">GNN + Neo4j</span>
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm p-5">
                  <p className="text-gray-900 text-sm mb-4">Found 4 accounts that received transfers from dormant accounts in the last 7 days:</p>
                  <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden mb-4">
                    <table className="w-full text-xs" style={{ fontFamily: 'DM Mono' }}>
                      <thead>
                        <tr className="bg-white text-gray-700">
                          <th className="text-left py-3 px-4">Account ID</th>
                          <th className="text-right py-3 px-4">Amount Received</th>
                          <th className="text-right py-3 px-4">Source Dormancy</th>
                          <th className="text-right py-3 px-4">Risk Score</th>
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          { id: 'ACC-0041', amt: '₹47,23,000', dormancy: '26 months', risk: 87, riskColor: 'text-[#E31E24]' },
                          { id: 'ACC-0203', amt: '₹18,92,000', dormancy: '14 months', risk: 68, riskColor: 'text-[#F59E0B]' },
                          { id: 'ACC-0455', amt: '₹9,45,000',  dormancy: '8 months',  risk: 54, riskColor: 'text-[#F59E0B]' },
                          { id: 'ACC-0821', amt: '₹6,12,000',  dormancy: '9 months',  risk: 42, riskColor: 'text-[#E31E24]' },
                        ].map((row, i) => (
                          <tr key={i} className="border-t border-gray-200">
                            <td className="py-3 px-4 text-gray-900">{row.id}</td>
                            <td className={`py-3 px-4 text-right font-bold ${row.riskColor}`}>{row.amt}</td>
                            <td className="py-3 px-4 text-right text-[#F59E0B]">{row.dormancy}</td>
                            <td className={`py-3 px-4 text-right font-bold ${row.riskColor}`}>{row.risk}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="border-t border-gray-200 pt-4">
                    <button onClick={() => setShowCypher(!showCypher)} className="flex items-center gap-2 text-xs text-gray-700 hover:text-gray-900 transition-colors">
                      <ChevronDown className={`w-4 h-4 transition-transform ${showCypher ? 'rotate-180' : ''}`} />
                      Cypher query used:
                    </button>
                    {showCypher && (
                      <div className="mt-3 bg-gray-50 border border-gray-200 rounded p-3">
                        <pre className="text-xs text-[#E31E24] overflow-x-auto" style={{ fontFamily: 'DM Mono' }}>
{`MATCH (source:Account)-[t:TRANSFER]->(target:Account)
WHERE source.lastActive < date() - duration({months: 6})
  AND t.timestamp > date() - duration({days: 7})
RETURN target.id, sum(t.amount) as totalReceived,
       source.dormancyMonths, target.riskScore
ORDER BY target.riskScore DESC`}
                        </pre>
                      </div>
                    )}
                  </div>
                  <button onClick={() => navigate('/graph')} className="mt-4 text-[#E31E24] hover:underline text-xs flex items-center gap-1">
                    <ExternalLink className="w-3 h-3" />
                    Open in graph view →
                  </button>
                </div>
              </div>
            </div>
          </>
        )}

        {/* Live messages */}
        {messages.map((msg, idx) => (
          <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            {msg.role === 'user' ? (
              <div className="bg-[#E31E24] rounded-2xl rounded-tr-sm px-5 py-3 max-w-2xl">
                <p className="text-white text-sm font-medium">{msg.text}</p>
              </div>
            ) : (
              <div className="max-w-3xl">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-full bg-white border border-[#E31E24] flex items-center justify-center text-[#E31E24] text-xs font-bold">FL</div>
                  <span className="text-xs text-gray-700">FundLens AI</span>
                </div>
                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm p-5">
                  {msg.loading ? (
                    <div className="flex items-center gap-2 text-gray-400 text-sm">
                      <Loader2 className="w-4 h-4 animate-spin" />
                      Processing query…
                    </div>
                  ) : (
                    <p className="text-gray-900 text-sm whitespace-pre-wrap">{msg.text}</p>
                  )}
                </div>
              </div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input Bar */}
      <div className="border-t border-gray-200 bg-white p-6">
        <div className="mb-4 flex flex-wrap gap-2">
          {SUGGESTED.map((s, idx) => (
            <button
              key={idx}
              onClick={() => setQuery(s)}
              className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-full text-xs text-gray-700 hover:border-[#E31E24] hover:text-gray-900 transition-colors"
            >
              {s}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-50 border border-gray-200 rounded-full px-5 py-4 flex items-center gap-3">
            <input
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask anything about any account, entity, or transaction pattern..."
              className="flex-1 bg-transparent text-gray-900 text-[15px] placeholder-gray-400 outline-none"
            />
            <button className="text-gray-700 hover:text-gray-900 transition-colors">
              <Mic className="w-5 h-5" />
            </button>
          </div>
          <button
            onClick={() => sendQuery(query)}
            className="w-[40px] h-[40px] bg-[#E31E24] rounded-full flex items-center justify-center hover:bg-[#d4183d] transition-colors"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}

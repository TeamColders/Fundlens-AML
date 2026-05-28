import { Mic, Send, ChevronDown, ExternalLink, Loader2 } from 'lucide-react';
import { useState } from 'react';
import { queryGraph } from '../../api/client';
import type { NLQueryResult } from '../../api/types';

export default function NLQuery() {
  const [query, setQuery] = useState('');
  const [showCypher, setShowCypher] = useState(false);
  const [isTyping, setIsTyping] = useState(false);
  const [result, setResult] = useState<NLQueryResult | null>(null);

  const handleQuery = async () => {
    if (!query.trim()) return;
    setIsTyping(true);
    setResult(null);
    try {
      const data = await queryGraph(query);
      setResult(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsTyping(false);
    }
  };

  const onKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleQuery();
    }
  };

  const suggestedQueries = [
    'Show me all accounts connected to ACC-0041',
    'Which accounts had sudden activity after 6+ months of dormancy?',
    'Find all structuring patterns above ₹10L this week',
  ];

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-gray-200">
        <h1 className="text-gray-900 text-2xl font-bold mb-2" style={{ fontFamily: 'Syne' }}>
          Natural Language Query
        </h1>
        <p className="text-gray-700 text-sm">
          Ask anything about accounts, entities, or transaction patterns
        </p>
      </div>

      {/* Conversation Area */}
      <div className="flex-1 overflow-auto p-6 space-y-6 pb-32">
        {/* Query 1 */}
        <div className="flex justify-end">
          <div className="bg-[#E31E24] rounded-2xl rounded-tr-sm px-5 py-3 max-w-2xl">
            <p className="text-white text-sm font-medium">
              Show me all accounts that received transfers from dormant accounts this week
            </p>
          </div>
        </div>

        {/* Response 1 */}
        <div className="flex justify-start">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-white border border-[#E31E24] flex items-center justify-center text-[#E31E24] text-xs font-bold">
                FL
              </div>
              <span className="text-xs text-gray-700">FundLens AI</span>
              <span className="px-2 py-1 bg-[#3B82F6] text-white rounded text-[10px] font-semibold">
                GNN + Neo4j
              </span>
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm p-5">
              <div className="mb-4">
                <p className="text-gray-900 text-sm mb-4">
                  Found 4 accounts that received transfers from dormant accounts in the last 7 days:
                </p>

                {/* Results table */}
                <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-hidden">
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
                      <tr className="border-t border-gray-200">
                        <td className="py-3 px-4 text-gray-900">ACC-0041</td>
                        <td className="py-3 px-4 text-right text-[#E31E24] font-bold">₹47,23,000</td>
                        <td className="py-3 px-4 text-right text-[#F59E0B]">26 months</td>
                        <td className="py-3 px-4 text-right text-[#E31E24] font-bold">87</td>
                      </tr>
                      <tr className="border-t border-gray-200">
                        <td className="py-3 px-4 text-gray-900">ACC-0203</td>
                        <td className="py-3 px-4 text-right text-[#F59E0B] font-bold">₹18,92,000</td>
                        <td className="py-3 px-4 text-right text-[#F59E0B]">14 months</td>
                        <td className="py-3 px-4 text-right text-[#F59E0B] font-bold">68</td>
                      </tr>
                      <tr className="border-t border-gray-200">
                        <td className="py-3 px-4 text-gray-900">ACC-0455</td>
                        <td className="py-3 px-4 text-right text-gray-900 font-bold">₹9,45,000</td>
                        <td className="py-3 px-4 text-right text-gray-700">8 months</td>
                        <td className="py-3 px-4 text-right text-[#F59E0B] font-bold">54</td>
                      </tr>
                      <tr className="border-t border-gray-200">
                        <td className="py-3 px-4 text-gray-900">ACC-0821</td>
                        <td className="py-3 px-4 text-right text-gray-900 font-bold">₹6,12,000</td>
                        <td className="py-3 px-4 text-right text-gray-700">9 months</td>
                        <td className="py-3 px-4 text-right text-[#E31E24] font-bold">42</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Expandable Cypher query */}
              <div className="border-t border-gray-200 pt-4">
                <button
                  onClick={() => setShowCypher(!showCypher)}
                  className="flex items-center gap-2 text-xs text-gray-700 hover:text-gray-900 transition-colors"
                >
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

              <button className="mt-4 text-[#E31E24] hover:underline text-xs flex items-center gap-1">
                <ExternalLink className="w-3 h-3" />
                Open in graph view →
              </button>
            </div>
          </div>
        </div>

        {/* Query 2 */}
        <div className="flex justify-end">
          <div className="bg-[#E31E24] rounded-2xl rounded-tr-sm px-5 py-3 max-w-2xl">
            <p className="text-white text-sm font-medium">
              What is the risk profile of entity RAJESH KUMAR PAN XXXXX1234X?
            </p>
          </div>
        </div>

        {/* Response 2 */}
        <div className="flex justify-start">
          <div className="max-w-3xl">
            <div className="flex items-center gap-2 mb-3">
              <div className="w-8 h-8 rounded-full bg-white border border-[#E31E24] flex items-center justify-center text-[#E31E24] text-xs font-bold">
                FL
              </div>
              <span className="text-xs text-gray-700">FundLens AI</span>
              <span className="px-2 py-1 bg-[#3B82F6] text-white rounded text-[10px] font-semibold">
                GNN + Neo4j
              </span>
            </div>

            <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm p-5">
              {/* Entity card */}
              <div className="bg-gray-50 border-l-4 border-[#E31E24] rounded-lg p-4 mb-4">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-gray-900 font-bold text-lg mb-1" style={{ fontFamily: 'Syne' }}>
                      Rajesh Kumar
                    </h3>
                    <div className="text-gray-700 text-xs" style={{ fontFamily: 'DM Mono' }}>
                      PAN: XXXXX1234X
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-xs text-gray-700 mb-1">Risk Score</div>
                    <div className="text-[#E31E24] text-3xl font-bold" style={{ fontFamily: 'Syne' }}>
                      87%
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4 pt-3 border-t border-gray-200">
                  <div>
                    <div className="text-xs text-gray-700 mb-1">Accounts</div>
                    <div className="text-gray-900 font-bold">2</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-700 mb-1">Typologies detected</div>
                    <div className="text-[#E31E24] font-bold">3</div>
                  </div>
                  <div>
                    <div className="text-xs text-gray-700 mb-1">Network size</div>
                    <div className="text-gray-900 font-bold">14</div>
                  </div>
                </div>

                <div className="mt-3 pt-3 border-t border-gray-200">
                  <div className="text-xs text-gray-700 mb-2">Active typologies:</div>
                  <div className="flex flex-wrap gap-2">
                    <span className="px-2 py-1 bg-[#E31E24] text-white rounded text-xs font-semibold">
                      Round-trip Layering
                    </span>
                    <span className="px-2 py-1 bg-[#F59E0B] text-white rounded text-xs font-semibold">
                      Dormant Activation
                    </span>
                    <span className="px-2 py-1 bg-[#F59E0B] text-white rounded text-xs font-semibold">
                      Structuring
                    </span>
                  </div>
                </div>
              </div>

              <button className="text-[#E31E24] hover:underline text-xs flex items-center gap-1">
                <ExternalLink className="w-3 h-3" />
                View full entity profile →
              </button>
            </div>
          </div>
        </div>

        {/* Live Query Results */}
        {result && (
          <>
            <div className="flex justify-end">
              <div className="bg-[#E31E24] rounded-2xl rounded-tr-sm px-5 py-3 max-w-2xl">
                <p className="text-white text-sm font-medium">{result.query}</p>
              </div>
            </div>

            <div className="flex justify-start">
              <div className="max-w-3xl">
                <div className="flex items-center gap-2 mb-3">
                  <div className="w-8 h-8 rounded-full bg-white border border-[#E31E24] flex items-center justify-center text-[#E31E24] text-xs font-bold">
                    FL
                  </div>
                  <span className="text-xs text-gray-700">FundLens AI</span>
                  <span className="px-2 py-1 bg-[#3B82F6] text-white rounded text-[10px] font-semibold">
                    GNN + LLM
                  </span>
                  <span className="text-xs text-gray-400">({result.execution_ms}ms)</span>
                </div>

                <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm p-5">
                  <p className="text-gray-900 text-sm mb-4">
                    Found {result.result_count} results:
                  </p>

                  <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-x-auto mb-4">
                    <pre className="p-4 text-xs text-gray-800" style={{ fontFamily: 'DM Mono' }}>
                      {JSON.stringify(result.results, null, 2)}
                    </pre>
                  </div>

                  <div className="border-t border-gray-200 pt-4">
                    <button
                      onClick={() => setShowCypher(!showCypher)}
                      className="flex items-center gap-2 text-xs text-gray-700 hover:text-gray-900 transition-colors"
                    >
                      <ChevronDown className={`w-4 h-4 transition-transform ${showCypher ? 'rotate-180' : ''}`} />
                      Cypher query used:
                    </button>
                    {showCypher && (
                      <div className="mt-3 bg-gray-50 border border-gray-200 rounded p-3">
                        <pre className="text-xs text-[#E31E24] overflow-x-auto" style={{ fontFamily: 'DM Mono' }}>
                          {result.cypher}
                        </pre>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </>
        )}

        {isTyping && (
          <div className="flex justify-start">
            <div className="max-w-3xl">
              <div className="flex items-center gap-2 mb-3">
                <div className="w-8 h-8 rounded-full bg-white border border-[#E31E24] flex items-center justify-center text-[#E31E24] text-xs font-bold">FL</div>
                <span className="text-xs text-gray-700">FundLens AI typing...</span>
              </div>
              <div className="bg-white border border-gray-200 rounded-2xl rounded-tl-sm p-5 w-24">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 rounded-full bg-[#E31E24] animate-pulse" />
                  <div className="w-2 h-2 rounded-full bg-[#E31E24] animate-pulse" style={{ animationDelay: '0.2s' }} />
                  <div className="w-2 h-2 rounded-full bg-[#E31E24] animate-pulse" style={{ animationDelay: '0.4s' }} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Query Input Bar - Fixed at bottom */}
      <div className="border-t border-gray-200 bg-white p-6">
        {/* Suggested queries */}
        <div className="mb-4 flex flex-wrap gap-2">
          {suggestedQueries.map((suggested, idx) => (
            <button
              key={idx}
              onClick={() => setQuery(suggested)}
              className="px-3 py-2 bg-gray-50 border border-gray-200 rounded-full text-xs text-gray-700 hover:border-[#E31E24] hover:text-gray-900 transition-colors"
            >
              {suggested}
            </button>
          ))}
        </div>

        {/* Input bar */}
        <div className="flex items-center gap-3">
          <div className="flex-1 bg-gray-50 border border-gray-200 rounded-full px-5 py-4 flex items-center gap-3">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="Ask anything about any account, entity, or transaction pattern..."
              className="flex-1 bg-transparent text-gray-900 text-[15px] placeholder-[#E31E24] placeholder-opacity-40 outline-none"
            />
            <button className="text-gray-700 hover:text-gray-900 transition-colors">
              <Mic className="w-5 h-5" />
            </button>
          </div>
          <button 
            onClick={handleQuery}
            className="w-[40px] h-[40px] bg-[#E31E24] rounded-full flex items-center justify-center hover:bg-[#d4183d] transition-colors"
          >
            <Send className="w-5 h-5 text-white" />
          </button>
        </div>
      </div>
    </div>
  );
}

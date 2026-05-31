import { ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router';
import type { EntityProfile, NLQueryResult } from '../../api/types';
import { formatAmount } from '../../lib/subgraphLayout';
import { pathWithCase, setStoredCaseId } from '../../lib/selectedCase';

interface NLQueryResultsProps {
  result: NLQueryResult;
  showCypher: boolean;
  onToggleCypher: () => void;
  caseId?: string;
}

function ResultTable({ rows }: { rows: Record<string, unknown>[] }) {
  if (!rows.length) {
    return <p className="text-xs text-gray-500">No rows returned.</p>;
  }

  const columns = Object.keys(rows[0]);
  const navigate = useNavigate();

  const formatCell = (key: string, value: unknown) => {
    if (value == null) return '—';
    if (key.includes('amount') && typeof value === 'number') {
      return formatAmount(value);
    }
    if (typeof value === 'number' && key.includes('score')) {
      return String(Math.round(value));
    }
    const text = String(value);
    if (key === 'account_id' && text.startsWith('ACC-')) {
      return (
        <button
          type="button"
          onClick={() => navigate(`/entity/${text}`)}
          className="text-[#E31E24] hover:underline font-medium"
        >
          {text}
        </button>
      );
    }
    if (key === 'case_id' && text.startsWith('CASE-')) {
      return (
        <button
          type="button"
          onClick={() => {
            setStoredCaseId(text);
            navigate('/');
          }}
          className="text-[#E31E24] hover:underline font-medium"
        >
          {text}
        </button>
      );
    }
    return text;
  };

  return (
    <div className="bg-gray-50 border border-gray-200 rounded-lg overflow-x-auto">
      <table className="w-full text-xs" style={{ fontFamily: 'DM Mono' }}>
        <thead>
          <tr className="bg-white text-gray-700">
            {columns.map((col) => (
              <th key={col} className="text-left py-3 px-4 whitespace-nowrap">
                {col.replace(/_/g, ' ')}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, idx) => (
            <tr key={idx} className="border-t border-gray-200">
              {columns.map((col) => (
                <td key={col} className="py-3 px-4 text-gray-900">
                  {formatCell(col, row[col])}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function EntityCard({ entity }: { entity: EntityProfile }) {
  const navigate = useNavigate();

  return (
    <div className="bg-gray-50 border-l-4 border-[#E31E24] rounded-lg p-4">
      <div className="flex items-start justify-between mb-3">
        <div>
          <h3 className="text-gray-900 font-bold text-lg mb-1" style={{ fontFamily: 'Syne' }}>
            {entity.owner_name}
          </h3>
          <div className="text-gray-700 text-xs" style={{ fontFamily: 'DM Mono' }}>
            {entity.account_id} · {entity.home_branch}
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-700 mb-1">Risk score</div>
          <div className="text-[#E31E24] text-3xl font-bold" style={{ fontFamily: 'Syne' }}>
            {entity.risk_score}
          </div>
        </div>
      </div>
      <div className="grid grid-cols-3 gap-4 pt-3 border-t border-gray-200 text-sm">
        <div>
          <div className="text-xs text-gray-600">Type</div>
          <div className="font-medium">{entity.account_type}</div>
        </div>
        <div>
          <div className="text-xs text-gray-600">Counterparties</div>
          <div className="font-medium">{entity.metrics?.counterparties_30d ?? '—'}</div>
        </div>
        <div>
          <div className="text-xs text-gray-600">Flow volume</div>
          <div className="font-medium">{formatAmount(entity.metrics?.current_month_volume ?? 0)}</div>
        </div>
      </div>
      <button
        type="button"
        onClick={() => navigate(`/entity/${entity.account_id}`)}
        className="mt-4 text-[#E31E24] hover:underline text-xs flex items-center gap-1"
      >
        <ExternalLink className="w-3 h-3" />
        View full entity profile
      </button>
    </div>
  );
}

export default function NLQueryResults({
  result,
  showCypher,
  onToggleCypher,
  caseId,
}: NLQueryResultsProps) {
  const navigate = useNavigate();
  const sourceLabel =
    result.source === 'neo4j'
      ? 'Neo4j'
      : result.source === 'gemini'
        ? 'Gemini'
        : result.source === 'gemini+sql'
          ? 'SQL + Gemini'
          : result.source === 'neo4j+gemini'
            ? 'Neo4j + Gemini'
            : result.source === 'sql'
              ? 'SQL + rules'
              : 'FundLens';

  return (
    <div>
      {result.fallback_reason && (
        <p className="text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded px-3 py-2 mb-3">
          {result.fallback_reason}
        </p>
      )}
      <p className="text-gray-900 text-sm mb-4">
        {result.summary || `Found ${result.result_count} result(s).`}
      </p>
      {result.narrative && (
        <div className="text-sm text-gray-800 leading-relaxed whitespace-pre-wrap mb-4 border-l-2 border-[#E31E24] pl-4">
          {result.narrative}
        </div>
      )}

      {result.display_type === 'entity' && result.entity ? (
        <EntityCard entity={result.entity} />
      ) : (
        <ResultTable rows={result.results} />
      )}

      <div className="border-t border-gray-200 pt-4 mt-4 flex flex-wrap items-center gap-4">
        <button
          type="button"
          onClick={onToggleCypher}
          className="text-xs text-gray-700 hover:text-gray-900"
        >
          {showCypher ? 'Hide' : 'Show'} Cypher ({sourceLabel})
        </button>
        {caseId && (
          <button
            type="button"
            onClick={() => navigate(pathWithCase('/graph', caseId))}
            className="text-[#E31E24] hover:underline text-xs flex items-center gap-1"
          >
            <ExternalLink className="w-3 h-3" />
            Open active case graph
          </button>
        )}
      </div>

      {showCypher && result.cypher && (
        <pre
          className="mt-3 bg-gray-50 border border-gray-200 rounded p-3 text-xs text-[#E31E24] overflow-x-auto"
          style={{ fontFamily: 'DM Mono' }}
        >
          {result.cypher}
        </pre>
      )}
    </div>
  );
}

import React from 'react';
import { History, CheckCircle2, AlertCircle } from 'lucide-react';

function formatRecencyWindow(minutes) {
  if (!minutes) return 'N/A';
  if (minutes < 60) return `${minutes}m`;
  if (minutes === 60) return '1h';
  if (minutes < 1440) return `${Math.round(minutes / 60)}h`;
  if (minutes === 1440) return '24h (1d)';
  if (minutes === 4320) return '3d';
  if (minutes === 10080) return '1w (7d)';
  if (minutes === 20160) return '2w (14d)';
  if (minutes === 43200) return '1mth (30d)';
  if (minutes === 129600) return '3mth (90d)';
  if (minutes === 259200) return '6mth (180d)';
  if (minutes === 525600) return '1yr (365d)';
  const days = Math.round(minutes / 1440);
  return `${days}d`;
}

export default function CollectionHistory({ history }) {
  if (!history || history.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-mongo-border p-8 text-center text-slate-500">
        <History className="w-8 h-8 mx-auto text-slate-300 mb-2" />
        <p className="font-mono text-xs">No execution history recorded in log.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden">
      <div className="p-5 border-b border-slate-200 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <History className="w-5 h-5 text-linkedin-blue" />
          <h3 className="font-bold text-slate-900 text-base font-sans">Pipeline Execution Audit Log</h3>
        </div>
        <span className="text-xs font-mono text-slate-500">{history.length} Requests Recorded</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full text-left border-collapse text-xs font-mono">
          <thead>
            <tr className="bg-[#F3F8FD] border-b border-slate-200 font-bold text-slate-600 uppercase tracking-wider font-sans">
              <th className="py-3 px-4">Request ID</th>
              <th className="py-3 px-4">Entities / Query</th>
              <th className="py-3 px-4">Scope</th>
              <th className="py-3 px-4">Window</th>
              <th className="py-3 px-4">Status</th>
              <th className="py-3 px-4">Metrics</th>
              <th className="py-3 px-4">Executed At</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100">
            {history.map((req) => (
              <tr key={req.id} className="hover:bg-[#F3F8FD]/50 transition-colors">
                <td className="py-3 px-4 font-bold text-linkedin-blue">{req.id}</td>
                <td className="py-3 px-4 font-sans">
                  <div className="font-bold text-slate-900">{req.entity}</div>
                  <div className="text-[11px] text-slate-500 font-mono">
                    Keywords: {Array.isArray(req.keywords) ? req.keywords.join(', ') : req.keywords}
                  </div>
                </td>
                <td className="py-3 px-4 text-slate-700 font-sans">
                  {req.category} ({req.location || 'Global'})
                </td>
                <td className="py-3 px-4 text-slate-600 font-sans">{formatRecencyWindow(req.time_window_minutes)}</td>
                <td className="py-3 px-4">
                  <span
                    className={`inline-flex items-center gap-1 font-bold px-2.5 py-0.5 rounded-full text-[10px] uppercase border ${
                      req.status === 'success'
                        ? 'bg-linkedin-light text-linkedin-blue border-linkedin-border'
                        : req.status === 'partial_success'
                        ? 'bg-amber-50 text-amber-800 border-amber-200'
                        : 'bg-rose-50 text-rose-800 border-rose-200'
                    }`}
                  >
                    {req.status}
                  </span>
                </td>
                <td className="py-3 px-4 text-slate-700 font-sans">
                  {req.summary ? (
                    <span>
                      {req.summary.articles_collected ?? 0} arts | {req.summary.duplicates_removed ?? 0} dups | ${req.summary.estimated_api_cost ?? 0}
                    </span>
                  ) : (
                    <span>-</span>
                  )}
                </td>
                <td className="py-3 px-4 text-slate-500 font-sans">
                  {new Date(req.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

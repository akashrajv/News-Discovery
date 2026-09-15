import React from 'react';
import { Route, CheckCircle2, XCircle, Info, DollarSign, Zap, GitBranch } from 'lucide-react';

export default function RoutingPanel({ routingSummary }) {
  if (!routingSummary) return null;

  const selected = routingSummary.selected_sources || [];
  const skipped = routingSummary.skipped_sources || [];
  const isCacheHit = routingSummary.cache_decision === 'HIT';

  return (
    <div className="bg-white rounded-xl border border-mongo-border shadow-xs p-5 mb-6">
      <div className="flex items-center justify-between border-b border-mongo-border pb-3 mb-4">
        <div className="flex items-center space-x-2">
          <GitBranch className="w-4 h-4 text-mongo-forest" />
          <h3 className="font-bold text-mongo-dark text-sm font-mono">
            Source Router Decision Rationale
          </h3>
        </div>
        <div>
          {isCacheHit ? (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-emerald-100 text-mongo-forest border border-emerald-300 rounded text-xs font-mono font-bold">
              <Zap className="w-3.5 h-3.5" />
              CACHE HIT (0 COST)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-2.5 py-0.5 bg-blue-50 text-blue-800 border border-blue-200 rounded text-xs font-mono font-semibold">
              <DollarSign className="w-3.5 h-3.5 text-blue-600" />
              COST-OPTIMIZED ROUTE
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Selected Sources */}
        <div className="bg-mongo-slate border border-mongo-border rounded-lg p-3">
          <h4 className="text-[11px] font-bold text-mongo-dark uppercase font-mono tracking-wider mb-2 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-mongo-forest" />
            <span>Selected Sources ({selected.length})</span>
          </h4>

          {selected.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No external source requests executed (Cache HIT active).</p>
          ) : (
            <div className="space-y-2 font-mono text-xs">
              {selected.map((item, idx) => (
                <div key={idx} className="bg-white border border-emerald-200 rounded p-2.5 shadow-2xs">
                  <div className="flex items-center justify-between font-bold text-mongo-dark mb-1">
                    <span className="text-mongo-forest">✓ {item.source_name}</span>
                    <span className="bg-emerald-50 text-mongo-forest px-2 py-0.5 rounded text-[10px] border border-emerald-200">
                      {item.connection_method.toUpperCase()} | ${item.estimated_cost}
                    </span>
                  </div>
                  <p className="text-slate-600 font-sans text-[11px]">{item.reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Skipped Sources */}
        <div className="bg-mongo-slate border border-mongo-border rounded-lg p-3">
          <h4 className="text-[11px] font-bold text-mongo-subtle uppercase font-mono tracking-wider mb-2 flex items-center gap-1.5">
            <XCircle className="w-4 h-4 text-slate-400" />
            <span>Skipped Sources ({skipped.length})</span>
          </h4>

          {skipped.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No sources were skipped.</p>
          ) : (
            <div className="space-y-2 font-mono text-xs max-h-48 overflow-y-auto pr-1">
              {skipped.map((item, idx) => (
                <div key={idx} className="bg-white border border-mongo-border rounded p-2.5 shadow-2xs">
                  <div className="flex items-center justify-between text-slate-700 font-semibold mb-1">
                    <span>{item.source_name}</span>
                    <span className="text-slate-500 bg-slate-100 px-1.5 py-0.5 rounded text-[10px]">
                      P{item.priority}
                    </span>
                  </div>
                  <p className="text-slate-500 text-[11px] font-sans">{item.reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

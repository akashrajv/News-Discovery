import React from 'react';
import { Route, CheckCircle2, XCircle, Info, DollarSign, Zap, GitBranch } from 'lucide-react';

export default function RoutingPanel({ routingSummary }) {
  if (!routingSummary) return null;

  const selected = routingSummary.selected_sources || [];
  const skipped = routingSummary.skipped_sources || [];
  const isCacheHit = routingSummary.cache_decision === 'HIT';

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 mb-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-4">
        <div className="flex items-center space-x-2">
          <GitBranch className="w-4 h-4 text-linkedin-blue" />
          <h3 className="font-bold text-slate-900 text-sm font-sans">
            Source Router Decision Rationale
          </h3>
        </div>
        <div>
          {isCacheHit ? (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-linkedin-light text-linkedin-blue border border-linkedin-border rounded-full text-xs font-mono font-bold">
              <Zap className="w-3.5 h-3.5" />
              CACHE HIT (0 COST)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 px-3 py-1 bg-blue-50 text-linkedin-blue border border-blue-200 rounded-full text-xs font-mono font-semibold">
              <DollarSign className="w-3.5 h-3.5 text-linkedin-blue" />
              COST-OPTIMIZED ROUTE
            </span>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Selected Sources */}
        <div className="bg-[#F3F8FD]/50 border border-slate-200 rounded-lg p-3">
          <h4 className="text-[11px] font-bold text-slate-800 uppercase font-sans tracking-wider mb-2 flex items-center gap-1.5">
            <CheckCircle2 className="w-4 h-4 text-linkedin-blue" />
            <span>Selected Sources ({selected.length})</span>
          </h4>

          {selected.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No external source requests executed (Cache HIT active).</p>
          ) : (
            <div className="space-y-2 font-mono text-xs">
              {selected.map((item, idx) => (
                <div key={idx} className="bg-white border border-linkedin-border rounded-lg p-2.5 shadow-2xs">
                  <div className="flex items-center justify-between font-bold text-slate-900 mb-1">
                    <span className="text-linkedin-blue font-sans font-bold">✓ {item.source_name}</span>
                    <span className="bg-linkedin-light text-linkedin-blue px-2 py-0.5 rounded-full text-[10px] border border-linkedin-border">
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
        <div className="bg-[#F3F8FD]/50 border border-slate-200 rounded-lg p-3">
          <h4 className="text-[11px] font-bold text-slate-600 uppercase font-sans tracking-wider mb-2 flex items-center gap-1.5">
            <XCircle className="w-4 h-4 text-slate-400" />
            <span>Skipped Sources ({skipped.length})</span>
          </h4>

          {skipped.length === 0 ? (
            <p className="text-xs text-slate-500 italic">No sources were skipped.</p>
          ) : (
            <div className="space-y-2 font-mono text-xs max-h-48 overflow-y-auto pr-1">
              {skipped.map((item, idx) => (
                <div key={idx} className="bg-white border border-slate-200 rounded-lg p-2.5 shadow-2xs">
                  <div className="flex items-center justify-between text-slate-700 font-semibold mb-1">
                    <span className="font-sans font-medium">{item.source_name}</span>
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

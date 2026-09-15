import React, { useState, useEffect } from 'react';
import { Server, CheckCircle2, Clock, AlertCircle, ShieldX } from 'lucide-react';
import { getNextResetUTC, formatCountdown } from '../utils/quotaUtils';

export default function SourceStatusCard({ sources }) {
  const [now, setNow] = useState(() => new Date());

  useEffect(() => {
    const timer = setInterval(() => {
      setNow(new Date());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  if (!sources || sources.length === 0) return null;

  const getStatusBadge = (status) => {
    switch (status) {
      case 'AVAILABLE':
      case 'SELECTED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-emerald-100 text-mongo-forest border border-emerald-300">
            <CheckCircle2 className="w-3 h-3" />
            {status}
          </span>
        );
      case 'RATE_LIMITED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-amber-100 text-amber-900 border border-amber-300">
            <Clock className="w-3 h-3" />
            RATE LIMITED
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-rose-100 text-rose-800 border border-rose-300">
            <AlertCircle className="w-3 h-3" />
            FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded text-xs font-mono font-bold bg-slate-100 text-slate-700 border border-slate-300">
            <ShieldX className="w-3 h-3" />
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-mongo-border shadow-xs p-5 mb-6">
      <div className="flex items-center justify-between border-b border-mongo-border pb-3 mb-4">
        <div className="flex items-center space-x-2">
          <Server className="w-5 h-5 text-mongo-forest" />
          <h3 className="font-bold text-mongo-dark text-base font-mono">
            Source Cluster Registry & Node Status
          </h3>
        </div>
        <span className="text-xs font-mono text-mongo-subtle">
          {sources.length} Configured Source Adapters
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {sources.map((src) => {
          const nextResetTime = src.next_reset_utc || getNextResetUTC(src.last_reset_at);
          const countdownText = formatCountdown(nextResetTime, now);

          return (
            <div
              key={src.id}
              className="border border-mongo-border rounded-lg p-4 bg-mongo-slate hover:border-mongo-forest transition-colors shadow-2xs flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-bold text-mongo-dark text-sm">{src.name}</h4>
                    <div className="flex items-center space-x-2 mt-1 font-mono text-[11px]">
                      <span className="font-bold text-mongo-forest uppercase px-2 py-0.5 bg-emerald-50 rounded border border-emerald-200">
                        {src.connection_method}
                      </span>
                      <span className="text-slate-500">Priority: {src.priority}</span>
                    </div>
                  </div>
                  {getStatusBadge(src.status || src.current_status)}
                </div>

                <div className="mt-3 pt-3 border-t border-mongo-border text-xs space-y-1.5 font-mono text-slate-700">
                  <div className="flex justify-between">
                    <span>API Key Configured:</span>
                    <span className={src.api_key_configured ? 'text-mongo-forest font-bold' : 'text-amber-700 font-bold'}>
                      {src.api_key_configured ? 'YES' : 'NO (RSS/Demo)'}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span>Remaining Quota:</span>
                    <span className="font-bold text-mongo-dark">
                      {src.requests_remaining ?? 100} reqs
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span>Used Today:</span>
                    <span className="font-mono text-slate-600">
                      {src.requests_used_today ?? src.requests_used ?? 0} reqs
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span>Est Cost / Req:</span>
                    <span className="text-mongo-dark font-bold">${src.estimated_cost ?? src.estimated_cost_per_request ?? 0}</span>
                  </div>

                  {src.last_error && (
                    <div className="mt-2 text-[11px] text-rose-700 bg-rose-50 p-2 rounded border border-rose-200 font-sans">
                      <strong>Last Error:</strong> {src.last_error}
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-mongo-border/50">
                <div className="flex items-center justify-between text-[11px] font-mono bg-mongo-forest/5 text-mongo-forest border border-emerald-200/80 px-2.5 py-1 rounded-md">
                  <span className="flex items-center gap-1 font-semibold">
                    <Clock className="w-3 h-3 text-mongo-forest" />
                    {countdownText}
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}


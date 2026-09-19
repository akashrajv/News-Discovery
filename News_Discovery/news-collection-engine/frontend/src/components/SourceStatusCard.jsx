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
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-linkedin-light text-linkedin-blue border border-linkedin-border">
            <CheckCircle2 className="w-3 h-3" />
            {status}
          </span>
        );
      case 'RATE_LIMITED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-amber-50 text-amber-800 border border-amber-200">
            <Clock className="w-3 h-3" />
            RATE LIMITED
          </span>
        );
      case 'FAILED':
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-rose-50 text-rose-800 border border-rose-200">
            <AlertCircle className="w-3 h-3" />
            FAILED
          </span>
        );
      default:
        return (
          <span className="inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-[10px] font-mono font-bold bg-slate-100 text-slate-700 border border-slate-200">
            <ShieldX className="w-3 h-3" />
            {status}
          </span>
        );
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 mb-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-4">
        <div className="flex items-center space-x-2">
          <Server className="w-5 h-5 text-linkedin-blue" />
          <h3 className="font-bold text-slate-900 text-base font-sans">
            Source Cluster Registry & Node Status
          </h3>
        </div>
        <span className="text-xs font-mono text-slate-500">
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
              className="border border-slate-200 rounded-xl p-4 bg-[#F3F8FD]/30 hover:border-linkedin-blue transition-colors shadow-2xs flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-bold text-slate-900 text-sm font-sans">{src.name}</h4>
                    <div className="flex items-center space-x-2 mt-1 font-mono text-[11px]">
                      <span className="font-bold text-linkedin-blue uppercase px-2 py-0.5 bg-linkedin-light rounded-full border border-linkedin-border text-[10px]">
                        {src.connection_method}
                      </span>
                      <span className="text-slate-500 font-sans">Priority: {src.priority}</span>
                    </div>
                  </div>
                  {getStatusBadge(src.status || src.current_status)}
                </div>

                <div className="mt-3 pt-3 border-t border-slate-200 text-xs space-y-1.5 font-mono text-slate-700">
                  <div className="flex justify-between">
                    <span>API Key Configured:</span>
                    <span className={src.api_key_configured ? 'text-linkedin-blue font-bold' : 'text-amber-700 font-bold'}>
                      {src.api_key_configured ? 'YES' : 'NO (RSS/Demo)'}
                    </span>
                  </div>

                  <div className="flex justify-between">
                    <span>Remaining Quota:</span>
                    <span className="font-bold text-slate-900">
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
                    <span className="text-slate-900 font-bold">${src.estimated_cost ?? src.estimated_cost_per_request ?? 0}</span>
                  </div>

                  {src.last_error && (
                    <div className="mt-2 text-[11px] text-rose-700 bg-rose-50 p-2 rounded border border-rose-200 font-sans">
                      <strong>Last Error:</strong> {src.last_error}
                    </div>
                  )}
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-200/80">
                <div className="flex items-center justify-between text-[11px] font-mono bg-linkedin-light text-linkedin-blue border border-linkedin-border px-2.5 py-1 rounded-md">
                  <span className="flex items-center gap-1 font-semibold">
                    <Clock className="w-3 h-3 text-linkedin-blue" />
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


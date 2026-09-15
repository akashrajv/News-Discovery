import React from 'react';
import { Activity, DollarSign, Database, CopyX, CheckCircle, PieChart } from 'lucide-react';

export default function UsageDashboard({ usageData }) {
  if (!usageData) {
    return (
      <div className="bg-white rounded-xl border border-mongo-border p-8 text-center text-slate-500">
        <Activity className="w-8 h-8 mx-auto text-mongo-forest mb-2 animate-bounce" />
        <p className="font-mono text-xs">Loading analytics telemetry...</p>
      </div>
    );
  }

  const {
    api_requests = 0,
    rss_collections = 0,
    cache_hits = 0,
    cache_misses = 0,
    duplicate_count = 0,
    successful_requests = 0,
    failed_requests = 0,
    estimated_api_cost = 0,
    cache_hit_rate = 0,
    source_utilization = {},
  } = usageData;

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl border border-mongo-border shadow-xs p-5">
        <div className="flex items-center justify-between border-b border-mongo-border pb-3 mb-5">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-mongo-forest" />
            <h3 className="font-bold text-mongo-dark text-base font-mono">
              Engine Metrics & Cost Analytics
            </h3>
          </div>
          <span className="text-xs font-mono text-mongo-subtle">
            Live Telemetry Aggregator
          </span>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 font-mono">
          <div className="p-4 rounded-xl bg-mongo-slate border border-mongo-border">
            <span className="text-[11px] font-bold text-mongo-subtle uppercase">API Requests</span>
            <div className="text-3xl font-bold text-mongo-dark mt-1">{api_requests}</div>
          </div>

          <div className="p-4 rounded-xl bg-mongo-slate border border-mongo-border">
            <span className="text-[11px] font-bold text-mongo-subtle uppercase">RSS Collections</span>
            <div className="text-3xl font-bold text-mongo-dark mt-1">{rss_collections}</div>
          </div>

          <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200">
            <span className="text-[11px] font-bold text-mongo-forest uppercase">Cache Hit Rate</span>
            <div className="text-3xl font-bold text-mongo-forest mt-1">{cache_hit_rate}%</div>
            <span className="text-[10px] text-slate-500">{cache_hits} hits / {cache_hits + cache_misses} total</span>
          </div>

          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
            <span className="text-[11px] font-bold text-amber-900 uppercase">Estimated Cost</span>
            <div className="text-3xl font-bold text-amber-950 mt-1">${estimated_api_cost.toFixed(4)}</div>
            <span className="text-[10px] text-amber-700 font-sans">Configured pricing</span>
          </div>
        </div>

        {/* Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
          <div className="border border-mongo-border rounded-lg p-4 bg-mongo-slate">
            <h4 className="text-[11px] font-bold text-mongo-dark uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <CheckCircle className="w-4 h-4 text-mongo-forest" />
              <span>Execution Summary</span>
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between bg-white p-2.5 rounded border border-mongo-border">
                <span>Successful Requests:</span>
                <span className="font-bold text-mongo-forest">{successful_requests}</span>
              </div>
              <div className="flex justify-between bg-white p-2.5 rounded border border-mongo-border">
                <span>Failed Requests:</span>
                <span className="font-bold text-rose-600">{failed_requests}</span>
              </div>
              <div className="flex justify-between bg-white p-2.5 rounded border border-mongo-border">
                <span>Duplicates Linked:</span>
                <span className="font-bold text-amber-700">{duplicate_count}</span>
              </div>
            </div>
          </div>

          <div className="border border-mongo-border rounded-lg p-4 bg-mongo-slate">
            <h4 className="text-[11px] font-bold text-mongo-dark uppercase tracking-wider mb-3 flex items-center gap-1.5">
              <PieChart className="w-4 h-4 text-mongo-forest" />
              <span>Source Utilization</span>
            </h4>
            {Object.keys(source_utilization).length === 0 ? (
              <p className="text-xs text-slate-500 italic font-sans">No utilization recorded.</p>
            ) : (
              <div className="space-y-2 font-mono">
                {Object.entries(source_utilization).map(([sourceName, count]) => (
                  <div key={sourceName} className="flex justify-between bg-white p-2.5 rounded border border-mongo-border">
                    <span className="text-slate-800 font-sans">{sourceName}:</span>
                    <span className="font-bold text-mongo-dark">{count} runs</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

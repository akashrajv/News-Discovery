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
      <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5">
        <div className="flex items-center justify-between border-b border-slate-200 pb-3 mb-5">
          <div className="flex items-center space-x-2">
            <Activity className="w-5 h-5 text-linkedin-blue" />
            <h3 className="font-bold text-slate-900 text-base font-sans">
              Engine Metrics & Cost Analytics
            </h3>
          </div>
          <span className="text-xs font-mono text-slate-500">
            Live Telemetry Aggregator
          </span>
        </div>

        {/* Top Metric Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6 font-mono">
          <div className="p-4 rounded-xl bg-[#F3F8FD]/50 border border-slate-200">
            <span className="text-[11px] font-bold text-slate-500 uppercase font-sans">API Requests</span>
            <div className="text-3xl font-bold text-slate-900 mt-1">{api_requests}</div>
          </div>

          <div className="p-4 rounded-xl bg-[#F3F8FD]/50 border border-slate-200">
            <span className="text-[11px] font-bold text-slate-500 uppercase font-sans">RSS Collections</span>
            <div className="text-3xl font-bold text-slate-900 mt-1">{rss_collections}</div>
          </div>

          <div className="p-4 rounded-xl bg-linkedin-light border border-linkedin-border">
            <span className="text-[11px] font-bold text-linkedin-blue uppercase font-sans">Cache Hit Rate</span>
            <div className="text-3xl font-bold text-linkedin-blue mt-1">{cache_hit_rate}%</div>
            <span className="text-[10px] text-slate-500 font-sans">{cache_hits} hits / {cache_hits + cache_misses} total</span>
          </div>

          <div className="p-4 rounded-xl bg-amber-50 border border-amber-200">
            <span className="text-[11px] font-bold text-amber-800 uppercase font-sans">Estimated Cost</span>
            <div className="text-3xl font-bold text-amber-950 mt-1">${estimated_api_cost.toFixed(4)}</div>
            <span className="text-[10px] text-amber-700 font-sans">Configured pricing</span>
          </div>
        </div>

        {/* Breakdown */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 font-mono text-xs">
          <div className="border border-slate-200 rounded-xl p-4 bg-[#F3F8FD]/30">
            <h4 className="text-[11px] font-bold text-slate-800 uppercase tracking-wider mb-3 flex items-center gap-1.5 font-sans">
              <CheckCircle className="w-4 h-4 text-linkedin-blue" />
              <span>Execution Summary</span>
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
                <span className="font-sans text-slate-700">Successful Requests:</span>
                <span className="font-bold text-linkedin-blue">{successful_requests}</span>
              </div>
              <div className="flex justify-between bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
                <span className="font-sans text-slate-700">Failed Requests:</span>
                <span className="font-bold text-rose-600">{failed_requests}</span>
              </div>
              <div className="flex justify-between bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
                <span className="font-sans text-slate-700">Duplicates Linked:</span>
                <span className="font-bold text-amber-800">{duplicate_count}</span>
              </div>
            </div>
          </div>

          <div className="border border-slate-200 rounded-xl p-4 bg-[#F3F8FD]/30">
            <h4 className="text-[11px] font-bold text-slate-800 uppercase tracking-wider mb-3 flex items-center gap-1.5 font-sans">
              <PieChart className="w-4 h-4 text-linkedin-blue" />
              <span>Source Utilization</span>
            </h4>
            {Object.keys(source_utilization).length === 0 ? (
              <p className="text-xs text-slate-500 italic font-sans">No utilization recorded.</p>
            ) : (
              <div className="space-y-2 font-mono">
                {Object.entries(source_utilization).map(([sourceName, count]) => (
                  <div key={sourceName} className="flex justify-between bg-white p-2.5 rounded-lg border border-slate-200 shadow-2xs">
                    <span className="text-slate-800 font-sans">{sourceName}:</span>
                    <span className="font-bold text-slate-900">{count} runs</span>
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

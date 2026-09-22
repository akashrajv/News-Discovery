import React from 'react';
import { Layers, Activity, Server, History, ShieldAlert, Cpu, Sparkles, Terminal } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, health, demoMode, isConnected = true, isRetrying = false, onRetry }) {
  return (
    <header className="bg-white text-slate-900 border-b border-slate-200 sticky top-0 z-40 shadow-xs">
      <div className="w-full max-w-[1600px] mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between min-h-[64px] py-2 gap-3">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3 shrink-0">
            <div className="bg-linkedin-blue p-2 rounded-lg text-white font-bold shadow-xs flex items-center justify-center shrink-0">
              <Layers className="w-5 h-5 text-white" />
            </div>
            <div className="shrink-0">
              <div className="flex items-center space-x-2">
                <h1 className="text-sm sm:text-base font-bold tracking-tight text-slate-900 font-sans whitespace-nowrap">
                  News Collection Engine
                </h1>
                <span className="text-[10px] bg-linkedin-light text-linkedin-blue border border-linkedin-border font-mono px-2 py-0.5 rounded-full font-bold whitespace-nowrap shrink-0">
                  Layer 1.0
                </span>
              </div>
              <p className="text-xs text-slate-500 font-sans whitespace-nowrap">Multi-Source Permitted Discovery Engine</p>
            </div>
          </div>

          {/* Center Badges */}
          <div className="hidden lg:flex items-center space-x-1.5 xl:space-x-2 shrink-0">
            {demoMode && (
              <div className="flex items-center space-x-1.5 bg-amber-50 border border-amber-200 text-amber-800 text-[11px] font-mono px-2.5 py-1 rounded-full whitespace-nowrap shrink-0">
                <Cpu className="w-3.5 h-3.5 shrink-0" />
                <span className="font-semibold whitespace-nowrap">DEMO MODE</span>
              </div>
            )}

            {/* SQLite Primary Database Status */}
            <div
              className="flex items-center space-x-1.5 text-[11px] font-mono px-2.5 py-1 rounded-full border bg-blue-50 border-blue-200 text-linkedin-blue whitespace-nowrap shrink-0"
              title="SQLite Database: news_engine.db (Primary Article Store)"
            >
              <div className="w-2 h-2 rounded-full bg-linkedin-blue shrink-0" />
              <span className="font-semibold whitespace-nowrap">SQLite: Primary DB</span>
            </div>

            {/* MongoDB Atlas Status (Only if configured) */}
            {health?.mongodb?.configured && (
              <div
                className={`flex items-center space-x-1.5 text-[11px] font-mono px-2.5 py-1 rounded-full border whitespace-nowrap shrink-0 ${
                  health.mongodb.status === 'connected'
                    ? 'bg-blue-50 border-blue-200 text-linkedin-blue'
                    : health.mongodb.status === 'auth_or_connection_error'
                    ? 'bg-amber-50 border-amber-200 text-amber-800'
                    : 'bg-slate-100 border-slate-200 text-slate-500'
                }`}
                title={
                  health.mongodb.status === 'connected'
                    ? `MongoDB Atlas: Connected (${health.mongodb.articles_count || 0} articles in ${health.mongodb.database})`
                    : `MongoDB Atlas: ${health.mongodb.error || 'Check Network Access / IP Whitelist'}`
                }
              >
                <div
                  className={`w-2 h-2 rounded-full shrink-0 ${
                    health.mongodb.status === 'connected'
                      ? 'bg-linkedin-blue animate-pulse'
                      : health.mongodb.status === 'auth_or_connection_error'
                      ? 'bg-amber-500'
                      : 'bg-slate-400'
                  }`}
                />
                <span className="font-semibold whitespace-nowrap">
                  {health.mongodb.status === 'connected'
                    ? 'Atlas: Connected'
                    : health.mongodb.status === 'auth_or_connection_error'
                    ? 'Atlas: IP / Auth Setup'
                    : 'Atlas: Inactive'}
                </span>
              </div>
            )}

            {/* Qdrant Vector Engine Status */}
            <div
              className="flex items-center space-x-1.5 text-[11px] font-mono px-2.5 py-1 rounded-full border bg-emerald-50 border-emerald-200 text-emerald-800 whitespace-nowrap shrink-0"
              title={`Qdrant Vector DB: ${health?.qdrant?.mode || 'Active'} (${health?.qdrant?.indexed_vectors || 0} vectors indexed)`}
            >
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse shrink-0" />
              <span className="font-semibold whitespace-nowrap">
                Qdrant: {health?.qdrant?.mode === 'remote' ? 'Cloud' : 'Vector DB'}
              </span>
            </div>

            {/* DeepSeek-R1 AI Engine Status */}
            <div
              className="flex items-center space-x-1.5 text-[11px] font-mono px-2.5 py-1 rounded-full border bg-purple-50 border-purple-200 text-purple-800 whitespace-nowrap shrink-0"
              title={`DeepSeek-R1: ${health?.deepseek_r1?.model || 'deepseek-reasoner'} (${health?.deepseek_r1?.status || 'Active'})`}
            >
              <Sparkles className="w-3.5 h-3.5 text-purple-600 shrink-0" />
              <span className="font-semibold whitespace-nowrap">DeepSeek-R1</span>
            </div>

            {/* Backend Connection Status */}
            <div
              onClick={!isConnected && onRetry ? onRetry : undefined}
              className={`flex items-center space-x-1.5 text-[11px] font-mono px-2.5 py-1 rounded-full border transition-all whitespace-nowrap shrink-0 ${
                isConnected
                  ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                  : 'bg-rose-50 border-rose-200 text-rose-800 cursor-pointer hover:bg-rose-100'
              }`}
              title={isConnected ? 'Backend connected at http://127.0.0.1:8000' : 'Click to reconnect to backend'}
            >
              <div
                className={`w-2 h-2 rounded-full shrink-0 ${
                  isConnected
                    ? 'bg-emerald-500 animate-pulse'
                    : isRetrying
                    ? 'bg-amber-500 animate-ping'
                    : 'bg-rose-500 animate-pulse'
                }`}
              />
              <span className="font-semibold whitespace-nowrap">
                {isConnected
                  ? (health?.status === 'degraded_mongodb' ? 'Online (SQLite)' : 'Engine Online')
                  : isRetrying
                  ? 'Connecting...'
                  : 'Offline (Click to Retry)'}
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 bg-[#F3F2F0] p-1 rounded-lg border border-slate-200 shrink-0">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap shrink-0 transition-all cursor-pointer ${
                activeTab === 'dashboard'
                  ? 'bg-linkedin-blue text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/80'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5 shrink-0" />
              <span className="whitespace-nowrap">Discovery Hub</span>
            </button>

            <button
              onClick={() => setActiveTab('sources')}
              className={`flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap shrink-0 transition-all cursor-pointer ${
                activeTab === 'sources'
                  ? 'bg-linkedin-blue text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/80'
              }`}
            >
              <Server className="w-3.5 h-3.5 shrink-0" />
              <span className="whitespace-nowrap">Sources & Health</span>
            </button>

            <button
              onClick={() => setActiveTab('usage')}
              className={`flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap shrink-0 transition-all cursor-pointer ${
                activeTab === 'usage'
                  ? 'bg-linkedin-blue text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/80'
              }`}
            >
              <Activity className="w-3.5 h-3.5 shrink-0" />
              <span className="whitespace-nowrap">Metrics & Costs</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-1.5 px-2.5 sm:px-3 py-1.5 rounded-md text-xs font-semibold whitespace-nowrap shrink-0 transition-all cursor-pointer ${
                activeTab === 'history'
                  ? 'bg-linkedin-blue text-white shadow-xs'
                  : 'text-slate-600 hover:text-slate-900 hover:bg-white/80'
              }`}
            >
              <History className="w-3.5 h-3.5 shrink-0" />
              <span className="whitespace-nowrap">Audit Log</span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}

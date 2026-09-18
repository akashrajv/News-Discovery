import React from 'react';
import { Layers, Activity, Server, History, ShieldAlert, Cpu, Sparkles, Terminal } from 'lucide-react';

export default function Header({ activeTab, setActiveTab, health, demoMode }) {
  return (
    <header className="bg-mongo-dark text-white border-b border-slate-800 sticky top-0 z-40 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo & Title */}
          <div className="flex items-center space-x-3">
            <div className="bg-mongo-forest p-2 rounded-lg text-mongo-green font-bold shadow-inner">
              <Layers className="w-5 h-5 text-mongo-green" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h1 className="text-base font-bold tracking-tight text-white font-mono">
                  News Collection Engine
                </h1>
                <span className="text-[10px] bg-mongo-forest/40 text-mongo-green border border-mongo-forest font-mono px-2 py-0.5 rounded-full font-semibold">
                  Layer 1.0
                </span>
              </div>
              <p className="text-xs text-slate-400 font-sans">Multi-Source Permitted Discovery Engine</p>
            </div>
          </div>

          {/* Center Badges */}
          <div className="hidden lg:flex items-center space-x-2.5">
            {demoMode && (
              <div className="flex items-center space-x-1.5 bg-amber-500/10 border border-amber-500/30 text-amber-300 text-xs font-mono px-2.5 py-1 rounded-full">
                <Cpu className="w-3.5 h-3.5" />
                <span>DEMO MODE</span>
              </div>
            )}

            {/* MongoDB Atlas Status */}
            {health?.mongodb && (
              <div
                className={`flex items-center space-x-1.5 text-xs font-mono px-2.5 py-1 rounded-full border ${
                  health.mongodb.status === 'connected'
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400'
                    : health.mongodb.status === 'auth_or_connection_error'
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    : 'bg-slate-800 border-slate-700 text-slate-400'
                }`}
                title={
                  health.mongodb.status === 'connected'
                    ? `MongoDB Atlas: Connected (${health.mongodb.articles_count || 0} articles in ${health.mongodb.database})`
                    : `MongoDB Atlas: ${health.mongodb.error || 'Check Network Access / IP Whitelist'}`
                }
              >
                <div
                  className={`w-2 h-2 rounded-full ${
                    health.mongodb.status === 'connected'
                      ? 'bg-mongo-green animate-pulse'
                      : health.mongodb.status === 'auth_or_connection_error'
                      ? 'bg-amber-400'
                      : 'bg-slate-500'
                  }`}
                />
                <span className="font-semibold">
                  {health.mongodb.status === 'connected'
                    ? 'Atlas: Connected'
                    : health.mongodb.status === 'auth_or_connection_error'
                    ? 'Atlas: IP / Auth Setup'
                    : 'Atlas: Inactive'}
                </span>
              </div>
            )}

            <div className="flex items-center space-x-1.5 bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 text-xs font-mono px-2.5 py-1 rounded-full">
              <div className="w-2 h-2 rounded-full bg-mongo-green" />
              <span className="font-semibold">
                {health?.status === 'healthy'
                  ? 'Engine Online'
                  : health?.status === 'degraded_mongodb'
                  ? 'Engine Online (SQLite Fallback)'
                  : 'Connecting...'}
              </span>
            </div>
          </div>

          {/* Navigation Tabs */}
          <nav className="flex space-x-1 bg-slate-900/60 p-1 rounded-lg border border-slate-800">
            <button
              onClick={() => setActiveTab('dashboard')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'dashboard'
                  ? 'bg-mongo-forest text-mongo-green shadow-xs'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Sparkles className="w-3.5 h-3.5" />
              <span>Discovery Hub</span>
            </button>

            <button
              onClick={() => setActiveTab('sources')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'sources'
                  ? 'bg-mongo-forest text-mongo-green shadow-xs'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Server className="w-3.5 h-3.5" />
              <span>Sources & Health</span>
            </button>

            <button
              onClick={() => setActiveTab('usage')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'usage'
                  ? 'bg-mongo-forest text-mongo-green shadow-xs'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              <span>Metrics & Costs</span>
            </button>

            <button
              onClick={() => setActiveTab('history')}
              className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-xs font-semibold transition-all ${
                activeTab === 'history'
                  ? 'bg-mongo-forest text-mongo-green shadow-xs'
                  : 'text-slate-300 hover:text-white hover:bg-slate-800'
              }`}
            >
              <History className="w-3.5 h-3.5" />
              <span>Audit Log</span>
            </button>
          </nav>
        </div>
      </div>
    </header>
  );
}

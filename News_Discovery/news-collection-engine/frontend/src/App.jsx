import React, { useState, useEffect } from 'react';
import Header from './components/Header';
import CollectionForm from './components/CollectionForm';
import StatsCards from './components/StatsCards';
import RoutingPanel from './components/RoutingPanel';
import SourceStatusCard from './components/SourceStatusCard';
import ArticleTable from './components/ArticleTable';
import ArticleDetailModal from './components/ArticleDetailModal';
import UsageDashboard from './components/UsageDashboard';
import CollectionHistory from './components/CollectionHistory';

import {
  collectNews,
  fetchArticles,
  fetchSourcesStatus,
  fetchUsage,
  fetchCollectionHistory,
  fetchHealth,
  fetchLastRoutingDecision,
} from './services/api';

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Core Data States
  const [health, setHealth] = useState(null);
  const [sources, setSources] = useState([]);
  const [articles, setArticles] = useState([]);
  const [stats, setStats] = useState(null);
  const [routingSummary, setRoutingSummary] = useState(null);
  const [usageData, setUsageData] = useState(null);
  const [history, setHistory] = useState([]);
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [activeTargetFilter, setActiveTargetFilter] = useState({ entity: '', keywords: [] });

  const [isConnected, setIsConnected] = useState(false);
  const [isRetrying, setIsRetrying] = useState(false);

  // Initial Load & Health Check with auto-recovery
  const loadInitialData = async (manual = false) => {
    if (manual) setIsRetrying(true);
    try {
      const healthRes = await fetchHealth();
      setHealth(healthRes);
      setIsConnected(true);
      setError(null);

      const [sourcesRes, articlesRes, usageRes, historyRes, routingRes] = await Promise.allSettled([
        fetchSourcesStatus(),
        fetchArticles(),
        fetchUsage(),
        fetchCollectionHistory(),
        fetchLastRoutingDecision(),
      ]);

      if (sourcesRes.status === 'fulfilled') setSources(sourcesRes.value);
      if (articlesRes.status === 'fulfilled') setArticles(articlesRes.value);
      if (usageRes.status === 'fulfilled') setUsageData(usageRes.value);
      if (historyRes.status === 'fulfilled') setHistory(historyRes.value);
      if (routingRes.status === 'fulfilled' && routingRes.value?.request_id) {
        setRoutingSummary(routingRes.value);
      }
    } catch (err) {
      console.error('Failed loading backend state:', err);
      setIsConnected(false);
      setError('Could not connect to FastAPI backend server. Ensure backend is running at http://127.0.0.1:8000.');
    } finally {
      if (manual) setIsRetrying(false);
    }
  };

  useEffect(() => {
    loadInitialData();

    // Resilient heartbeat: every 3.5s if disconnected, every 25s if connected
    const interval = setInterval(() => {
      if (!isConnected) {
        loadInitialData();
      } else {
        fetchHealth()
          .then((h) => {
            setHealth(h);
            setIsConnected(true);
          })
          .catch(() => {
            setIsConnected(false);
          });
      }
    }, isConnected ? 25000 : 3500);

    return () => clearInterval(interval);
  }, [isConnected]);

  // Handle Pipeline Execution Request
  const handleCollect = async (formData) => {
    setLoading(true);
    setError(null);
    setActiveTargetFilter({
      entity: formData.entity || '',
      keywords: formData.keywords || [],
    });
    try {
      const response = await collectNews(formData);
      setArticles(response.articles || []);
      setStats({
        articles_collected: response.articles_collected,
        duplicates_removed: response.duplicates_removed,
        low_relevance_filtered: response.low_relevance_filtered ?? 0,
        cache_hits: response.cache_hits,
        cache_misses: response.cache_misses,
        api_requests: response.api_requests,
        rss_collections: response.rss_collections,
        sources_used: response.sources_used,
        sources_failed: response.sources_failed,
        estimated_api_cost: response.estimated_api_cost,
      });

      if (response.routing_summary) {
        setRoutingSummary(response.routing_summary);
      }

      // Refresh sources, usage & history
      const [sourcesRes, usageRes, historyRes] = await Promise.all([
        fetchSourcesStatus(),
        fetchUsage(),
        fetchCollectionHistory(),
      ]);
      setSources(sourcesRes);
      setUsageData(usageRes);
      setHistory(historyRes);
    } catch (err) {
      console.error('Collection execution error:', err);
      setError(err.response?.data?.detail || 'Pipeline execution failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#F3F2F0] flex flex-col font-sans text-slate-900 selection:bg-linkedin-blue selection:text-white">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        demoMode={health?.demo_mode ?? true}
        isConnected={isConnected}
        isRetrying={isRetrying}
        onRetry={() => loadInitialData(true)}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Banner Alert for Error or Disconnected Backend */}
        {error && (
          <div className="mb-6 bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-xl text-xs flex flex-wrap justify-between items-center gap-2 shadow-xs">
            <div className="flex items-center space-x-2 font-mono">
              <span className="relative flex h-2.5 w-2.5">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-rose-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2.5 w-2.5 bg-rose-500"></span>
              </span>
              <span>{error}</span>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => loadInitialData(true)}
                disabled={isRetrying}
                className="bg-rose-600 hover:bg-rose-700 text-white px-3 py-1 rounded-md text-xs font-semibold shadow-xs transition-all cursor-pointer disabled:opacity-50"
              >
                {isRetrying ? 'Connecting...' : 'Retry Connection Now'}
              </button>
              <button
                onClick={() => setError(null)}
                className="text-xs font-bold underline hover:text-rose-950 cursor-pointer"
              >
                Dismiss
              </button>
            </div>
          </div>
        )}

        {/* Dashboard / Discovery Hub Tab View */}
        {activeTab === 'dashboard' && (
          <div>
            <CollectionForm onCollect={handleCollect} loading={loading} />
            <StatsCards stats={stats} />
            <RoutingPanel routingSummary={routingSummary} />
            <ArticleTable
              articles={articles}
              activeTargetFilter={activeTargetFilter}
              onClearFilter={() => setActiveTargetFilter({ entity: '', keywords: [] })}
              onSelectArticle={(art) => setSelectedArticle(art)}
              onCollectForCompany={(companyName) => {
                handleCollect({
                  entity: companyName,
                  keywords: [],
                  time_window_minutes: 60
                });
              }}
            />
          </div>
        )}

        {/* Sources Tab View */}
        {activeTab === 'sources' && (
          <div>
            <SourceStatusCard sources={sources} />
          </div>
        )}

        {/* Usage Analytics Tab View */}
        {activeTab === 'usage' && (
          <div>
            <UsageDashboard usageData={usageData} />
          </div>
        )}

        {/* History Audit Tab View */}
        {activeTab === 'history' && (
          <div>
            <CollectionHistory history={history} />
          </div>
        )}
      </main>

      {/* Article Detail Inspector Modal */}
      {selectedArticle && (
        <ArticleDetailModal
          article={selectedArticle}
          onClose={() => setSelectedArticle(null)}
        />
      )}

      {/* LinkedIn Style Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500 font-sans">
        <span className="font-semibold text-linkedin-blue">News Collection Engine</span> &bull; Layer 1.0 &copy; 2026 AI News Intelligence Platform
      </footer>
    </div>
  );
}

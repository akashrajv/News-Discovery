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

  // Initial Load & Health Check
  const loadInitialData = async () => {
    try {
      const healthRes = await fetchHealth();
      setHealth(healthRes);

      const sourcesRes = await fetchSourcesStatus();
      setSources(sourcesRes);

      const articlesRes = await fetchArticles();
      setArticles(articlesRes);

      const usageRes = await fetchUsage();
      setUsageData(usageRes);

      const historyRes = await fetchCollectionHistory();
      setHistory(historyRes);

      const routingRes = await fetchLastRoutingDecision();
      if (routingRes && routingRes.request_id) {
        setRoutingSummary(routingRes);
      }
    } catch (err) {
      console.error('Failed loading backend initial state:', err);
      setError('Could not connect to FastAPI backend server. Ensure backend is running at http://127.0.0.1:8000.');
    }
  };

  useEffect(() => {
    loadInitialData();
  }, []);

  // Handle Pipeline Execution Request
  const handleCollect = async (formData) => {
    setLoading(true);
    setError(null);
    try {
      const response = await collectNews(formData);
      setArticles(response.articles || []);
      setStats({
        articles_collected: response.articles_collected,
        duplicates_removed: response.duplicates_removed,
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
    <div className="min-h-screen bg-mongo-slate flex flex-col font-sans text-mongo-dark selection:bg-mongo-green selection:text-mongo-dark">
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        health={health}
        demoMode={health?.demo_mode ?? true}
      />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Banner Alert for Error */}
        {error && (
          <div className="mb-6 bg-rose-50 border border-rose-200 text-rose-800 px-4 py-3 rounded-xl text-xs font-mono flex justify-between items-center">
            <span>{error}</span>
            <button
              onClick={() => setError(null)}
              className="text-xs font-bold underline hover:text-rose-950 ml-4"
            >
              Dismiss
            </button>
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

      {/* MongoDB Atlas Style Footer */}
      <footer className="bg-white border-t border-mongo-border py-4 text-center text-xs font-mono text-mongo-subtle">
        Antigravity News Collection Engine &bull; Layer 1.0 &copy; 2026 AI News Intelligence Platform
      </footer>
    </div>
  );
}

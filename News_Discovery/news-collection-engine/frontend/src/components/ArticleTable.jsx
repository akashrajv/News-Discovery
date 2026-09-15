import React, { useState } from 'react';
import { Newspaper, ExternalLink, Filter, CopyX, CheckCircle, Search, Layers, Clock, ArrowUpRight, Target, Sparkles, AlertTriangle, TrendingUp, ShieldAlert } from 'lucide-react';

export default function ArticleTable({ articles, onSelectArticle, onCollectForCompany }) {
  const [filterCompany, setFilterCompany] = useState('ALL');
  const [filterImportance, setFilterImportance] = useState('ALL');
  const [searchQuery, setSearchQuery] = useState('');

  if (!articles) return null;

  const companiesList = ['ALL', 'NVIDIA', 'Tata Motors', 'Tesla', 'Apple', 'Microsoft'];
  const importanceLevels = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'];

  const filteredArticles = articles.filter((art) => {
    const targetText = `${art.target_entity || ''} ${art.title} ${art.description || ''} ${art.source}`.toLowerCase();
    
    // Company match
    let matchesCompany = filterCompany === 'ALL';
    if (!matchesCompany) {
      const compLower = filterCompany.toLowerCase();
      const aliases = {
        'nvidia': ['nvidia', 'nvda', 'geforce', 'blackwell'],
        'tata motors': ['tata motors', 'tata motor', 'tata nexon', 'tata tiago', 'jlr', 'jaguar land rover'],
        'tesla': ['tesla', 'tsla', 'elon musk', 'cybercab', 'robotaxi'],
        'apple': ['apple', 'aapl', 'iphone', 'macbook', 'ios'],
        'microsoft': ['microsoft', 'msft', 'azure', 'copilot']
      }[compLower] || [compLower];

      matchesCompany = aliases.some(alias => targetText.includes(alias));
    }

    // Importance rating match
    const matchesImportance =
      filterImportance === 'ALL' ||
      (art.importance_rating && art.importance_rating.toUpperCase() === filterImportance.toUpperCase());

    // Search query match
    const matchesSearch =
      searchQuery === '' || targetText.includes(searchQuery.toLowerCase());

    return matchesCompany && matchesImportance && matchesSearch;
  });

  const formatDate = (isoStr, pubUnavailable) => {
    if (pubUnavailable || !isoStr) return <span className="text-slate-400 italic font-mono text-[11px]">Time N/A</span>;
    try {
      const dt = new Date(isoStr);
      return dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', month: 'short', day: 'numeric' });
    } catch {
      return <span className="text-slate-400 font-mono text-[11px]">Unknown</span>;
    }
  };

  const renderImportanceBadge = (rating) => {
    const r = (rating || 'MEDIUM').toUpperCase();
    if (r === 'CRITICAL') {
      return (
        <span className="inline-flex items-center gap-1 font-mono font-bold text-rose-900 bg-rose-100 border border-rose-300 px-2 py-0.5 rounded">
          <ShieldAlert className="w-3 h-3 text-rose-700" /> Critical Impact
        </span>
      );
    }
    if (r === 'HIGH') {
      return (
        <span className="inline-flex items-center gap-1 font-mono font-bold text-amber-900 bg-amber-100 border border-amber-300 px-2 py-0.5 rounded">
          <TrendingUp className="w-3 h-3 text-amber-700" /> High Importance
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 font-mono font-bold text-slate-700 bg-slate-100 border border-slate-300 px-2 py-0.5 rounded">
        Medium Importance
      </span>
    );
  };

  const renderSentimentBadge = (tone) => {
    if (!tone || tone === 'Neutral') return null;
    const isRisk = tone.includes('Risk') || tone.includes('Threat');
    return (
      <span className={`inline-flex items-center gap-1 font-mono font-bold px-2 py-0.5 rounded border ${
        isRisk ? 'text-rose-800 bg-rose-50 border-rose-200' : 'text-emerald-800 bg-emerald-50 border-emerald-200'
      }`}>
        <Sparkles className="w-3 h-3" /> {tone}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl border border-mongo-border shadow-xs overflow-hidden mb-6">
      {/* Feed Header */}
      <div className="p-5 border-b border-mongo-border flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Newspaper className="w-5 h-5 text-mongo-forest" />
            <h3 className="font-bold text-mongo-dark text-base font-mono">
              Target Company Intelligence Stream
            </h3>
            <span className="bg-emerald-100 text-mongo-forest text-xs font-mono font-bold px-2.5 py-0.5 rounded-full border border-emerald-300">
              {filteredArticles.length} Articles
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5">
            AI-analyzed, semantically matched, and importance-ranked target news
          </p>
        </div>

        {/* Filter controls */}
        <div className="flex flex-wrap items-center gap-3">
          {/* Quick Search */}
          <div className="relative">
            <input
              type="text"
              placeholder="Search headline / topic..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="text-xs pl-8 pr-3 py-1.5 border border-mongo-border rounded-lg focus:outline-none focus:ring-2 focus:ring-mongo-forest bg-mongo-slate font-medium text-mongo-dark w-48 sm:w-56"
            />
            <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
          </div>

          {/* Importance Filter */}
          <div className="flex items-center space-x-1 bg-mongo-slate p-1 rounded-lg border border-mongo-border text-xs font-mono">
            {importanceLevels.map((imp) => (
              <button
                key={imp}
                onClick={() => setFilterImportance(imp)}
                className={`px-2 py-1 rounded font-bold transition-all ${
                  filterImportance === imp
                    ? 'bg-slate-800 text-white shadow-2xs'
                    : 'text-slate-600 hover:text-mongo-dark hover:bg-slate-200'
                }`}
              >
                {imp}
              </button>
            ))}
          </div>

          {/* Company Filter Buttons */}
          <div className="flex items-center space-x-1 bg-mongo-slate p-1 rounded-lg border border-mongo-border text-xs font-mono overflow-x-auto">
            {companiesList.map((comp) => (
              <button
                key={comp}
                onClick={() => setFilterCompany(comp)}
                className={`px-2.5 py-1 rounded font-bold transition-all whitespace-nowrap ${
                  filterCompany === comp
                    ? 'bg-mongo-forest text-mongo-green shadow-2xs'
                    : 'text-slate-600 hover:text-mongo-dark hover:bg-slate-200'
                }`}
              >
                {comp}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Feed List Cards View */}
      {filteredArticles.length === 0 ? (
        <div className="p-12 text-center text-slate-500">
          <Target className="w-10 h-10 mx-auto text-slate-300 mb-2" />
          <p className="font-bold text-mongo-dark">No matching target company articles found.</p>
          <p className="text-xs text-slate-500 mt-1">
            {filterCompany !== 'ALL'
              ? `No articles directly relevant to ${filterCompany} in current cache.`
              : 'Run a discovery request above to fetch live news.'}
          </p>
          {filterCompany !== 'ALL' && onCollectForCompany && (
            <button
              onClick={() => onCollectForCompany(filterCompany)}
              className="mt-4 inline-flex items-center space-x-1.5 px-4 py-2 text-xs font-mono font-bold text-mongo-green bg-mongo-forest hover:bg-[#00523a] rounded-lg transition-colors shadow-sm"
            >
              <Sparkles className="w-4 h-4 text-mongo-green" />
              <span>Collect News for {filterCompany}</span>
            </button>
          )}
        </div>
      ) : (
        <div className="divide-y divide-mongo-border">
          {filteredArticles.map((art) => {
            const relScore = art.relevance_score != null ? Math.round(art.relevance_score) : 85;
            return (
              <div
                key={art.id}
                className="p-5 hover:bg-mongo-slate/60 transition-colors flex flex-col md:flex-row md:items-start justify-between gap-4"
              >
                {/* Content Main */}
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-2 font-mono text-[11px]">
                    {/* Source Badge */}
                    <span className="font-bold text-mongo-dark bg-slate-100 border border-slate-200 px-2 py-0.5 rounded">
                      {art.source}
                    </span>

                    {/* AI Target Relevance % Badge */}
                    <span className="font-bold text-emerald-900 bg-emerald-100 border border-emerald-300 px-2 py-0.5 rounded inline-flex items-center gap-1">
                      <Target className="w-3 h-3 text-emerald-700" />
                      {relScore}% Relevant
                    </span>

                    {/* Business Importance Rating Badge */}
                    {renderImportanceBadge(art.importance_rating)}

                    {/* Impact Sentiment Badge */}
                    {renderSentimentBadge(art.sentiment_tone)}

                    {/* Published Time */}
                    <span className="text-slate-500 flex items-center gap-1">
                      <Clock className="w-3 h-3 text-slate-400" />
                      {formatDate(art.published_at, art.publication_time_unavailable)}
                    </span>
                  </div>

                  {/* Article Title */}
                  <button
                    onClick={() => onSelectArticle(art)}
                    className="font-bold text-mongo-dark hover:text-mongo-forest text-left text-base leading-snug transition-colors block"
                  >
                    {art.title}
                  </button>

                  {/* AI Summary / Rationale Snippet */}
                  {art.ai_summary && (
                    <div className="mt-2 bg-emerald-50/70 border border-emerald-200/80 rounded-lg p-2.5 text-xs text-mongo-dark font-medium flex items-start gap-2">
                      <Sparkles className="w-4 h-4 text-mongo-forest shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold text-mongo-forest font-mono text-[11px] block uppercase tracking-wider mb-0.5">
                          AI Executive Summary
                        </span>
                        <p className="text-slate-700 leading-relaxed">{art.ai_summary}</p>
                      </div>
                    </div>
                  )}

                  {/* Description Snippet fallback */}
                  {!art.ai_summary && art.description && (
                    <p className="text-xs text-slate-600 mt-1.5 leading-relaxed line-clamp-2">
                      {art.description}
                    </p>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2 shrink-0 pt-1">
                  <button
                    onClick={() => onSelectArticle(art)}
                    className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-mono font-bold text-mongo-dark bg-slate-100 hover:bg-slate-200 border border-slate-300 rounded-lg transition-colors"
                  >
                    <Layers className="w-3.5 h-3.5 text-slate-600" />
                    <span>Inspect Metadata</span>
                  </button>

                  <a
                    href={art.url || art.canonical_url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1 px-3 py-1.5 text-xs font-mono font-bold text-mongo-green bg-mongo-forest hover:bg-[#00523a] rounded-lg transition-colors shadow-2xs cursor-pointer"
                  >
                    <span>Publisher Article</span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-mongo-green" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

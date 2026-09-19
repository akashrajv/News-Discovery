import React, { useState, useEffect } from 'react';
import {
  Newspaper,
  ExternalLink,
  Filter,
  CopyX,
  CheckCircle,
  Search,
  Layers,
  Clock,
  ArrowUpRight,
  Target,
  Sparkles,
  AlertTriangle,
  TrendingUp,
  ShieldAlert,
  User,
  Database,
  Brain,
  Loader2,
  Compass,
  X,
  Tag,
  Plus,
  Building2
} from 'lucide-react';
import { searchSemantic } from '../services/api';

export default function ArticleTable({
  articles,
  activeTargetFilter,
  onClearFilter,
  onSelectArticle,
  onCollectForCompany
}) {
  // Mode: 'feed' | 'semantic'
  const [activeMode, setActiveMode] = useState('feed');

  // Filter States
  const [filterCompany, setFilterCompany] = useState('ALL');
  const [activeKeywords, setActiveKeywords] = useState([]);
  const [newKeywordInput, setNewKeywordInput] = useState('');
  const [strictKeywordMatch, setStrictKeywordMatch] = useState(true);
  const [filterImportance, setFilterImportance] = useState('ALL');
  const [filterRelevance, setFilterRelevance] = useState(0);
  const [searchQuery, setSearchQuery] = useState('');

  // Semantic Search States
  const [semanticQuery, setSemanticQuery] = useState('');
  const [semanticResults, setSemanticResults] = useState(null);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [semanticError, setSemanticError] = useState(null);
  const [semanticMeta, setSemanticMeta] = useState(null);

  // Dynamically derive company cards from entered target companies and current search articles
  const companiesList = React.useMemo(() => {
    const list = [];

    // 1. Target companies explicitly entered by user in the search console
    if (activeTargetFilter?.entity && activeTargetFilter.entity.trim()) {
      const raw = activeTargetFilter.entity
        .split(',')
        .map(e => e.trim())
        .filter(e => e && e.toLowerCase() !== 'all' && e.toLowerCase() !== 'all companies');
      list.push(...raw);
    }

    // 2. Any target entities present in the articles returned for this search
    if (articles && articles.length > 0) {
      const fromArticles = articles
        .map(a => a.target_entity)
        .filter(e => e && e !== 'All Companies' && e !== 'All' && !list.some(x => x.toLowerCase() === e.toLowerCase()));
      list.push(...Array.from(new Set(fromArticles)));
    }

    if (list.length > 0) {
      return ['ALL', ...Array.from(new Set(list))];
    }

    return ['ALL'];
  }, [activeTargetFilter?.entity, articles]);

  const importanceLevels = ['ALL', 'CRITICAL', 'HIGH', 'MEDIUM'];
  const relevanceTiers = [
    { label: 'All Scores', min: 0 },
    { label: '≥ 60% Relevant', min: 60 },
    { label: '≥ 75% High', min: 75 },
    { label: '≥ 90% Peak', min: 90 },
  ];

  // Synchronize when activeTargetFilter is updated from the query console
  useEffect(() => {
    if (activeTargetFilter) {
      if (activeTargetFilter.entity && activeTargetFilter.entity.trim()) {
        const ent = activeTargetFilter.entity.trim();
        const entered = ent.split(',').map(e => e.trim()).filter(Boolean);
        // If single entity was entered (e.g. "Tesla"), select it directly
        if (entered.length === 1 && entered[0].toLowerCase() !== 'all' && entered[0].toLowerCase() !== 'all companies') {
          setFilterCompany(entered[0]);
        } else {
          setFilterCompany('ALL');
        }
      }
      if (activeTargetFilter.keywords && Array.isArray(activeTargetFilter.keywords)) {
        setActiveKeywords(activeTargetFilter.keywords.filter(Boolean));
        if (activeTargetFilter.keywords.length > 0) {
          setSemanticQuery(activeTargetFilter.keywords.join(' '));
        }
      }
    }
  }, [activeTargetFilter]);

  // Get count of matching articles for a company
  const getCompanyCount = (comp) => {
    if (!articles) return 0;
    if (comp === 'ALL') return articles.length;
    const compLower = comp.toLowerCase();
    const knownAliases = {
      'nvidia': ['nvidia', 'nvda', 'geforce', 'blackwell', 'hopper', 'cuda', 'jensen huang', 'rtx'],
      'tata motors': ['tata motors', 'tata motor', 'tata nexon', 'tata tiago', 'tata punch', 'tata curvv', 'jlr', 'jaguar land rover', 'tata ev'],
      'tesla': ['tesla', 'tsla', 'elon musk', 'cybercab', 'robotaxi', 'cybertruck', 'fsd', 'model 3', 'model y'],
      'apple': ['apple', 'aapl', 'iphone', 'macbook', 'ios', 'apple intelligence', 'tim cook'],
      'microsoft': ['microsoft', 'msft', 'azure', 'copilot', 'windows', 'satya nadella'],
      'openai': ['openai', 'open ai', 'chatgpt', 'sam altman'],
      'google': ['google', 'alphabet', 'gemini', 'deepmind', 'sundar pichai'],
      'amazon': ['amazon', 'aws', 'andy jassy', 'jeff bezos'],
      'meta': ['meta', 'facebook', 'instagram', 'zuckerberg', 'llama']
    }[compLower] || [compLower];

    return articles.filter(art => {
      const txt = `${art.target_entity || ''} ${art.title || ''} ${art.description || ''} ${art.content || ''}`.toLowerCase();
      return knownAliases.some(a => txt.includes(a));
    }).length;
  };

  if (!articles) return null;

  // Add a keyword filter tag
  const handleAddKeyword = (e) => {
    if (e) e.preventDefault();
    const clean = newKeywordInput.trim();
    if (clean && !activeKeywords.some(k => k.toLowerCase() === clean.toLowerCase())) {
      setActiveKeywords([...activeKeywords, clean]);
      setNewKeywordInput('');
    }
  };

  // Remove a keyword filter tag
  const handleRemoveKeyword = (kwToRemove) => {
    setActiveKeywords(activeKeywords.filter(k => k.toLowerCase() !== kwToRemove.toLowerCase()));
  };

  // Clear all target company and keyword focus filters
  const handleResetTargetFocus = () => {
    setFilterCompany('ALL');
    setActiveKeywords([]);
    setSearchQuery('');
    setFilterImportance('ALL');
    setFilterRelevance(0);
    if (onClearFilter) onClearFilter();
  };

  // Qdrant Semantic Vector Search
  const handleSemanticSearch = async (e) => {
    if (e) e.preventDefault();
    const q = semanticQuery.trim() || activeKeywords.join(' ');
    if (!q) return;

    setSemanticLoading(true);
    setSemanticError(null);
    try {
      const entity = filterCompany !== 'ALL' ? filterCompany : null;
      const resp = await searchSemantic(q, 15, 0.20, entity);
      setSemanticResults(resp.results || []);
      setSemanticMeta({
        query: resp.query,
        count: resp.total_found ?? resp.results?.length ?? 0,
        vectorEngine: resp.vector_engine,
      });
    } catch (err) {
      console.error('Semantic search error:', err);
      setSemanticError(err.response?.data?.detail || 'Semantic search failed. Ensure Qdrant service is active.');
    } finally {
      setSemanticLoading(false);
    }
  };

  const clearSemanticSearch = () => {
    setSemanticResults(null);
    setSemanticQuery('');
    setSemanticMeta(null);
    setSemanticError(null);
  };

  // Strict Filter: Article must match target company AND keyword entered
  const filteredArticles = articles.filter((art) => {
    const targetText = `${art.target_entity || ''} ${art.title || ''} ${art.description || ''} ${art.content || ''} ${art.source || ''}`.toLowerCase();
    
    // 1. Target Company Match
    let matchesCompany = filterCompany === 'ALL';
    if (!matchesCompany) {
      const compLower = filterCompany.toLowerCase();
      const aliases = {
        'nvidia': ['nvidia', 'nvda', 'geforce', 'blackwell', 'hopper', 'cuda', 'jensen huang', 'rtx'],
        'tata motors': ['tata motors', 'tata motor', 'tata nexon', 'tata tiago', 'tata punch', 'tata curvv', 'jlr', 'jaguar land rover', 'tata ev'],
        'tesla': ['tesla', 'tsla', 'elon musk', 'cybercab', 'robotaxi', 'cybertruck', 'fsd', 'model 3', 'model y'],
        'apple': ['apple', 'aapl', 'iphone', 'macbook', 'ios', 'apple intelligence', 'tim cook'],
        'microsoft': ['microsoft', 'msft', 'azure', 'copilot', 'windows', 'satya nadella']
      }[compLower] || [compLower];

      matchesCompany = aliases.some(alias => targetText.includes(alias));
    }

    // 2. Strict Keyword Match: When keywords are entered, article MUST match at least one keyword
    let matchesKeywords = true;
    if (strictKeywordMatch && activeKeywords && activeKeywords.length > 0) {
      const cleanKws = activeKeywords.map(k => k.toLowerCase().trim()).filter(Boolean);
      if (cleanKws.length > 0) {
        matchesKeywords = cleanKws.some(kw => targetText.includes(kw));
      }
    }

    // 3. Importance Rating Match
    const matchesImportance =
      filterImportance === 'ALL' ||
      (art.importance_rating && art.importance_rating.toUpperCase() === filterImportance.toUpperCase());

    // 4. Relevance Score Match
    const relScore = art.relevance_score != null ? art.relevance_score : 85.0;
    const matchesRelevance = relScore >= filterRelevance;

    // 5. Quick Search Text Match
    const matchesSearch =
      searchQuery === '' || targetText.includes(searchQuery.toLowerCase());

    return matchesCompany && matchesKeywords && matchesImportance && matchesSearch && matchesRelevance;
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

  const renderRelevanceBadge = (score) => {
    const s = score != null ? Math.round(score) : 85;
    if (s >= 80) {
      return (
        <span className="font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 font-mono text-[10px]">
          <Target className="w-3 h-3 text-emerald-600" />
          {s}% Relevant
        </span>
      );
    }
    if (s >= 60) {
      return (
        <span className="font-bold text-linkedin-blue bg-linkedin-light border border-linkedin-border px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 font-mono text-[10px]">
          <Target className="w-3 h-3 text-linkedin-blue" />
          {s}% Relevant
        </span>
      );
    }
    if (s >= 40) {
      return (
        <span className="font-bold text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 font-mono text-[10px]">
          <Target className="w-3 h-3 text-amber-600" />
          {s}% Relevant
        </span>
      );
    }
    return (
      <span className="font-bold text-slate-600 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 font-mono text-[10px]">
        <Target className="w-3 h-3 text-slate-400" />
        {s}% Low Match
      </span>
    );
  };

  const renderImportanceBadge = (rating) => {
    const r = (rating || 'MEDIUM').toUpperCase();
    if (r === 'CRITICAL') {
      return (
        <span className="inline-flex items-center gap-1 font-mono font-bold text-rose-800 bg-rose-50 border border-rose-200 px-2.5 py-0.5 rounded-full text-[10px]">
          <ShieldAlert className="w-3 h-3 text-rose-600" /> Critical Impact
        </span>
      );
    }
    if (r === 'HIGH') {
      return (
        <span className="inline-flex items-center gap-1 font-mono font-bold text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full text-[10px]">
          <TrendingUp className="w-3 h-3 text-amber-600" /> High Importance
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 font-mono font-bold text-slate-600 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full text-[10px]">
        Medium Importance
      </span>
    );
  };

  const renderSentimentBadge = (tone) => {
    if (!tone || tone === 'Neutral') return null;
    const isRisk = tone.includes('Risk') || tone.includes('Threat');
    return (
      <span className={`inline-flex items-center gap-1 font-mono font-bold px-2.5 py-0.5 rounded-full border text-[10px] ${
        isRisk ? 'text-rose-800 bg-rose-50 border-rose-200' : 'text-linkedin-blue bg-linkedin-light border-linkedin-border'
      }`}>
        <Sparkles className="w-3 h-3" /> {tone}
      </span>
    );
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs overflow-hidden mb-6">
      {/* Header & Tabs */}
      <div className="p-5 border-b border-slate-200 flex flex-col xl:flex-row xl:items-center justify-between gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Newspaper className="w-5 h-5 text-linkedin-blue" />
            <h3 className="font-bold text-slate-900 text-base font-sans">
              Target Company Intelligence Stream
            </h3>
            <span className="bg-linkedin-light text-linkedin-blue text-xs font-mono font-bold px-2.5 py-0.5 rounded-full border border-linkedin-border">
              {activeMode === 'semantic' && semanticResults ? semanticResults.length : filteredArticles.length} Articles
            </span>
          </div>
          <p className="text-xs text-slate-500 mt-0.5 font-sans">
            Displaying only articles similar to target company & entered keywords
          </p>
        </div>

        {/* Discovery Mode Switcher */}
        <div className="flex items-center bg-[#F3F2F0] p-1 rounded-xl border border-slate-200 text-xs font-sans">
          <button
            onClick={() => setActiveMode('feed')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
              activeMode === 'feed'
                ? 'bg-white text-slate-900 shadow-xs'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <Layers className="w-3.5 h-3.5 text-linkedin-blue" />
            <span>Target Stream</span>
          </button>
          <button
            onClick={() => setActiveMode('semantic')}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg font-bold transition-all cursor-pointer ${
              activeMode === 'semantic'
                ? 'bg-gradient-to-r from-purple-600 to-indigo-600 text-white shadow-xs'
                : 'text-slate-600 hover:text-purple-600'
            }`}
          >
            <Compass className="w-3.5 h-3.5" />
            <span>Qdrant Vector Discovery</span>
          </button>
        </div>
      </div>

      {/* Target Company & Keywords Active Filter Focus Banner */}
      {(filterCompany !== 'ALL' || activeKeywords.length > 0) && (
        <div className="bg-[#F3F8FD] border-b border-linkedin-border px-5 py-3 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2 text-xs">
            <span className="font-bold text-slate-700 font-sans flex items-center gap-1">
              <Filter className="w-3.5 h-3.5 text-linkedin-blue" />
              <span>Active Target Focus:</span>
            </span>

            {/* Target Company Tag */}
            {filterCompany !== 'ALL' ? (
              <span className="inline-flex items-center gap-1 bg-linkedin-blue text-white font-bold px-2.5 py-1 rounded-full text-xs shadow-2xs font-sans">
                <span>Company: {filterCompany}</span>
                <button
                  type="button"
                  onClick={() => setFilterCompany('ALL')}
                  className="hover:bg-white/20 rounded-full p-0.5 transition-colors cursor-pointer"
                  title="Remove company filter"
                >
                  <X className="w-3 h-3" />
                </button>
              </span>
            ) : (
              <span className="text-slate-500 font-medium">All Companies &bull;</span>
            )}

            {/* Active Keywords Tags */}
            {activeKeywords.length > 0 && (
              <div className="flex flex-wrap items-center gap-1.5">
                <span className="text-slate-600 text-[11px] font-bold">Keywords:</span>
                {activeKeywords.map((kw, i) => (
                  <span
                    key={i}
                    className="inline-flex items-center gap-1 bg-white border border-slate-300 text-slate-800 font-semibold px-2.5 py-0.5 rounded-full text-xs shadow-2xs font-sans"
                  >
                    <Tag className="w-3 h-3 text-linkedin-blue" />
                    <span>{kw}</span>
                    <button
                      type="button"
                      onClick={() => handleRemoveKeyword(kw)}
                      className="hover:text-rose-600 text-slate-400 p-0.5 transition-colors cursor-pointer"
                      title={`Remove keyword ${kw}`}
                    >
                      <X className="w-3 h-3" />
                    </button>
                  </span>
                ))}
              </div>
            )}

            {/* Add New Keyword Inline */}
            <form onSubmit={handleAddKeyword} className="inline-flex items-center">
              <input
                type="text"
                placeholder="+ Add keyword..."
                value={newKeywordInput}
                onChange={(e) => setNewKeywordInput(e.target.value)}
                className="text-[11px] px-2.5 py-0.5 bg-white border border-slate-300 rounded-full focus:outline-none focus:ring-1 focus:ring-linkedin-blue text-slate-800 w-28"
              />
            </form>
          </div>

          <div className="flex items-center gap-2 text-xs shrink-0">
            {/* Strict Keyword Toggle */}
            <label className="inline-flex items-center gap-1.5 cursor-pointer text-[11px] font-semibold text-slate-600 select-none">
              <input
                type="checkbox"
                checked={strictKeywordMatch}
                onChange={(e) => setStrictKeywordMatch(e.target.checked)}
                className="rounded text-linkedin-blue focus:ring-linkedin-blue cursor-pointer"
              />
              <span>Strict Keyword Match</span>
            </label>

            <span className="text-slate-300">|</span>

            <button
              onClick={handleResetTargetFocus}
              className="text-xs font-semibold text-slate-500 hover:text-rose-600 underline cursor-pointer"
            >
              Clear Focus
            </button>
          </div>
        </div>
      )}

      {/* Mode 1: Qdrant Vector Semantic Discovery Panel */}
      {activeMode === 'semantic' && (
        <div className="p-5 bg-gradient-to-r from-purple-50/70 via-indigo-50/40 to-slate-50 border-b border-purple-100">
          <div className="max-w-4xl">
            <div className="flex items-center gap-2 mb-2">
              <span className="inline-flex items-center gap-1 text-[11px] font-mono font-bold text-purple-800 bg-purple-100 border border-purple-200 px-2.5 py-0.5 rounded-full">
                <Database className="w-3 h-3 text-purple-600" />
                Qdrant Vector Search
              </span>
              <span className="text-xs text-slate-600 font-sans">
                Target vector search scoped to company & semantic concept:
              </span>
            </div>

            <form onSubmit={handleSemanticSearch} className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2.5">
              <div className="relative flex-1">
                <input
                  type="text"
                  placeholder="e.g. 'semiconductor packaging bottlenecks', 'robotaxi safety approval', 'cloud margin expansion'..."
                  value={semanticQuery}
                  onChange={(e) => setSemanticQuery(e.target.value)}
                  className="w-full text-xs pl-9 pr-9 py-2.5 border border-purple-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-purple-500/20 focus:border-purple-500 bg-white font-medium text-slate-900 shadow-xs"
                />
                <Search className="w-4 h-4 text-purple-500 absolute left-3 top-3" />
                {semanticQuery && (
                  <button
                    type="button"
                    onClick={() => setSemanticQuery('')}
                    className="absolute right-3 top-3 text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>

              {/* Company scope selector for semantic search */}
              <select
                value={filterCompany}
                onChange={(e) => setFilterCompany(e.target.value)}
                className="text-xs px-3 py-2.5 bg-white border border-purple-200 rounded-xl font-bold text-slate-700 focus:outline-none focus:ring-2 focus:ring-purple-500/20 cursor-pointer"
              >
                {companiesList.map((comp) => (
                  <option key={comp} value={comp}>
                    {comp === 'ALL' ? 'All Target Entities' : comp}
                  </option>
                ))}
              </select>

              <button
                type="submit"
                disabled={semanticLoading || !semanticQuery.trim()}
                className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-purple-600 hover:bg-purple-700 text-white text-xs font-bold font-sans rounded-xl shadow-xs transition-colors disabled:opacity-50 cursor-pointer shrink-0"
              >
                {semanticLoading ? (
                  <Loader2 className="w-4 h-4 animate-spin" />
                ) : (
                  <Sparkles className="w-4 h-4" />
                )}
                <span>Search Vector Space</span>
              </button>

              {semanticResults && (
                <button
                  type="button"
                  onClick={clearSemanticSearch}
                  className="px-3 py-2 text-xs font-sans font-semibold text-slate-600 bg-white hover:bg-slate-100 border border-slate-200 rounded-xl transition-colors cursor-pointer shrink-0"
                >
                  Clear Results
                </button>
              )}
            </form>

            {semanticError && (
              <div className="mt-3 text-xs font-mono text-rose-700 bg-rose-50 border border-rose-200 rounded-lg p-2.5">
                {semanticError}
              </div>
            )}

            {semanticMeta && (
              <div className="mt-3 flex items-center gap-3 text-xs font-mono text-purple-900 bg-purple-100/60 border border-purple-200/80 rounded-lg px-3 py-1.5">
                <span className="font-bold">Vector Match:</span>
                <span>Found {semanticMeta.count} semantically matching articles in Qdrant</span>
                <span className="text-purple-400">|</span>
                <span>Engine: {semanticMeta.vectorEngine}</span>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Mode 2: Standard Filter Controls */}
      {activeMode === 'feed' && (
        <div className="p-4 bg-[#FAFAFA] border-b border-slate-200 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2.5">
            {/* Quick Search */}
            <div className="relative">
              <input
                type="text"
                placeholder="Search headline / content..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="text-xs pl-8 pr-3 py-1.5 border border-slate-200 rounded-full focus:outline-none focus:ring-2 focus:ring-linkedin-blue/20 focus:border-linkedin-blue bg-white font-medium text-slate-900 w-44 sm:w-52 transition-colors"
              />
              <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2.5" />
            </div>

            {/* Relevance Filter */}
            <div className="flex items-center space-x-1 bg-white p-1 rounded-full border border-slate-200 text-xs font-sans">
              <span className="text-[10px] font-bold text-slate-500 px-2 hidden sm:inline uppercase">Score:</span>
              {relevanceTiers.map((tier) => (
                <button
                  key={tier.min}
                  onClick={() => setFilterRelevance(tier.min)}
                  className={`px-2.5 py-1 rounded-full font-bold transition-all cursor-pointer whitespace-nowrap ${
                    filterRelevance === tier.min
                      ? 'bg-linkedin-blue text-white shadow-xs'
                      : 'text-slate-600 hover:text-linkedin-blue hover:bg-slate-100'
                  }`}
                >
                  {tier.label}
                </button>
              ))}
            </div>

            {/* Importance Filter */}
            <div className="flex items-center space-x-1 bg-white p-1 rounded-full border border-slate-200 text-xs font-sans">
              {importanceLevels.map((imp) => (
                <button
                  key={imp}
                  onClick={() => setFilterImportance(imp)}
                  className={`px-2.5 py-1 rounded-full font-bold transition-all cursor-pointer ${
                    filterImportance === imp
                      ? 'bg-slate-900 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  {imp}
                </button>
              ))}
            </div>
          </div>

          {/* Dynamic Target Company Cards */}
          {companiesList.length > 1 && (
            <div className="flex items-center space-x-1.5 bg-white p-1 rounded-full border border-slate-200 text-xs font-sans overflow-x-auto max-w-full">
              {companiesList.map((comp) => {
                const isSelected = filterCompany.toLowerCase() === comp.toLowerCase() || (comp === 'ALL' && filterCompany === 'ALL');
                const count = getCompanyCount(comp);
                return (
                  <button
                    key={comp}
                    onClick={() => setFilterCompany(comp)}
                    className={`px-3 py-1 rounded-full font-bold transition-all whitespace-nowrap cursor-pointer flex items-center gap-1.5 ${
                      isSelected
                        ? 'bg-linkedin-blue text-white shadow-xs'
                        : 'text-slate-600 hover:text-linkedin-blue hover:bg-slate-100'
                    }`}
                  >
                    <span>{comp === 'ALL' ? 'All Target Companies' : comp}</span>
                    <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded-full ${
                      isSelected ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-600'
                    }`}>
                      {count}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Articles Stream View */}
      {activeMode === 'semantic' && semanticResults ? (
        // Qdrant Semantic Results
        semanticResults.length === 0 ? (
          <div className="p-12 text-center text-slate-500">
            <Compass className="w-10 h-10 mx-auto text-purple-300 mb-2" />
            <p className="font-bold text-slate-800 font-sans">No semantically similar articles found in Qdrant.</p>
            <p className="text-xs text-slate-500 mt-1 font-sans">
              Try broadening your vector query or clearing company filters.
            </p>
          </div>
        ) : (
          <div className="divide-y divide-purple-100">
            {semanticResults.map((item) => {
              const art = item.article;
              const simPercent = item.score_percentage || Math.round((item.similarity_score ?? item.score ?? 0.8) * 100);
              return (
                <div
                  key={art.id}
                  className="p-5 hover:bg-purple-50/40 transition-colors flex flex-col md:flex-row md:items-start justify-between gap-4"
                >
                  <div className="flex-1">
                    <div className="flex flex-wrap items-center gap-2 mb-2 font-mono text-[11px]">
                      {/* Qdrant Cosine Similarity Score Badge */}
                      <span className="font-bold text-purple-900 bg-purple-100 border border-purple-300 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 font-mono text-[10px]">
                        <Database className="w-3 h-3 text-purple-700" />
                        {simPercent}% Vector Match
                      </span>

                      {/* DeepSeek-R1 Indicator */}
                      {art.reasoning_trace && (
                        <span className="font-bold text-indigo-900 bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 font-mono text-[10px]">
                          <Brain className="w-3 h-3 text-indigo-600" />
                          DeepSeek-R1 &lt;think&gt;
                        </span>
                      )}

                      {/* Source Badge */}
                      <span className="font-bold text-slate-800 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full">
                        {art.source}
                      </span>

                      {/* Target Entity */}
                      {art.target_entity && (
                        <span className="font-semibold text-slate-600 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full text-[10px]">
                          {art.target_entity}
                        </span>
                      )}

                      {/* Published Time */}
                      <span className="text-slate-500 flex items-center gap-1 font-sans">
                        <Clock className="w-3 h-3 text-slate-400" />
                        {formatDate(art.published_at, art.publication_time_unavailable)}
                      </span>
                    </div>

                    {/* Article Title */}
                    <button
                      onClick={() => onSelectArticle(art)}
                      className="font-bold text-slate-900 hover:text-purple-700 text-left text-base leading-snug transition-colors block font-sans cursor-pointer"
                    >
                      {art.title}
                    </button>

                    {/* 3-Line AI Summary */}
                    {art.ai_summary && (
                      <div className="mt-2.5 bg-white border border-purple-200 rounded-xl p-3 text-xs text-slate-800 font-sans flex items-start gap-2.5 shadow-xs">
                        <Sparkles className="w-4 h-4 text-purple-600 shrink-0 mt-0.5" />
                        <div className="w-full">
                          <span className="font-bold text-purple-800 font-sans text-[11px] block uppercase tracking-wider mb-0.5">
                            DeepSeek-R1 Executive Takeaway
                          </span>
                          <p className="text-slate-700 leading-relaxed font-sans whitespace-pre-line">{art.ai_summary}</p>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 shrink-0 pt-1">
                    <button
                      onClick={() => onSelectArticle(art)}
                      className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-sans font-semibold text-purple-900 bg-purple-50 hover:bg-purple-100 border border-purple-200 rounded-full transition-colors cursor-pointer shadow-xs"
                    >
                      <Brain className="w-3.5 h-3.5 text-purple-600" />
                      <span>Inspect Reasoning</span>
                    </button>

                    <a
                      href={art.url || art.canonical_url || '#'}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1.5 px-4 py-1.5 text-xs font-sans font-bold text-white bg-purple-600 hover:bg-purple-700 rounded-full transition-colors shadow-xs cursor-pointer"
                    >
                      <span>Publisher</span>
                      <ArrowUpRight className="w-3.5 h-3.5 text-white" />
                    </a>
                  </div>
                </div>
              );
            })}
          </div>
        )
      ) : filteredArticles.length === 0 ? (
        // Empty State
        <div className="p-12 text-center text-slate-500">
          <Target className="w-10 h-10 mx-auto text-slate-300 mb-2" />
          <p className="font-bold text-slate-800 font-sans">
            No articles match both the target company and entered keywords.
          </p>
          <p className="text-xs text-slate-500 mt-1 font-sans max-w-md mx-auto">
            {activeKeywords.length > 0 && filterCompany !== 'ALL'
              ? `No cached news found for ${filterCompany} containing keywords: ${activeKeywords.join(', ')}.`
              : activeKeywords.length > 0
              ? `No articles match keywords: ${activeKeywords.join(', ')}.`
              : filterCompany !== 'ALL'
              ? `No articles match target company ${filterCompany}.`
              : 'Try broadening your search or running a new discovery request.'}
          </p>
          <div className="flex items-center justify-center gap-2 mt-4">
            {(filterCompany !== 'ALL' || activeKeywords.length > 0 || searchQuery || filterRelevance > 0) && (
              <button
                onClick={handleResetTargetFocus}
                className="px-4 py-2 text-xs font-sans font-semibold text-slate-700 bg-slate-100 hover:bg-slate-200 rounded-full transition-colors cursor-pointer"
              >
                Reset Target & Keyword Filters
              </button>
            )}
            {filterCompany !== 'ALL' && onCollectForCompany && (
              <button
                onClick={() => onCollectForCompany(filterCompany)}
                className="inline-flex items-center space-x-1.5 px-5 py-2 text-xs font-sans font-bold text-white bg-linkedin-blue hover:bg-linkedin-hover rounded-full transition-colors shadow-xs cursor-pointer"
              >
                <Sparkles className="w-4 h-4 text-white" />
                <span>Collect News for {filterCompany}</span>
              </button>
            )}
          </div>
        </div>
      ) : (
        // Feed Stream Cards List
        <div className="divide-y divide-slate-100">
          {filteredArticles.map((art) => {
            return (
              <div
                key={art.id}
                className="p-5 hover:bg-[#F3F8FD]/50 transition-colors flex flex-col md:flex-row md:items-start justify-between gap-4"
              >
                {/* Content Main */}
                <div className="flex-1">
                  <div className="flex flex-wrap items-center gap-2 mb-2 font-mono text-[11px]">
                    {/* Source Badge */}
                    <span className="font-bold text-slate-800 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full">
                      {art.source}
                    </span>

                    {/* Author Badge */}
                    {art.author && (
                      <span className="font-semibold text-slate-600 bg-slate-100 border border-slate-200 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 font-sans">
                        <User className="w-3 h-3 text-slate-400" />
                        By {art.author}
                      </span>
                    )}

                    {/* DeepSeek-R1 Reasoning Badge */}
                    {art.reasoning_trace && (
                      <span className="font-bold text-indigo-900 bg-indigo-50 border border-indigo-200 px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 font-mono text-[10px]">
                        <Brain className="w-3 h-3 text-indigo-600" />
                        DeepSeek-R1 &lt;think&gt;
                      </span>
                    )}

                    {/* AI Target Relevance % Badge */}
                    {renderRelevanceBadge(art.relevance_score)}

                    {/* Business Importance Rating Badge */}
                    {renderImportanceBadge(art.importance_rating)}

                    {/* Impact Sentiment Badge */}
                    {renderSentimentBadge(art.sentiment_tone)}

                    {/* Published Time */}
                    <span className="text-slate-500 flex items-center gap-1 font-sans">
                      <Clock className="w-3 h-3 text-slate-400" />
                      {formatDate(art.published_at, art.publication_time_unavailable)}
                    </span>
                  </div>

                  {/* Article Title */}
                  <button
                    onClick={() => onSelectArticle(art)}
                    className="font-bold text-slate-900 hover:text-linkedin-blue text-left text-base leading-snug transition-colors block font-sans cursor-pointer"
                  >
                    {art.title}
                  </button>

                  {/* 3-Line AI Executive Summary */}
                  {art.ai_summary && (
                    <div className="mt-2.5 bg-[#F3F8FD] border border-linkedin-border rounded-xl p-3 text-xs text-slate-800 font-sans flex items-start gap-2.5">
                      <Sparkles className="w-4 h-4 text-linkedin-blue shrink-0 mt-0.5" />
                      <div className="w-full">
                        <span className="font-bold text-linkedin-blue font-sans text-[11px] block uppercase tracking-wider mb-0.5">
                          AI Executive Summary
                        </span>
                        <p className="text-slate-700 leading-relaxed font-sans whitespace-pre-line">{art.ai_summary}</p>
                      </div>
                    </div>
                  )}

                  {/* Description Snippet fallback */}
                  {!art.ai_summary && art.description && (
                    <p className="text-xs text-slate-600 mt-1.5 leading-relaxed line-clamp-2 font-sans">
                      {art.description}
                    </p>
                  )}
                </div>

                {/* Action Buttons */}
                <div className="flex items-center space-x-2 shrink-0 pt-1">
                  <button
                    onClick={() => onSelectArticle(art)}
                    className="inline-flex items-center space-x-1.5 px-3.5 py-1.5 text-xs font-sans font-semibold text-slate-700 bg-white hover:bg-slate-50 border border-slate-300 rounded-full transition-colors cursor-pointer shadow-xs"
                  >
                    <Layers className="w-3.5 h-3.5 text-slate-500" />
                    <span>Inspect</span>
                  </button>

                  <a
                    href={art.url || art.canonical_url || '#'}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center space-x-1.5 px-4 py-1.5 text-xs font-sans font-bold text-white bg-linkedin-blue hover:bg-linkedin-hover rounded-full transition-colors shadow-xs cursor-pointer"
                  >
                    <span>Publisher</span>
                    <ArrowUpRight className="w-3.5 h-3.5 text-white" />
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

import React, { useState } from 'react';
import { X, ExternalLink, Hash, Layers, ArrowUpRight, Terminal, Sparkles, Target, ShieldAlert, TrendingUp, User, BrainCircuit, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { fetchSimilarArticles } from '../services/api';

export default function ArticleDetailModal({ article, onClose }) {
  if (!article) return null;

  const [showReasoning, setShowReasoning] = useState(false);
  const [similarArticles, setSimilarArticles] = useState([]);
  const [loadingSimilar, setLoadingSimilar] = useState(false);
  const [similarError, setSimilarError] = useState(null);

  const articleUrl = article.url || article.canonical_url || '#';
  const relScore = article.relevance_score != null ? Math.round(article.relevance_score) : 85;

  const handleLoadSimilar = async () => {
    setLoadingSimilar(true);
    setSimilarError(null);
    try {
      const data = await fetchSimilarArticles(article.id, 4);
      setSimilarArticles(data || []);
    } catch (err) {
      setSimilarError('Could not find similar articles in vector index.');
    } finally {
      setLoadingSimilar(false);
    }
  };

  const getRelevanceStyle = (s) => {
    if (s >= 80) return 'bg-emerald-50 text-emerald-800 border-emerald-200';
    if (s >= 60) return 'bg-linkedin-light text-linkedin-blue border-linkedin-border';
    if (s >= 40) return 'bg-amber-50 text-amber-800 border-amber-200';
    return 'bg-slate-100 text-slate-600 border-slate-200';
  };

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-slate-200 max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-5 border-b border-slate-200 flex items-start justify-between bg-[#F3F8FD] rounded-t-xl">
          <div className="pr-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider bg-slate-100 text-slate-700 border border-slate-200 px-2.5 py-0.5 rounded-full">
                {article.collection_method} connector
              </span>
              <span className={`text-[10px] font-mono font-bold uppercase tracking-wider border px-2.5 py-0.5 rounded-full inline-flex items-center gap-1 ${getRelevanceStyle(relScore)}`}>
                <Target className="w-3 h-3" /> {relScore}% Relevant
              </span>
            </div>

            <h3 className="font-bold text-slate-900 text-base mt-2 leading-snug font-sans">
              <a
                href={articleUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-linkedin-blue hover:underline inline-flex items-center gap-1.5"
              >
                <span>{article.title}</span>
                <ExternalLink className="w-4 h-4 text-slate-400 shrink-0 inline" />
              </a>
            </h3>
            <p className="text-xs text-slate-500 mt-1 font-sans flex flex-wrap items-center gap-3">
              <span>Source: <span className="font-bold text-slate-800">{article.source}</span></span>
              {article.author && (
                <span className="flex items-center gap-1">
                  <User className="w-3 h-3 text-slate-400" />
                  Author: <span className="font-bold text-slate-800">{article.author}</span>
                </span>
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-full hover:bg-slate-200 transition-colors shrink-0 cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4">
          {/* AI Semantic Intelligence Breakdown */}
          <div className="bg-[#F3F8FD] border border-linkedin-border rounded-xl p-4 space-y-3">
            <h4 className="font-sans font-bold text-linkedin-blue uppercase text-xs tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-linkedin-blue" /> AI Target Intelligence & Business Importance Analysis
            </h4>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs">
              <div className="bg-white p-2.5 rounded-lg border border-linkedin-border/60">
                <span className="text-slate-400 text-[10px] block uppercase font-sans">Target Entity</span>
                <span className="font-bold text-slate-900 font-sans">{article.target_entity || 'Target Company'}</span>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-linkedin-border/60">
                <span className="text-slate-400 text-[10px] block uppercase font-sans">Target Relevance</span>
                <span className="font-bold text-linkedin-blue">{relScore}% Match</span>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-linkedin-border/60">
                <span className="text-slate-400 text-[10px] block uppercase font-sans">Business Impact</span>
                <span className="font-bold text-slate-900 font-sans">{article.importance_rating || 'MEDIUM'}</span>
              </div>
              <div className="bg-white p-2.5 rounded-lg border border-linkedin-border/60">
                <span className="text-slate-400 text-[10px] block uppercase font-sans">Sentiment Tone</span>
                <span className="font-bold text-slate-800 font-sans">{article.sentiment_tone || 'Neutral'}</span>
              </div>
            </div>

            {article.ai_summary && (
              <div className="bg-white p-3 rounded-lg border border-linkedin-border text-xs leading-relaxed text-slate-800 font-sans">
                <span className="font-bold text-linkedin-blue font-sans text-[11px] block uppercase mb-1">
                  Executive Rationale
                </span>
                <p className="whitespace-pre-line leading-relaxed">{article.ai_summary}</p>
              </div>
            )}

            {/* DeepSeek-R1 Cognitive Reasoning Chain (<think>) */}
            {article.reasoning_trace && (
              <div className="bg-purple-50/70 border border-purple-200 rounded-lg p-3 text-xs font-sans">
                <button
                  type="button"
                  onClick={() => setShowReasoning(!showReasoning)}
                  className="w-full flex items-center justify-between text-purple-900 font-bold cursor-pointer"
                >
                  <span className="flex items-center gap-1.5">
                    <BrainCircuit className="w-4 h-4 text-purple-600" />
                    DeepSeek-R1 Cognitive Reasoning Chain (&lt;think&gt;)
                  </span>
                  {showReasoning ? <ChevronUp className="w-4 h-4 text-purple-600" /> : <ChevronDown className="w-4 h-4 text-purple-600" />}
                </button>
                {showReasoning && (
                  <div className="mt-2.5 pt-2.5 border-t border-purple-200 font-mono text-[11px] text-purple-950 whitespace-pre-line leading-relaxed bg-white/90 p-3 rounded-lg border border-purple-100 shadow-2xs">
                    {article.reasoning_trace}
                  </div>
                )}
              </div>
            )}
          </div>

          {/* Qdrant Vector Semantic Discovery: Similar Articles */}
          <div className="bg-emerald-50/50 border border-emerald-200 rounded-xl p-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div className="flex items-center gap-2">
                <Target className="w-4 h-4 text-emerald-700" />
                <h4 className="font-sans font-bold text-emerald-950 uppercase text-xs tracking-wider">
                  Qdrant Semantic Vector Discovery
                </h4>
              </div>
              <button
                type="button"
                onClick={handleLoadSimilar}
                disabled={loadingSimilar}
                className="text-xs font-sans font-bold px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full transition-all cursor-pointer inline-flex items-center gap-1.5 shadow-2xs self-start sm:self-auto"
              >
                {loadingSimilar ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Sparkles className="w-3.5 h-3.5" />}
                <span>Find Semantically Similar</span>
              </button>
            </div>

            {similarArticles.length > 0 && (
              <div className="mt-3 space-y-2">
                <span className="text-[11px] font-bold text-emerald-800 uppercase block font-mono">
                  Nearest Vector Neighbors in Qdrant:
                </span>
                {similarArticles.map((item, idx) => (
                  <div key={idx} className="bg-white p-2.5 rounded-lg border border-emerald-200 flex items-center justify-between text-xs shadow-2xs hover:border-emerald-400 transition-colors">
                    <div className="pr-3 flex-1 min-w-0">
                      <span className="font-bold text-slate-900 block font-sans truncate">{item.article.title}</span>
                      <span className="text-[10px] text-slate-500 font-sans">{item.article.source} &bull; {item.article.target_entity}</span>
                    </div>
                    <span className="shrink-0 font-mono font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded-full text-[10px]">
                      {item.score_percentage}% Similarity
                    </span>
                  </div>
                ))}
              </div>
            )}
            {similarError && <p className="text-xs text-rose-600 mt-2 font-sans">{similarError}</p>}
          </div>

          {/* Description */}
          <div>
            <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1 font-sans">
              Description Snippet
            </h4>
            <div className="text-xs text-slate-800 bg-[#F3F8FD]/50 p-3 rounded-lg border border-slate-200 leading-relaxed font-sans">
              {article.description || <span className="text-slate-400 italic">No description provided in feed.</span>}
            </div>
          </div>

          {/* Full Content if available */}
          {article.content && (
            <div>
              <h4 className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-1 font-sans">
                Raw Excerpt
              </h4>
              <p className="text-xs text-slate-700 bg-[#F3F8FD]/50 p-3 rounded-lg border border-slate-200 font-mono">
                {article.content}
              </p>
            </div>
          )}

          {/* MongoDB Atlas Style Document Inspector */}
          <div className="bg-[#1D2226] text-slate-200 p-4 rounded-xl text-xs space-y-2 font-mono">
            <h4 className="font-sans font-bold text-sky-400 uppercase text-[11px] tracking-wider mb-2 flex items-center gap-1.5 border-b border-slate-700 pb-2">
              <Terminal className="w-4 h-4 text-sky-400" /> Document Metadata
            </h4>

            <div className="grid grid-cols-1 gap-2">
              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">_id:</span>
                <span className="text-sky-300 font-bold">{article.id}</span>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">author:</span>
                <span className="text-slate-200 font-bold">{article.author || 'N/A (Unspecified)'}</span>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-1 items-center">
                <span className="text-slate-400">canonical_url:</span>
                {articleUrl !== '#' ? (
                  <a
                    href={articleUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sky-400 hover:underline truncate max-w-xs inline-flex items-center gap-1"
                    title={articleUrl}
                  >
                    <span className="truncate">{article.canonical_url || article.url}</span>
                    <ExternalLink className="w-3 h-3 shrink-0" />
                  </a>
                ) : (
                  <span className="text-slate-300 truncate max-w-xs">N/A</span>
                )}
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">relevance_score:</span>
                <span className="text-sky-300 font-bold">{article.relevance_score != null ? `${article.relevance_score}%` : 'N/A'}</span>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">importance_rating:</span>
                <span className="text-amber-300 font-bold">{article.importance_rating || 'MEDIUM'}</span>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">normalized_title:</span>
                <span className="text-slate-300 truncate max-w-xs">{article.normalized_title || 'N/A'}</span>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">content_hash (MD5):</span>
                <span className="text-amber-300 font-bold">{article.content_hash || 'N/A'}</span>
              </div>

              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">published_at:</span>
                <span className="text-slate-200">
                  {article.publication_time_unavailable
                    ? 'UNAVAILABLE IN FEED'
                    : new Date(article.published_at).toUTCString()}
                </span>
              </div>

              <div className="flex justify-between">
                <span className="text-slate-400">collected_at:</span>
                <span className="text-slate-200">{new Date(article.collected_at).toUTCString()}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-4 bg-[#F3F8FD] border-t border-slate-200 rounded-b-xl flex justify-between items-center">
          <button
            onClick={onClose}
            className="px-5 py-2 text-xs font-sans font-semibold text-slate-700 bg-white border border-slate-300 rounded-full hover:bg-slate-50 transition-colors cursor-pointer shadow-xs"
          >
            Close Inspector
          </button>
          <a
            href={articleUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1.5 px-5 py-2 text-xs font-sans font-bold text-white bg-linkedin-blue hover:bg-linkedin-hover rounded-full transition-colors shadow-xs cursor-pointer"
          >
            <span>Open Publisher Article</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-white" />
          </a>
        </div>
      </div>
    </div>
  );
}

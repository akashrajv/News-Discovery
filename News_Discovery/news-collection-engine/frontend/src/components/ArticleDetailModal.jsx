import React from 'react';
import { X, ExternalLink, Hash, Layers, ArrowUpRight, Terminal, Sparkles, Target, ShieldAlert, TrendingUp, User } from 'lucide-react';

export default function ArticleDetailModal({ article, onClose }) {
  if (!article) return null;

  const articleUrl = article.url || article.canonical_url || '#';
  const relScore = article.relevance_score != null ? Math.round(article.relevance_score) : 85;

  return (
    <div className="fixed inset-0 z-50 bg-slate-900/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white rounded-xl shadow-2xl border border-mongo-border max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-5 border-b border-mongo-border flex items-start justify-between bg-mongo-slate rounded-t-xl">
          <div className="pr-4">
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-100 text-mongo-forest border border-emerald-300 px-2 py-0.5 rounded">
                {article.collection_method} connector
              </span>
              <span className="text-[10px] font-mono font-bold uppercase tracking-wider bg-emerald-50 text-emerald-800 border border-emerald-300 px-2 py-0.5 rounded inline-flex items-center gap-1">
                <Target className="w-3 h-3 text-emerald-600" /> {relScore}% Relevant
              </span>
            </div>

            <h3 className="font-bold text-mongo-dark text-base mt-2 leading-snug font-sans">
              <a
                href={articleUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-mongo-forest hover:underline inline-flex items-center gap-1.5"
              >
                <span>{article.title}</span>
                <ExternalLink className="w-4 h-4 text-slate-400 shrink-0 inline" />
              </a>
            </h3>
            <p className="text-xs text-slate-500 mt-1 font-mono flex flex-wrap items-center gap-3">
              <span>Source: <span className="font-bold text-mongo-dark">{article.source}</span></span>
              {article.author && (
                <span className="flex items-center gap-1">
                  <User className="w-3 h-3 text-slate-400" />
                  Author: <span className="font-bold text-mongo-dark">{article.author}</span>
                </span>
              )}
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-slate-400 hover:text-slate-600 p-1.5 rounded-lg hover:bg-slate-200 transition-colors shrink-0"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content Body */}
        <div className="p-5 space-y-4">
          {/* AI Semantic Intelligence Breakdown */}
          <div className="bg-gradient-to-br from-emerald-50 to-teal-50 border border-emerald-200 rounded-xl p-4 space-y-3">
            <h4 className="font-mono font-bold text-mongo-forest uppercase text-xs tracking-wider flex items-center gap-1.5">
              <Sparkles className="w-4 h-4 text-mongo-forest" /> AI Target Intelligence & Business Importance Analysis
            </h4>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 font-mono text-xs">
              <div className="bg-white/80 p-2 rounded border border-emerald-100">
                <span className="text-slate-400 text-[10px] block uppercase">Target Entity</span>
                <span className="font-bold text-mongo-dark">{article.target_entity || 'Target Company'}</span>
              </div>
              <div className="bg-white/80 p-2 rounded border border-emerald-100">
                <span className="text-slate-400 text-[10px] block uppercase">Target Relevance</span>
                <span className="font-bold text-emerald-800">{relScore}% Match</span>
              </div>
              <div className="bg-white/80 p-2 rounded border border-emerald-100">
                <span className="text-slate-400 text-[10px] block uppercase">Business Impact</span>
                <span className="font-bold text-slate-900">{article.importance_rating || 'MEDIUM'}</span>
              </div>
              <div className="bg-white/80 p-2 rounded border border-emerald-100">
                <span className="text-slate-400 text-[10px] block uppercase">Sentiment Tone</span>
                <span className="font-bold text-slate-800">{article.sentiment_tone || 'Neutral'}</span>
              </div>
            </div>

            {article.ai_summary && (
              <div className="bg-white/90 p-3 rounded-lg border border-emerald-200 text-xs leading-relaxed text-slate-800">
                <span className="font-bold text-mongo-forest font-mono text-[11px] block uppercase mb-1">
                  Executive Rationale
                </span>
                <p>{article.ai_summary}</p>
              </div>
            )}
          </div>

          {/* Description */}
          <div>
            <h4 className="text-[11px] font-bold text-mongo-subtle uppercase tracking-wider mb-1 font-mono">
              Description Snippet
            </h4>
            <div className="text-xs text-slate-800 bg-mongo-slate p-3 rounded-lg border border-mongo-border leading-relaxed font-sans">
              {article.description || <span className="text-slate-400 italic">No description provided in feed.</span>}
            </div>
          </div>

          {/* Full Content if available */}
          {article.content && (
            <div>
              <h4 className="text-[11px] font-bold text-mongo-subtle uppercase tracking-wider mb-1 font-mono">
                Raw Excerpt
              </h4>
              <p className="text-xs text-slate-700 bg-mongo-slate p-3 rounded-lg border border-mongo-border font-mono">
                {article.content}
              </p>
            </div>
          )}

          {/* MongoDB Atlas Style Document Inspector */}
          <div className="bg-mongo-dark text-slate-200 p-4 rounded-xl text-xs space-y-2 font-mono">
            <h4 className="font-mono font-bold text-mongo-green uppercase text-[11px] tracking-wider mb-2 flex items-center gap-1.5 border-b border-slate-800 pb-2">
              <Terminal className="w-4 h-4 text-mongo-green" /> MongoDB Document Metadata
            </h4>

            <div className="grid grid-cols-1 gap-2">
              <div className="flex justify-between border-b border-slate-800 pb-1">
                <span className="text-slate-400">_id:</span>
                <span className="text-mongo-green font-bold">{article.id}</span>
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
                    className="text-mongo-green hover:underline truncate max-w-xs inline-flex items-center gap-1"
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
                <span className="text-emerald-400 font-bold">{article.relevance_score != null ? `${article.relevance_score}%` : 'N/A'}</span>
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
        <div className="p-4 bg-mongo-slate border-t border-mongo-border rounded-b-xl flex justify-between items-center">
          <button
            onClick={onClose}
            className="px-4 py-2 text-xs font-mono font-bold text-slate-700 bg-white border border-slate-300 rounded-lg hover:bg-slate-100 transition-colors cursor-pointer"
          >
            Close Inspector
          </button>
          <a
            href={articleUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center space-x-1 px-4 py-2 text-xs font-mono font-bold text-mongo-green bg-mongo-forest hover:bg-[#00523a] rounded-lg transition-colors shadow-2xs cursor-pointer"
          >
            <span>Open Publisher Article</span>
            <ArrowUpRight className="w-3.5 h-3.5 text-mongo-green" />
          </a>
        </div>
      </div>
    </div>
  );
}

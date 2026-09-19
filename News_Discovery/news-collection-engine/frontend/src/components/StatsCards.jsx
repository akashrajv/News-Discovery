import React from 'react';
import { Newspaper, CopyX, Zap, DollarSign } from 'lucide-react';

export default function StatsCards({ stats }) {
  if (!stats) return null;

  const cards = [
    {
      title: 'Unique Articles Discovered',
      value: stats.articles_collected ?? 0,
      sub: `${stats.sources_used ?? 0} sources queried`,
      icon: Newspaper,
      badge: 'Retained',
      badgeColor: 'bg-linkedin-light text-linkedin-blue border-linkedin-border',
    },
    {
      title: 'Filtered Duplicates & Noise',
      value: (stats.duplicates_removed ?? 0) + (stats.low_relevance_filtered ?? 0),
      sub: (stats.low_relevance_filtered ?? 0) > 0
        ? `${stats.duplicates_removed ?? 0} duplicates, ${stats.low_relevance_filtered} low-relevance dropped`
        : `${stats.duplicates_removed ?? 0} duplicates linked & removed`,
      icon: CopyX,
      badge: 'Cleaned',
      badgeColor: 'bg-amber-50 text-amber-800 border-amber-200',
    },
    {
      title: 'Cache Response State',
      value: stats.cache_hits > 0 ? 'Cache HIT' : 'Cache MISS',
      sub: stats.cache_hits > 0 ? '0 API requests needed' : `${stats.api_requests ?? 0} API / ${stats.rss_collections ?? 0} RSS`,
      icon: Zap,
      badge: stats.cache_hits > 0 ? '100% Cached' : 'Fresh Request',
      badgeColor: stats.cache_hits > 0 ? 'bg-linkedin-light text-linkedin-blue border-linkedin-border' : 'bg-slate-100 text-slate-700 border-slate-200',
    },
    {
      title: 'Estimated API Cost',
      value: `$${(stats.estimated_api_cost ?? 0).toFixed(4)}`,
      sub: 'Based on configured pricing',
      icon: DollarSign,
      badge: 'Cost Tracked',
      badgeColor: 'bg-blue-50 text-linkedin-blue border-blue-200',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="bg-white rounded-xl border border-slate-200 p-4 shadow-xs hover:border-linkedin-blue transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-sans font-bold text-slate-500 uppercase tracking-wider">
                {card.title}
              </span>
              <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full border ${card.badgeColor}`}>
                {card.badge}
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-2xl font-bold font-sans text-slate-900">
                {card.value}
              </span>
              <Icon className="w-5 h-5 text-linkedin-blue" />
            </div>
            <p className="text-[11px] text-slate-500 font-sans mt-1">
              {card.sub}
            </p>
          </div>
        );
      })}
    </div>
  );
}

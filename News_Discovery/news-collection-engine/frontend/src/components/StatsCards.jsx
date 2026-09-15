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
      badgeColor: 'bg-emerald-100 text-mongo-forest border-emerald-200',
    },
    {
      title: 'Duplicates Filtered',
      value: stats.duplicates_removed ?? 0,
      sub: 'Multi-stage title/hash deduplication',
      icon: CopyX,
      badge: 'Linked',
      badgeColor: 'bg-amber-100 text-amber-900 border-amber-200',
    },
    {
      title: 'Cache Response State',
      value: stats.cache_hits > 0 ? 'Cache HIT' : 'Cache MISS',
      sub: stats.cache_hits > 0 ? '0 API requests needed' : `${stats.api_requests ?? 0} API / ${stats.rss_collections ?? 0} RSS`,
      icon: Zap,
      badge: stats.cache_hits > 0 ? '100% Cached' : 'Fresh Request',
      badgeColor: stats.cache_hits > 0 ? 'bg-emerald-100 text-mongo-forest border-emerald-300' : 'bg-slate-100 text-slate-700 border-slate-200',
    },
    {
      title: 'Estimated API Cost',
      value: `$${(stats.estimated_api_cost ?? 0).toFixed(4)}`,
      sub: 'Based on configured pricing',
      icon: DollarSign,
      badge: 'Cost Tracked',
      badgeColor: 'bg-blue-100 text-blue-800 border-blue-200',
    },
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
      {cards.map((card, idx) => {
        const Icon = card.icon;
        return (
          <div
            key={idx}
            className="bg-white rounded-xl border border-mongo-border p-4 shadow-2xs hover:border-mongo-forest transition-colors"
          >
            <div className="flex items-center justify-between mb-2">
              <span className="text-[11px] font-mono font-bold text-mongo-subtle uppercase tracking-wider">
                {card.title}
              </span>
              <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded border ${card.badgeColor}`}>
                {card.badge}
              </span>
            </div>
            <div className="flex items-baseline justify-between mt-1">
              <span className="text-2xl font-bold font-mono text-mongo-dark">
                {card.value}
              </span>
              <Icon className="w-4 h-4 text-mongo-forest" />
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

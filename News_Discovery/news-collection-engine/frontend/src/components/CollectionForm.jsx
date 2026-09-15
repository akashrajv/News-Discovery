import React, { useState } from 'react';
import { Search, Loader2, Sparkles, Building2, Sliders, ChevronRight } from 'lucide-react';

export default function CollectionForm({ onCollect, loading }) {
  const [entity, setEntity] = useState('Tata Motors, NVIDIA, Tesla, Apple, Microsoft');
  const [keywords, setKeywords] = useState('EV, AI, GPU, tech, revenue');
  const [location, setLocation] = useState('Global');
  const [category, setCategory] = useState('All Sectors');
  const [timeWindow, setTimeWindow] = useState('60');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!entity.trim()) return;

    const kwArray = keywords
      .split(',')
      .map((k) => k.trim())
      .filter((k) => k.length > 0);

    onCollect({
      entity: entity.trim(),
      keywords: kwArray,
      location: location.trim(),
      category: category.trim(),
      time_window_minutes: parseInt(timeWindow, 10),
    });
  };

  const handlePreset = (presetType) => {
    switch (presetType) {
      case 'ALL':
        setEntity('Tata Motors, NVIDIA, Tesla, Apple, Microsoft');
        setKeywords('EV, AI, GPU, tech, revenue');
        setCategory('All Sectors');
        break;
      case 'TECH':
        setEntity('NVIDIA, Apple, Microsoft');
        setKeywords('AI, GPU, cloud, chip, revenue');
        setCategory('Technology');
        break;
      case 'AUTO':
        setEntity('Tata Motors, Tesla');
        setKeywords('EV, electric vehicle, battery, sales');
        setCategory('Automotive');
        break;
      default:
        break;
    }
  };

  return (
    <div className="bg-white rounded-xl border border-mongo-border shadow-xs p-5 mb-6">
      {/* Top Header & Presets */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-mongo-border pb-4 mb-4 gap-3">
        <div className="flex items-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-mongo-forest" />
          <h2 className="font-bold text-mongo-dark text-base font-mono">
            Collection Query Console
          </h2>
        </div>

        {/* MongoDB-style Quick Preset Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs font-mono">
          <span className="text-mongo-subtle mr-1 text-[11px]">Quick Presets:</span>
          <button
            type="button"
            onClick={() => handlePreset('ALL')}
            className="px-2.5 py-1 bg-emerald-50 hover:bg-emerald-100 text-mongo-forest font-bold rounded border border-emerald-200 transition-colors"
          >
            All Companies
          </button>
          <button
            type="button"
            onClick={() => handlePreset('TECH')}
            className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded border border-slate-300 transition-colors"
          >
            Tech Giants
          </button>
          <button
            type="button"
            onClick={() => handlePreset('AUTO')}
            className="px-2.5 py-1 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded border border-slate-300 transition-colors"
          >
            Automotive
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3">
          {/* Target Entities */}
          <div className="lg:col-span-3">
            <label className="block text-[11px] font-bold text-mongo-subtle uppercase tracking-wider mb-1 font-mono">
              Target Entities (Single or Comma-Separated)
            </label>
            <div className="relative">
              <input
                type="text"
                value={entity}
                onChange={(e) => setEntity(e.target.value)}
                placeholder="e.g. Tata Motors, NVIDIA, Tesla, Apple, Microsoft"
                className="w-full pl-9 pr-3 py-2 text-xs border border-mongo-border rounded-lg focus:outline-none focus:ring-2 focus:ring-mongo-forest focus:border-mongo-forest bg-mongo-slate font-medium text-mongo-dark transition-colors"
                required
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>
          </div>

          {/* Keywords */}
          <div className="lg:col-span-1">
            <label className="block text-[11px] font-bold text-mongo-subtle uppercase tracking-wider mb-1 font-mono">
              Keywords Filter
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="e.g. EV, AI, GPU"
              className="w-full px-3 py-2 text-xs border border-mongo-border rounded-lg focus:outline-none focus:ring-2 focus:ring-mongo-forest focus:border-mongo-forest bg-mongo-slate font-medium text-mongo-dark transition-colors"
            />
          </div>

          {/* Category / Region */}
          <div className="lg:col-span-1">
            <label className="block text-[11px] font-bold text-mongo-subtle uppercase tracking-wider mb-1 font-mono">
              Region / Scope
            </label>
            <input
              type="text"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Global"
              className="w-full px-3 py-2 text-xs border border-mongo-border rounded-lg focus:outline-none focus:ring-2 focus:ring-mongo-forest focus:border-mongo-forest bg-mongo-slate font-medium text-mongo-dark transition-colors"
            />
          </div>

          {/* Recency Dropdown */}
          <div className="lg:col-span-1">
            <label className="block text-[11px] font-bold text-mongo-subtle uppercase tracking-wider mb-1 font-mono">
              Recency Window
            </label>
            <select
              value={timeWindow}
              onChange={(e) => setTimeWindow(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-mongo-border rounded-lg focus:outline-none focus:ring-2 focus:ring-mongo-forest focus:border-mongo-forest bg-mongo-slate font-medium text-mongo-dark transition-colors"
            >
              <option value="10">10 minutes</option>
              <option value="30">30 minutes</option>
              <option value="60">1 hour</option>
              <option value="360">6 hours</option>
              <option value="1440">24 hours (1 day)</option>
              <option value="4320">3 days</option>
              <option value="10080">1 week (7 days)</option>
              <option value="20160">2 weeks (14 days)</option>
              <option value="43200">1 month (30 days)</option>
              <option value="129600">3 months (90 days)</option>
              <option value="259200">6 months (180 days)</option>
              <option value="525600">1 year (365 days)</option>
            </select>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-1">
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 bg-mongo-forest hover:bg-[#00523a] active:bg-[#003d2b] text-mongo-green font-bold text-xs px-5 py-2.5 rounded-lg shadow-sm hover:shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed font-mono"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-mongo-green" />
                <span>Processing Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-mongo-green" />
                <span>Run Discovery Pipeline</span>
                <ChevronRight className="w-4 h-4 text-mongo-green" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

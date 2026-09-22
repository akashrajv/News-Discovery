import React, { useState } from 'react';
import { Search, Loader2, Sparkles, Building2, Sliders, ChevronRight } from 'lucide-react';

export default function CollectionForm({ onCollect, loading }) {
  const [entity, setEntity] = useState('Tata Motors, NVIDIA, Tesla, Apple, Microsoft');
  const [keywords, setKeywords] = useState('EV, AI, GPU, tech, revenue');
  const [location, setLocation] = useState('Global');
  const [category, setCategory] = useState('All Sectors');
  const [timeWindow, setTimeWindow] = useState('60');
  const [minRelevance, setMinRelevance] = useState('60');

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
      min_relevance: parseFloat(minRelevance),
    });
  };

  const handlePreset = (presetType) => {
    switch (presetType) {
      case 'INDIA':
        setEntity('Vee Technologies, Tata Motors, Infosys, Zoho');
        setKeywords('revenue, expansion, tech, hiring, contract');
        setLocation('India');
        setCategory('Technology & Business');
        break;
      case 'STATES':
        setEntity('tech companies, startups, MSME, industry');
        setKeywords('expansion, revenue, investment, factory, plant');
        setLocation('Tamil Nadu');
        setCategory('Regional Business');
        break;
      case 'ALL':
        setEntity('Tata Motors, NVIDIA, Tesla, Apple, Microsoft');
        setKeywords('EV, AI, GPU, tech, revenue');
        setLocation('Global');
        setCategory('All Sectors');
        break;
      case 'TECH':
        setEntity('NVIDIA, Apple, Microsoft');
        setKeywords('AI, GPU, cloud, chip, revenue');
        setLocation('Global');
        setCategory('Technology');
        break;
      case 'AUTO':
        setEntity('Tata Motors, Tesla');
        setKeywords('EV, electric vehicle, battery, sales');
        setLocation('India');
        setCategory('Automotive');
        break;
      default:
        break;
    }
  };

  const handleStateSelect = (stateName) => {
    setLocation(stateName);
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs p-5 mb-6">
      {/* Top Header & Presets */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-200 pb-4 mb-4 gap-3">
        <div className="flex items-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-linkedin-blue" />
          <h2 className="font-bold text-slate-900 text-base font-sans">
            Collection Query Console
          </h2>
        </div>

        {/* LinkedIn-style Quick Preset Pills */}
        <div className="flex flex-wrap items-center gap-1.5 text-xs">
          <span className="text-slate-500 mr-1 text-[11px] font-sans">Presets:</span>
          <button
            type="button"
            onClick={() => handlePreset('INDIA')}
            className="px-3 py-1 bg-amber-50 hover:bg-amber-100 text-amber-900 font-bold rounded-full border border-amber-300 transition-colors cursor-pointer"
          >
            🇮🇳 Indian Companies
          </button>
          <button
            type="button"
            onClick={() => handlePreset('STATES')}
            className="px-3 py-1 bg-emerald-50 hover:bg-emerald-100 text-emerald-900 font-bold rounded-full border border-emerald-300 transition-colors cursor-pointer"
          >
            📍 State Discovery
          </button>
          <button
            type="button"
            onClick={() => handlePreset('ALL')}
            className="px-3 py-1 bg-linkedin-light hover:bg-[#D0E3F5] text-linkedin-blue font-bold rounded-full border border-linkedin-border transition-colors cursor-pointer"
          >
            All Companies
          </button>
          <button
            type="button"
            onClick={() => handlePreset('TECH')}
            className="px-3 py-1 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-full border border-slate-300 transition-colors cursor-pointer"
          >
            Tech Giants
          </button>
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-3">
          {/* Target Entities */}
          <div className="lg:col-span-2">
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1 font-sans">
              Target Entities (Single or Comma-Separated)
            </label>
            <div className="relative">
              <input
                type="text"
                value={entity}
                onChange={(e) => setEntity(e.target.value)}
                placeholder="e.g. Vee Technologies, Tata Motors, Infosys"
                className="w-full pl-9 pr-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-linkedin-blue/20 focus:border-linkedin-blue bg-white font-medium text-slate-900 transition-colors"
                required
              />
              <Search className="w-4 h-4 text-slate-400 absolute left-3 top-2.5" />
            </div>
          </div>

          {/* Keywords */}
          <div className="lg:col-span-1">
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1 font-sans">
              Keywords Filter
            </label>
            <input
              type="text"
              value={keywords}
              onChange={(e) => setKeywords(e.target.value)}
              placeholder="e.g. revenue, expansion, AI"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-linkedin-blue/20 focus:border-linkedin-blue bg-white font-medium text-slate-900 transition-colors"
            />
          </div>

          {/* Category / Region */}
          <div className="lg:col-span-1">
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1 font-sans">
              State / Region
            </label>
            <input
              type="text"
              list="indian-states-list"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
              placeholder="e.g. Tamil Nadu, Karnataka"
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-linkedin-blue/20 focus:border-linkedin-blue bg-white font-medium text-slate-900 transition-colors"
            />
            <datalist id="indian-states-list">
              <option value="India" />
              <option value="Tamil Nadu" />
              <option value="Karnataka" />
              <option value="Maharashtra" />
              <option value="Telangana" />
              <option value="Gujarat" />
              <option value="Delhi NCR" />
              <option value="Kerala" />
              <option value="Uttar Pradesh" />
              <option value="West Bengal" />
              <option value="Andhra Pradesh" />
              <option value="Global" />
            </datalist>
          </div>

          {/* Recency Dropdown */}
          <div className="lg:col-span-1">
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1 font-sans">
              Recency Window
            </label>
            <select
              value={timeWindow}
              onChange={(e) => setTimeWindow(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-linkedin-blue/20 focus:border-linkedin-blue bg-white font-medium text-slate-900 transition-colors cursor-pointer"
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

          {/* Min Relevance Threshold Dropdown */}
          <div className="lg:col-span-1">
            <label className="block text-[11px] font-bold text-slate-600 uppercase tracking-wider mb-1 font-sans">
              Min Relevance
            </label>
            <select
              value={minRelevance}
              onChange={(e) => setMinRelevance(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-slate-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-linkedin-blue/20 focus:border-linkedin-blue bg-white font-bold text-linkedin-blue transition-colors cursor-pointer"
            >
              <option value="60">≥ 60% (Recommended)</option>
              <option value="75">≥ 75% (High Match)</option>
              <option value="90">≥ 90% (Peak Match)</option>
              <option value="50">≥ 50% (Broad Match)</option>
              <option value="0">Any Score (≥ 0%)</option>
            </select>
          </div>
        </div>

        {/* Action Button */}
        <div className="flex justify-end pt-1">
          <button
            type="submit"
            disabled={loading}
            className="flex items-center space-x-2 bg-linkedin-blue hover:bg-linkedin-hover active:bg-linkedin-active text-white font-bold text-xs px-6 py-2.5 rounded-full shadow-xs hover:shadow transition-all disabled:opacity-50 disabled:cursor-not-allowed font-sans cursor-pointer"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin text-white" />
                <span>Processing Pipeline...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-4 h-4 text-white" />
                <span>Run Discovery Pipeline</span>
                <ChevronRight className="w-4 h-4 text-white" />
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
}

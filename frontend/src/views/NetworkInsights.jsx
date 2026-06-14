import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { TrendingUp, BarChart3, Globe, AlertTriangle, Target, Zap, CheckCircle, Activity, MessageCircle, Mail, Smartphone } from 'lucide-react';

const CHANNEL_ICONS = { email: Mail, sms: Smartphone, linkedin: MessageCircle, outreach: Zap, default: Activity };

function NetworkInsights({ user }) {
  const [insights, setInsights] = useState(null);
  const [benchmarks, setBenchmarks] = useState(null);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [industry, setIndustry] = useState('');

  useEffect(() => {
    loadData();
  }, [industry]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [ins, bench, st] = await Promise.all([
        api.network.getInsights(industry || null),
        api.network.getBenchmarks(industry || null),
        api.network.getStats(),
      ]);
      setInsights(ins);
      setBenchmarks(bench);
      setStats(st);
    } catch (err) {
      console.error('Error loading network data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading network insights...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Network Insights</h1>
        <p className="text-gray-600 dark:text-gray-400">Shared Intent Graph — anonymized data makes everyone smarter</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">Network Outcomes</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats?.total_anonymized_outcomes || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">Success Rate</p>
          <p className="text-2xl font-bold text-green-600">{stats?.overall_success_rate || 0}%</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">Industries Tracked</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{stats?.industries_tracked || 0}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">Insights Available</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{insights?.insights?.length || 0}</p>
        </div>
      </div>

      {/* Industry Filter */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-6">
        <div className="flex items-center gap-4">
          <Globe size={20} className="text-primary-600" />
          <input type="text" value={industry} onChange={(e) => setIndustry(e.target.value)}
            placeholder="Filter by industry (e.g., Fintech, SaaS, Healthcare)..."
            className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 flex-1" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Benchmarks */}
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <BarChart3 size={20} className="text-primary-600" />
              Industry Benchmarks
              {benchmarks?.industry && <span className="text-sm text-gray-500 font-normal">— {benchmarks.industry}</span>}
            </h2>
            {benchmarks?.benchmarks?.length > 0 ? (
              <div className="space-y-3">
                {benchmarks.benchmarks.map((b, i) => {
                  const Icon = CHANNEL_ICONS[b.segment] || CHANNEL_ICONS.default;
                  return (
                    <div key={i} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <Icon size={18} className="text-primary-600" />
                        <div>
                          <p className="text-sm font-medium text-gray-900 dark:text-white capitalize">{b.segment} ({b.type})</p>
                          <p className="text-xs text-gray-500">{b.sample_size} samples</p>
                        </div>
                      </div>
                      <span className={`text-lg font-bold ${b.success_rate >= 50 ? 'text-green-600' : 'text-yellow-600'}`}>
                        {b.success_rate}%
                      </span>
                    </div>
                  );
                })}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">{benchmarks?.message || 'No benchmark data yet.'}</p>
            )}
          </div>

          {/* Alerts */}
          {insights?.alerts?.length > 0 && (
            <div className="space-y-3">
              <h2 className="text-lg font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                <AlertTriangle size={20} className="text-yellow-600" />
                Actionable Alerts
              </h2>
              {insights.alerts.map((alert, i) => (
                <div key={i} className={`p-4 rounded-lg border ${alert.priority === 'high' ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800' : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'}`}>
                  <div className="flex items-center gap-2 mb-1">
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${alert.priority === 'high' ? 'bg-red-100 dark:bg-red-900/30 text-red-700' : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700'}`}>
                      {alert.priority.toUpperCase()}
                    </span>
                    <span className="font-semibold text-gray-900 dark:text-white text-sm">{alert.title}</span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{alert.detail}</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Network Insights */}
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
              <TrendingUp size={20} className="text-primary-600" />
              Network Intelligence
            </h2>
            {insights?.insights?.length > 0 ? (
              <div className="space-y-4">
                {insights.insights.map((ins, i) => (
                  <div key={i} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-semibold text-gray-900 dark:text-white text-sm">{ins.title}</h3>
                      <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                        {(ins.confidence * 100).toFixed(0)}% confidence
                      </span>
                    </div>
                    <p className="text-sm text-gray-600 dark:text-gray-400">{ins.detail}</p>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">{insights?.message || 'Network intelligence building...'}</p>
            )}
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Data Privacy</h2>
            <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle size={18} className="text-green-600" />
                <span className="text-sm font-medium text-green-700 dark:text-green-300">Anonymized & Encrypted</span>
              </div>
              <p className="text-xs text-green-600 dark:text-green-400">
                All data is SHA-256 hashed before ingestion. No PII, emails, or company names are ever stored in the network. Your data improves the network without ever leaving your control.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default NetworkInsights;

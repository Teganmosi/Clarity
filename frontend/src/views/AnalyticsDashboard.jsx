import React, { useState, useEffect } from 'react';
import { analyticsAPI, intentAPI } from '../services/api';
import { TrendingUp, DollarSign, Target, AlertCircle, Zap } from 'lucide-react';

function AnalyticsDashboard({ user }) {
  const [pipeline, setPipeline] = useState(null);
  const [forecast, setForecast] = useState(null);
  const [highIntent, setHighIntent] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [pipe, fore, high] = await Promise.all([
        analyticsAPI.getPipelineValue().catch(() => null),
        analyticsAPI.getForecast(3).catch(() => null),
        intentAPI.getHighPriority(75).catch(() => null),
      ]);
      setPipeline(pipe);
      setForecast(fore);
      setHighIntent(high);
    } catch (err) {
      console.error('Error loading analytics dashboard:', err);
    } finally {
      setLoading(false);
    }

  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading analytics dashboard...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Analytics Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">Pipeline health, revenue forecasts, and intent overview</p>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500 dark:text-gray-400">Pipeline Value</p>
            <DollarSign size={20} className="text-green-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            ${(pipeline?.total_pipeline_value || 0).toLocaleString()}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500 dark:text-gray-400">Avg Closure Prob</p>
            <Target size={20} className="text-blue-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {((pipeline?.average_closure_probability || 0) * 100).toFixed(1)}%
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500 dark:text-gray-400">High Intent Leads</p>
            <Zap size={20} className="text-purple-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {highIntent?.total || 0}
          </p>
        </div>

        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <div className="flex items-center justify-between mb-2">
            <p className="text-sm text-gray-500 dark:text-gray-400">Total Leads</p>
            <TrendingUp size={20} className="text-yellow-600" />
          </div>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">
            {pipeline?.total_leads || 0}
          </p>
        </div>
      </div>

      {/* Revenue Forecast */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Revenue Forecast</h2>
        {forecast?.forecast ? (
          <div className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {forecast.forecast.map((month) => (
                <div key={month.month} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                  <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">{month.month}</p>
                  <p className="text-xl font-bold text-gray-900 dark:text-white">
                    ${month.projected_revenue.toLocaleString()}
                  </p>
                  <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                    {month.lead_count} leads · {(month.avg_closure_prob * 100).toFixed(1)}% avg prob
                  </p>
                </div>
              ))}
            </div>
            <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
              <p className="text-sm text-gray-500 dark:text-gray-400">Total Projected Revenue (3 months)</p>
              <p className="text-3xl font-bold text-green-600 dark:text-green-400">
                ${(forecast.total_projected_revenue || 0).toLocaleString()}
              </p>
            </div>
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">No forecast data available yet. Enrich leads and analyze intent first.</p>
        )}
      </div>

      {/* High Intent Leads */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">High Intent Leads (Score &gt; 75)</h2>
        {highIntent?.leads?.length > 0 ? (
          <div className="space-y-3">
            {highIntent.leads.map((lead) => (
              <div key={lead.id} className="flex items-center justify-between p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">{lead.name}</p>
                  <p className="text-sm text-gray-500 dark:text-gray-400">{lead.company}</p>
                </div>
                <div className="text-right">
                  <span className="px-2 py-1 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full text-xs font-semibold">
                    Intent: {lead.intent_score}
                  </span>
                  {lead.intent_signals?.length > 0 && (
                    <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                      {lead.intent_signals.length} signal(s)
                    </p>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">No high-intent leads found. Analyze lead intent first.</p>
        )}
      </div>
    </div>
  );
}

export default AnalyticsDashboard;

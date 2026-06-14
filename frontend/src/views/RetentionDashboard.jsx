import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { AlertTriangle, TrendingUp, TrendingDown, DollarSign, RefreshCw, AlertCircle, CheckCircle, Activity, Zap } from 'lucide-react';

function RetentionDashboard({ user }) {
  const [atRisk, setAtRisk] = useState([]);
  const [expansion, setExpansion] = useState([]);
  const [trends, setTrends] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [risk, exp, tr] = await Promise.all([
        api.retention.getAtRisk(),
        api.retention.getExpansion(),
        api.retention.getTrends(),
      ]);
      setAtRisk(risk?.accounts || []);
      setExpansion(exp?.accounts || []);
      setTrends(tr?.trends || []);
    } catch (err) {
      console.error('Error loading retention data:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading retention dashboard...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Retention & Expansion</h1>
        <p className="text-gray-600 dark:text-gray-400">Predictive churn detection and upsell opportunity radar</p>
      </div>

      {/* Summary cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500">At-Risk Accounts</p>
          <p className="text-2xl font-bold text-red-600">{atRisk.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-500">Expansion Opps</p>
          <p className="text-2xl font-bold text-green-600">{expansion.length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-400 capitalize">Healthy</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{atRisk.filter(a => a.health_status === 'healthy').length}</p>
        </div>
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 text-center">
          <p className="text-sm text-gray-400">Trends Tracked</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{trends.length}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* At-Risk Accounts */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <AlertTriangle size={20} className="text-red-600" />
            At-Risk Accounts (Churn &ge; 70)
          </h2>
          {atRisk.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">No accounts at risk. All accounts are healthy!</p>
          ) : (
            <div className="space-y-3">
              {atRisk.map((a) => (
                <div key={a.id} className="p-4 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-900 dark:text-white">{a.company_name}</span>
                    <span className="px-2 py-0.5 bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300 rounded text-xs font-bold">{a.churn_risk_score}%</span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{a.industry} · {a.health_status}</p>
                  <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-red-600 h-2 rounded-full" style={{ width: `${a.churn_risk_score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Expansion Opportunities */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center gap-2">
            <TrendingUp size={20} className="text-green-600" />
            Expansion Opportunities (Score &ge; 80)
          </h2>
          {expansion.length === 0 ? (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">No expansion opportunities identified yet.</p>
          ) : (
            <div className="space-y-3">
              {expansion.map((a) => (
                <div key={a.id} className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-semibold text-gray-900 dark:text-white">{a.company_name}</span>
                    <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs font-bold">{a.expansion_score}%</span>
                  </div>
                  <p className="text-xs text-gray-600 dark:text-gray-400">{a.industry} · {a.health_status}</p>
                  <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div className="bg-green-600 h-2 rounded-full" style={{ width: `${a.expansion_score}%` }} />
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Health Trends */}
      <div className="mt-6 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Health Trends</h2>
        {trends.length === 0 ? (
          <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-4">No trend data yet. Run a snapshot to start tracking.</p>
        ) : (
          <div className="space-y-2">
            <div className="flex justify-between text-xs text-gray-500 dark:text-gray-400 mb-2">
              <span>Recent Snapshots</span>
              <span className="flex items-center gap-4">
                <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-blue-600" /> Health</span>
                <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-red-600" /> Churn Risk</span>
                <span className="flex items-center gap-1"><div className="w-3 h-3 rounded bg-green-600" /> Expansion</span>
              </span>
            </div>
            <div className="space-y-1">
              {trends.slice(-10).map((t, i) => (
                <div key={t.id} className="flex items-center gap-2 text-xs">
                  <span className="w-20 text-gray-500 dark:text-gray-400">{t.snapshot_date ? new Date(t.snapshot_date).toLocaleDateString() : ''}</span>
                  <div className="flex-1 flex gap-1 h-4">
                    <div className="bg-blue-600 h-4 rounded" style={{ width: `${t.health_score || 0}%`, minWidth: '2px' }} title={`Health: ${t.health_score}`} />
                    <div className="bg-red-600 h-4 rounded" style={{ width: `${t.churn_risk || 0}%`, minWidth: '2px' }} title={`Churn: ${t.churn_risk}`} />
                    <div className="bg-green-600 h-4 rounded" style={{ width: `${t.expansion_score || 0}%`, minWidth: '2px' }} title={`Expansion: ${t.expansion_score}`} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
        <button onClick={async () => { await api.retention.snapshotAll(); loadData(); }}
          className="btn btn-secondary flex items-center gap-2 mt-4 text-sm bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200">
          <RefreshCw size={16} /> Take Snapshot
        </button>
      </div>
    </div>
  );
}

export default RetentionDashboard;

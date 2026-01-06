import React, { useState, useEffect } from 'react';
import { analyticsAPI, leadsAPI } from '../services/api';
import {
  Users,
  TrendingUp,
  CheckCircle,
  AlertCircle,
  Plus,
  Upload,
  ArrowUp,
  ArrowDown,
  Clock,
  FileText
} from 'lucide-react';
import { useNavigate } from 'react-router-dom';

/**
 * Dashboard Component
 * Main dashboard showing key metrics and recent activity
 */
function Dashboard({ user }) {
  const [analytics, setAnalytics] = useState(null);
  const [recentLeads, setRecentLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [analyticsRes, leadsRes] = await Promise.all([
        analyticsAPI.getDashboard(),
        leadsAPI.getLeads({ page: 1, per_page: 5, sort_by: 'created_at', sort_order: 'desc' })
      ]);

      console.log('Dashboard Data:', { analyticsRes, leadsRes });

      // Transform API response to match component expectations
      const dashboardData = {
        ...analyticsRes,
        total_leads: analyticsRes.conversion_rate?.total_leads || 0,
        converted_leads: analyticsRes.conversion_rate?.converted_leads || 0,
        conversion_rate: analyticsRes.conversion_rate?.conversion_rate || 0,
        average_score: analyticsRes.score_distribution?.average_score || 0,
        conversion_rate_change: 0, // Not provided by API yet
        // Keep original objects for other usages if needed, but ensure they don't conflict if possible.
        // The component uses analytics.conversion_rate as a number. 
        // We must override the object with the number.
        score_distribution: analyticsRes.score_distribution || {},
        recent_activity: analyticsRes.recent_activity || []
      };

      setAnalytics(dashboardData);
      setRecentLeads(leadsRes?.leads || []);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error('Error fetching dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getScoreCategory = (score) => {
    if (score >= 80) return { label: 'Hot', color: 'badge-hot' };
    if (score >= 50) return { label: 'Warm', color: 'badge-warm' };
    return { label: 'Cold', color: 'badge-cold' };
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'converted':
        return <CheckCircle size={18} className="text-green-600" />;
      case 'lost':
        return <AlertCircle size={18} className="text-red-600" />;
      default:
        return <Clock size={18} className="text-gray-600" />;
    }
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-600 dark:text-gray-400">Loading dashboard...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4 text-red-600 dark:text-red-400">
          {error}
        </div>
      </div>
    );
  }

  if (!analytics) {
    return null;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">Welcome back, {user?.username}</p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="card bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-sm p-6 rounded-lg border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded">
              <Users size={24} className="text-gray-600 dark:text-gray-300" />
            </div>
            {analytics.conversion_rate_change > 0 ? (
              <ArrowUp size={20} className="text-green-600 dark:text-green-400" />
            ) : (
              <ArrowDown size={20} className="text-red-600 dark:text-red-400" />
            )}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Total Leads</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.total_leads}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {analytics.conversion_rate_change > 0 ? '+' : ''}
            {analytics.conversion_rate_change}% from last month
          </p>
        </div>

        <div className="card bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-sm p-6 rounded-lg border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-green-100 dark:bg-green-900/30 rounded">
              <CheckCircle size={24} className="text-green-600 dark:text-green-400" />
            </div>
            {analytics.conversion_rate_change > 0 ? (
              <ArrowUp size={20} className="text-green-600 dark:text-green-400" />
            ) : (
              <ArrowDown size={20} className="text-red-600 dark:text-red-400" />
            )}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Converted Leads</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.converted_leads}</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {analytics.conversion_rate_change > 0 ? '+' : ''}
            {analytics.conversion_rate_change}% from last month
          </p>
        </div>

        <div className="card bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-sm p-6 rounded-lg border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-blue-100 dark:bg-blue-900/30 rounded">
              <TrendingUp size={24} className="text-blue-600 dark:text-blue-400" />
            </div>
            {analytics.conversion_rate_change > 0 ? (
              <ArrowUp size={20} className="text-green-600 dark:text-green-400" />
            ) : (
              <ArrowDown size={20} className="text-red-600 dark:text-red-400" />
            )}
          </div>
          <p className="text-sm text-gray-600 dark:text-gray-400 mb-1">Conversion Rate</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.conversion_rate}%</p>
          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
            {analytics.conversion_rate_change > 0 ? '+' : ''}
            {analytics.conversion_rate_change}% from last month
          </p>
        </div>

        <div className="card bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 shadow-sm p-6 rounded-lg border">
          <div className="flex items-center justify-between mb-4">
            <div className="p-2 bg-purple-100 dark:bg-purple-900/30 rounded">
              <TrendingUp size={24} className="text-purple-600 dark:text-purple-400" />
            </div>
            {analytics.conversion_rate_change > 0 ? (
              <ArrowUp size={20} className="text-green-600 dark:text-green-400" />
            ) : (
              <ArrowDown size={20} className="text-red-600 dark:text-red-400" />
            )}
          </div>
          <p className="text-sm text-gray-600 mb-1 dark:text-gray-400">Average Score</p>
          <p className="text-2xl font-bold text-gray-900 dark:text-white">{analytics.average_score}</p>
          <p className="text-xs text-gray-500 mt-1 dark:text-gray-400">
            {analytics.conversion_rate_change > 0 ? '+' : ''}
            {analytics.conversion_rate_change}% from last month
          </p>
        </div>
      </div>

      {/* Score Distribution */}
      <div className="card mb-8 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Lead Score Distribution</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-red-800 dark:text-red-300">Hot Leads</span>
              <span className="text-2xl font-bold text-red-900 dark:text-red-200">
                {analytics.score_distribution?.hot || 0}
              </span>
            </div>
            <p className="text-xs text-red-600 dark:text-red-400">
              Score 80-100 • High priority
            </p>
          </div>

          <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-yellow-800 dark:text-yellow-300">Warm Leads</span>
              <span className="text-2xl font-bold text-yellow-900 dark:text-yellow-200">
                {analytics.score_distribution?.warm || 0}
              </span>
            </div>
            <p className="text-xs text-yellow-600 dark:text-yellow-400">
              Score 50-79 • Medium priority
            </p>
          </div>

          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-blue-800 dark:text-blue-300">Cold Leads</span>
              <span className="text-2xl font-bold text-blue-900 dark:text-blue-200">
                {analytics.score_distribution?.cold || 0}
              </span>
            </div>
            <p className="text-xs text-blue-600 dark:text-blue-400">
              Score 0-49 • Low priority
            </p>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Leads */}
        <div className="card bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Leads</h3>
            <button
              onClick={() => navigate('/leads')}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              View All
            </button>
          </div>
          <div className="space-y-3">
            {recentLeads.length > 0 ? (
              recentLeads.map((lead) => (
                <div
                  key={lead.id}
                  className="flex items-center justify-between py-3 border-b border-gray-200 dark:border-gray-700 last:border-0"
                >
                  <div className="flex items-center gap-3">
                    <div className="flex-shrink-0 h-10 w-10 bg-gray-200 dark:bg-gray-700 rounded-full flex items-center justify-center">
                      <span className="text-sm font-medium text-gray-600 dark:text-gray-300">
                        {lead.name.charAt(0).toUpperCase()}
                      </span>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900 dark:text-white">{lead.name}</p>
                      <p className="text-xs text-gray-600 dark:text-gray-400">{lead.company}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getScoreCategory(lead.score).color}`}>
                      {getScoreCategory(lead.score).label}
                    </span>
                    <span className="text-sm font-semibold text-gray-900 dark:text-white">{lead.score}</span>
                  </div>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-600 dark:text-gray-400 text-center py-4">No recent leads</p>
            )}
          </div>
        </div>

        {/* Activity Feed */}
        <div className="card bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Recent Activity</h3>
            <button
              onClick={() => navigate('/analytics')}
              className="text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white transition-colors"
            >
              View All
            </button>
          </div>
          <div className="space-y-3">
            {analytics.recent_activity?.length > 0 ? (
              analytics.recent_activity.map((activity, index) => (
                <div
                  key={index}
                  className="flex items-start gap-3 py-3 border-b border-gray-200 dark:border-gray-700 last:border-0"
                >
                  <div className="p-2 bg-gray-100 dark:bg-gray-700 rounded mt-1">
                    <Clock size={18} className="text-gray-600 dark:text-gray-300" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900 dark:text-white">{activity.lead_name}</p>
                    <p className="text-xs text-gray-600 dark:text-gray-400">{activity.action || 'New Lead Created'}</p>
                  </div>
                  <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                    {activity.timestamp ? new Date(activity.timestamp).toLocaleString() : 'Just now'}
                  </span>
                </div>
              ))
            ) : (
              <p className="text-sm text-gray-600 dark:text-gray-400 text-center py-4">No recent activity</p>
            )}
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card mt-6 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg shadow-sm p-6">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={() => navigate('/leads')}
            className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-150"
          >
            <div className="p-2 bg-gray-200 dark:bg-gray-600 rounded">
              <FileText size={20} className="text-gray-600 dark:text-gray-300" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900 dark:text-white">View All Leads</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Manage your leads</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/analytics')}
            className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-150"
          >
            <div className="p-2 bg-gray-200 dark:bg-gray-600 rounded">
              <TrendingUp size={20} className="text-gray-600 dark:text-gray-300" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900 dark:text-white">View Analytics</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Track performance</p>
            </div>
          </button>

          <button
            onClick={() => navigate('/integrations')}
            className="flex items-center gap-3 p-4 bg-gray-50 dark:bg-gray-700/50 border border-gray-200 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-150"
          >
            <div className="p-2 bg-gray-200 dark:bg-gray-600 rounded">
              <Upload size={20} className="text-gray-600 dark:text-gray-300" />
            </div>
            <div className="text-left">
              <p className="text-sm font-medium text-gray-900 dark:text-white">Sync Integrations</p>
              <p className="text-xs text-gray-600 dark:text-gray-400">Connect platforms</p>
            </div>
          </button>
        </div>
      </div>
    </div>
  );
}

export default Dashboard;

import React, { useState, useEffect } from 'react';
import { analyticsAPI } from '../services/api';
import {
  TrendingUp,
  Users,
  BarChart3,
  Clock,
  ArrowUp,
  ArrowDown,
  RefreshCw
} from 'lucide-react';
import {
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  LineChart,
  Line,
  ResponsiveContainer
} from 'recharts';

/**
 * Analytics Component
 * Displays lead analytics and performance metrics
 */
function Analytics({ user }) {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    fetchAnalytics();
  }, []);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await analyticsAPI.getDashboard();
      console.log('Analytics Data:', response);

      const analyticsData = {
        ...response,
        total_leads: response.conversion_rate?.total_leads || 0,
        converted_leads: response.conversion_rate?.converted_leads || 0,
        conversion_rate: response.conversion_rate?.conversion_rate || 0,
        average_score: response.score_distribution?.average_score || 0,
        conversion_rate_change: 0,
        score_distribution: response.score_distribution || {},
        source_performance: response.conversion_rate?.by_source || {},
        campaign_performance: response.conversion_rate?.by_campaign || {}
      };

      setAnalytics(analyticsData);
    } catch (err) {
      setError('Failed to load analytics');
      console.error('Error fetching analytics:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchAnalytics();
    setRefreshing(false);
  };

  const COLORS = ['#dc2626', '#eab308', '#3b82f6'];

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-600 dark:text-gray-400">Loading analytics...</div>
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

  // Prepare chart data
  const scoreDistributionData = [
    { name: 'Hot', value: analytics.score_distribution?.hot || 0 },
    { name: 'Warm', value: analytics.score_distribution?.warm || 0 },
    { name: 'Cold', value: analytics.score_distribution?.cold || 0 },
  ];

  const scoreRangesData = [
    { range: '81-100', count: analytics.score_distribution?.score_ranges?.['81-100'] || 0 },
    { range: '61-80', count: analytics.score_distribution?.score_ranges?.['61-80'] || 0 },
    { range: '41-60', count: analytics.score_distribution?.score_ranges?.['41-60'] || 0 },
    { range: '21-40', count: analytics.score_distribution?.score_ranges?.['21-40'] || 0 },
    { range: '0-20', count: analytics.score_distribution?.score_ranges?.['0-20'] || 0 },
  ];

  const sourcePerformanceData = Object.entries(analytics.source_performance || {}).map(([source, data]) => ({
    source,
    leads: data.total,
    converted: data.converted,
    rate: data.conversion_rate
  }));

  const campaignPerformanceData = Object.entries(analytics.campaign_performance || {}).map(([campaign, data]) => ({
    campaign,
    leads: data.total,
    converted: data.converted,
    rate: data.conversion_rate
  }));

  const trendsData = analytics.trends || [];
  console.log('Trends Data:', trendsData);

  return (
    <div className="container mx-auto px-4 py-8 max-w-7xl">
      {/* Header */}
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">Analytics</h1>
          <p className="text-lg text-gray-600 dark:text-gray-400">Track your lead performance and metrics</p>
        </div>
        <button
          onClick={handleRefresh}
          disabled={refreshing}
          className="btn btn-secondary flex items-center gap-2 px-4 py-2 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-200 border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 rounded-md transition-colors"
        >
          <RefreshCw size={20} className={refreshing ? 'animate-spin' : ''} />
          Refresh Data
        </button>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10">
        <div className="card p-6 shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-full">
              <Users size={24} className="text-gray-600 dark:text-gray-300" />
            </div>
            {analytics.conversion_rate_change > 0 ? (
              <div className="flex items-center text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded-full">
                <ArrowUp size={16} className="mr-1" />
                <span className="text-xs font-semibold">{analytics.conversion_rate_change}%</span>
              </div>
            ) : (
              <div className="flex items-center text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-2 py-1 rounded-full">
                <ArrowDown size={16} className="mr-1" />
                <span className="text-xs font-semibold">{Math.abs(analytics.conversion_rate_change)}%</span>
              </div>
            )}
          </div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Total Leads</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{analytics.total_leads}</p>
        </div>

        <div className="card p-6 shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-green-100 dark:bg-green-900/30 rounded-full">
              <TrendingUp size={24} className="text-green-600 dark:text-green-400" />
            </div>
            {analytics.conversion_rate_change > 0 ? (
              <div className="flex items-center text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded-full">
                <ArrowUp size={16} className="mr-1" />
                <span className="text-xs font-semibold">{analytics.conversion_rate_change}%</span>
              </div>
            ) : (
              <div className="flex items-center text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-2 py-1 rounded-full">
                <ArrowDown size={16} className="mr-1" />
                <span className="text-xs font-semibold">{Math.abs(analytics.conversion_rate_change)}%</span>
              </div>
            )}
          </div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Converted Leads</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{analytics.converted_leads}</p>
        </div>

        <div className="card p-6 shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-blue-100 dark:bg-blue-900/30 rounded-full">
              <BarChart3 size={24} className="text-blue-600 dark:text-blue-400" />
            </div>
            {analytics.conversion_rate_change > 0 ? (
              <div className="flex items-center text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded-full">
                <ArrowUp size={16} className="mr-1" />
                <span className="text-xs font-semibold">{analytics.conversion_rate_change}%</span>
              </div>
            ) : (
              <div className="flex items-center text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-2 py-1 rounded-full">
                <ArrowDown size={16} className="mr-1" />
                <span className="text-xs font-semibold">{Math.abs(analytics.conversion_rate_change)}%</span>
              </div>
            )}
          </div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Conversion Rate</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{analytics.conversion_rate}%</p>
        </div>

        <div className="card p-6 shadow-sm hover:shadow-md transition-shadow bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
          <div className="flex items-center justify-between mb-4">
            <div className="p-3 bg-purple-100 dark:bg-purple-900/30 rounded-full">
              <Clock size={24} className="text-purple-600 dark:text-purple-400" />
            </div>
            {analytics.conversion_rate_change > 0 ? (
              <div className="flex items-center text-green-600 dark:text-green-400 bg-green-50 dark:bg-green-900/30 px-2 py-1 rounded-full">
                <ArrowUp size={16} className="mr-1" />
                <span className="text-xs font-semibold">{analytics.conversion_rate_change}%</span>
              </div>
            ) : (
              <div className="flex items-center text-red-600 dark:text-red-400 bg-red-50 dark:bg-red-900/30 px-2 py-1 rounded-full">
                <ArrowDown size={16} className="mr-1" />
                <span className="text-xs font-semibold">{Math.abs(analytics.conversion_rate_change)}%</span>
              </div>
            )}
          </div>
          <p className="text-sm font-medium text-gray-500 dark:text-gray-400 mb-1">Average Score</p>
          <p className="text-3xl font-bold text-gray-900 dark:text-white">{analytics.average_score}</p>
        </div>
      </div>

      {/* Charts Row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
        {/* Score Distribution */}
        <div className="card p-6 shadow-sm bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 border-b dark:border-gray-700 pb-2">Score Distribution</h3>
          <ResponsiveContainer width="100%" height={400}>
            <PieChart>
              <Pie
                data={scoreDistributionData}
                cx="50%"
                cy="50%"
                labelLine={false}
                outerRadius={130}
                fill="#8884d8"
                dataKey="value"
                paddingAngle={5}
                stroke="none"
              >
                {scoreDistributionData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }} itemStyle={{ color: '#f3f4f6' }} />
              <Legend verticalAlign="bottom" height={36} wrapperStyle={{ color: '#9ca3af' }} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Score Ranges */}
        <div className="card p-6 shadow-sm bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 border-b dark:border-gray-700 pb-2">Score Ranges</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={scoreRangesData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
              <XAxis dataKey="range" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9ca3af' }} />
              <Tooltip cursor={{ fill: '#374151' }} contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }} itemStyle={{ color: '#f3f4f6' }} />
              <Bar dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Charts Row 2 */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-10">
        {/* Source Performance */}
        <div className="card p-6 shadow-sm bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 border-b dark:border-gray-700 pb-2">Source Performance</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={sourcePerformanceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
              <XAxis dataKey="source" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9ca3af' }} />
              <Tooltip cursor={{ fill: '#374151' }} contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }} itemStyle={{ color: '#f3f4f6' }} />
              <Legend wrapperStyle={{ color: '#9ca3af' }} />
              <Bar dataKey="leads" fill="#3b82f6" name="Total Leads" radius={[4, 4, 0, 0]} />
              <Bar dataKey="converted" fill="#22c55e" name="Converted" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Campaign Performance */}
        <div className="card p-6 shadow-sm bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 border-b dark:border-gray-700 pb-2">Campaign Performance</h3>
          <ResponsiveContainer width="100%" height={400}>
            <BarChart data={campaignPerformanceData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
              <XAxis dataKey="campaign" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af' }} />
              <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9ca3af' }} />
              <Tooltip cursor={{ fill: '#374151' }} contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }} itemStyle={{ color: '#f3f4f6' }} />
              <Legend wrapperStyle={{ color: '#9ca3af' }} />
              <Bar dataKey="leads" fill="#3b82f6" name="Total Leads" radius={[4, 4, 0, 0]} />
              <Bar dataKey="converted" fill="#22c55e" name="Converted" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Trends Chart */}
      <div className="card p-6 shadow-sm mb-10 bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 border-b dark:border-gray-700 pb-2">Lead Trends</h3>
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={trendsData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#374151" />
            <XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fill: '#9ca3af' }} />
            <YAxis axisLine={false} tickLine={false} tick={{ fill: '#9ca3af' }} />
            <Tooltip contentStyle={{ backgroundColor: '#1f2937', borderColor: '#374151', color: '#f3f4f6' }} itemStyle={{ color: '#f3f4f6' }} />
            <Legend wrapperStyle={{ color: '#9ca3af' }} />
            <Line type="monotone" dataKey="leads" stroke="#3b82f6" name="Total Leads" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 8 }} />
            <Line type="monotone" dataKey="conversions" stroke="#22c55e" name="Converted" strokeWidth={2} dot={{ r: 4 }} activeDot={{ r: 8 }} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Recent Activity */}
      <div className="card p-6 shadow-sm bg-white dark:bg-gray-800 border dark:border-gray-700 rounded-lg">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-6 border-b dark:border-gray-700 pb-2">Recent Activity</h3>
        <div className="space-y-4">
          {analytics.recent_activity?.length > 0 ? (
            analytics.recent_activity.map((activity, index) => (
              <div key={index} className="flex items-center justify-between py-4 border-b border-gray-100 dark:border-gray-700 last:border-0 hover:bg-gray-50 dark:hover:bg-gray-700/50 px-2 rounded transition-colors">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-gray-100 dark:bg-gray-700 rounded-lg">
                    <Clock size={20} className="text-gray-600 dark:text-gray-300" />
                  </div>
                  <div>
                    <p className="text-base font-medium text-gray-900 dark:text-white">{activity.lead_name}</p>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{activity.action}</p>
                  </div>
                </div>
                <span className="text-sm text-gray-400 dark:text-gray-500">
                  {new Date(activity.timestamp).toLocaleString(undefined, {
                    month: 'short',
                    day: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </span>
              </div>
            ))
          ) : (
            <p className="text-gray-500 dark:text-gray-400 text-center py-8 bg-gray-50 dark:bg-gray-900/50 rounded-lg">No recent activity found</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default Analytics;

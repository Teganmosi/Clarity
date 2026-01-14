import React from 'react';
import { X, Target, Phone, Mail, Building2, Calendar, TrendingUp, Flame, Zap, Snowflake, Award, AlertCircle, CheckCircle2, AlertTriangle, Info } from 'lucide-react';

/**
 * Lead Detail Modal Component
 * Shows comprehensive lead information with score breakdown and insights
 */
function LeadDetailModal({ lead, onClose }) {
  if (!lead) return null;

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-red-600';
    if (score >= 50) return 'text-yellow-600';
    return 'text-blue-600';
  };

  const getScoreBg = (score) => {
    if (score >= 80) return 'bg-red-100 dark:bg-red-900/20';
    if (score >= 50) return 'bg-yellow-100 dark:bg-yellow-900/20';
    return 'bg-blue-100 dark:bg-blue-900/20';
  };

  const getScoreIcon = (category) => {
    switch (category) {
      case 'hot': return <Flame size={24} className="text-red-600" />;
      case 'warm': return <Zap size={24} className="text-yellow-600" />;
      case 'cold': return <Snowflake size={24} className="text-blue-600" />;
      default: return null;
    }
  };

  const getInsights = () => {
    const insights = [];

    // Score-based insights
    if (lead.score >= 80) {
      insights.push({
        type: 'success',
        icon: <Award size={20} className="text-green-600" />,
        title: 'High-Value Lead',
        description: 'This lead has excellent conversion potential. Prioritize immediate outreach.'
      });
    } else if (lead.score >= 50) {
      insights.push({
        type: 'warning',
        icon: <TrendingUp size={20} className="text-yellow-600" />,
        title: 'Moderate Potential',
        description: 'Good engagement signals. Consider personalized follow-up.'
      });
    } else {
      insights.push({
        type: 'info',
        icon: <AlertCircle size={20} className="text-blue-600" />,
        title: 'Needs Nurturing',
        description: 'Low engagement score. Consider lead nurturing campaigns.'
      });
    }

    // Engagement-based insights
    if (lead.past_interactions > 5) {
      insights.push({
        type: 'success',
        icon: <Target size={20} className="text-green-600" />,
        title: 'Highly Engaged',
        description: `${lead.past_interactions} interactions detected. Strong buying signal.`
      });
    }

    if (lead.pages_visited > 10) {
      insights.push({
        type: 'success',
        icon: <TrendingUp size={20} className="text-green-600" />,
        title: 'Active Researcher',
        description: `${lead.pages_visited} pages visited. Shows strong interest.`
      });
    }

    if (lead.time_on_site > 10) {
      insights.push({
        type: 'success',
        icon: <TrendingUp size={20} className="text-green-600" />,
        title: 'Deep Engagement',
        description: `${lead.time_on_site.toFixed(1)} minutes on site. High intent.`
      });
    }

    // Source-based insights
    if (lead.source === 'referral') {
      insights.push({
        type: 'success',
        icon: <Award size={20} className="text-green-600" />,
        title: 'Referral Lead',
        description: 'Referrals have 3x higher conversion rates.'
      });
    }

    if (lead.source === 'paid_ads') {
      insights.push({
        type: 'info',
        icon: <TrendingUp size={20} className="text-blue-600" />,
        title: 'Paid Traffic',
        description: 'Consider retargeting campaigns for better ROI.'
      });
    }

    // Company size insights
    if (lead.company_size === 'enterprise') {
      insights.push({
        type: 'success',
        icon: <Building2 size={20} className="text-green-600" />,
        title: 'Enterprise Lead',
        description: 'High-value opportunity. Allocate senior sales resources.'
      });
    }

    // Budget insights
    if (lead.budget === 'high' || lead.budget === 'enterprise') {
      insights.push({
        type: 'success',
        icon: <Award size={20} className="text-green-600" />,
        title: 'High Budget',
        description: 'Large deal potential. Consider offering premium solutions.'
      });
    }

    return insights;
  };

  const insights = getInsights();

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto animate-scale-in">
        {/* Header */}
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 z-10">
          <div className="flex items-center justify-between">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-white">Lead Details</h2>
            <button
              onClick={onClose}
              className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
            >
              <X size={24} className="text-gray-600 dark:text-gray-400" />
            </button>
          </div>
        </div>

        <div className="p-6 space-y-6">
          {/* Score Card */}
          <div className={`p-6 rounded-xl border-2 ${getScoreBg(lead.score)} animate-slide-in`}>
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center space-x-3">
                {getScoreIcon(lead.score_category)}
                <div>
                  <h3 className="text-4xl font-bold text-gray-900 dark:text-white">
                    {lead.score.toFixed(1)}
                  </h3>
                  <p className="text-lg text-gray-600 dark:text-gray-300 capitalize">
                    {lead.score_category} Lead
                  </p>
                </div>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600 dark:text-gray-400">Conversion Probability</p>
                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                  {(lead.conversion_probability * 100).toFixed(0)}%
                </p>
              </div>
            </div>

            {/* Confidence Badge */}
            {lead.confidence_level && (
              <div className="mb-4">
                <div className={`inline-flex items-center space-x-2 px-3 py-1 rounded-full ${lead.confidence_level === 'high' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' :
                  lead.confidence_level === 'medium' ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' :
                    'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'
                  }`}>
                  {lead.confidence_level === 'high' ? <CheckCircle2 size={16} /> :
                    lead.confidence_level === 'medium' ? <AlertTriangle size={16} /> :
                      <Info size={16} />}
                  <span className="text-sm font-medium">
                    {lead.confidence_label} ({lead.data_points}/{lead.total_factors} factors)
                  </span>
                </div>
              </div>
            )}

            {/* Score Explanation */}
            {lead.explanation && lead.explanation.top_positive_factors && lead.explanation.top_positive_factors.length > 0 && (
              <div className="space-y-3 mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Why this score?</h4>
                <div className="space-y-2">
                  {lead.explanation.top_positive_factors.map((factor, index) => (
                    <div key={index} className="flex items-center justify-between text-sm">
                      <span className="text-gray-600 dark:text-gray-400">✓ {factor.factor}</span>
                      <span className="font-medium text-green-600 dark:text-green-400">+{factor.contribution} pts</span>
                    </div>
                  ))}
                  {lead.explanation.top_negative_factors && lead.explanation.top_negative_factors.length > 0 && (
                    <>
                      {lead.explanation.top_negative_factors.map((factor, index) => (
                        <div key={index} className="flex items-center justify-between text-sm">
                          <span className="text-gray-600 dark:text-gray-400">• {factor.factor}</span>
                          <span className="font-medium text-red-600 dark:text-red-400">{factor.contribution} pts</span>
                        </div>
                      ))}
                    </>
                  )}
                </div>
              </div>
            )}

            {/* Comparative Insights (Phase 2) */}
            {lead.comparative_insights && (
              <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-3">
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300">Comparative Ranking</h4>
                  <div className="flex items-center text-xs font-medium text-blue-600 dark:text-blue-400">
                    <TrendingUp size={14} className="mr-1" />
                    Relative to {lead.comparative_insights.total_leads} leads
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-100 dark:border-blue-800">
                    <p className="text-xs text-blue-600 dark:text-blue-400 font-medium uppercase mb-1">Percentile Rank</p>
                    <p className="text-xl font-bold text-blue-900 dark:text-blue-200">
                      {lead.comparative_insights.rank_text}
                    </p>
                    <p className="text-[10px] text-blue-600 dark:text-blue-400 mt-1">
                      Scores higher than {lead.comparative_insights.percentile}% of leads
                    </p>
                  </div>

                  <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-100 dark:border-purple-800">
                    <p className="text-xs text-purple-600 dark:text-purple-400 font-medium uppercase mb-1">Similar Leads</p>
                    <p className="text-xl font-bold text-purple-900 dark:text-purple-200">
                      {lead.comparative_insights.similar_conversion_rate}%
                    </p>
                    <p className="text-[10px] text-purple-600 dark:text-purple-400 mt-1">
                      Conversion rate for ±5 score range
                    </p>
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Recommendation Card */}
          {lead.recommendation && (
            <div className={`p-6 rounded-xl border-2 animate-slide-in ${lead.recommendation.priority === 'urgent' ? 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800' :
              lead.recommendation.priority === 'medium' ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800' :
                'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
              }`}>
              <div className="flex items-start space-x-3">
                <div className="text-3xl">{lead.recommendation.icon}</div>
                <div className="flex-1">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-white mb-1">
                    Recommended Action
                  </h3>
                  <p className="text-xl font-semibold text-gray-800 dark:text-gray-200 mb-2">
                    {lead.recommendation.action}
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">
                    {lead.recommendation.reason}
                  </p>
                  <div className="flex items-center space-x-4 text-sm">
                    <span className={`px-3 py-1 rounded-full font-medium ${lead.recommendation.priority === 'urgent' ? 'bg-red-200 dark:bg-red-800 text-red-800 dark:text-red-200' :
                      lead.recommendation.priority === 'medium' ? 'bg-yellow-200 dark:bg-yellow-800 text-yellow-800 dark:text-yellow-200' :
                        'bg-blue-200 dark:bg-blue-800 text-blue-800 dark:text-blue-200'
                      }`}>
                      {lead.recommendation.priority.toUpperCase()} Priority
                    </span>
                    <span className="text-gray-600 dark:text-gray-400">
                      Timeline: {lead.recommendation.timeline}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Missing Data Alerts (Phase 2) */}
          {lead.missing_data && lead.missing_data.length > 0 && (
            <div className="card border-2 border-yellow-200 dark:border-yellow-800 bg-yellow-50 dark:bg-yellow-900/10 animate-slide-in">
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-3 flex items-center">
                <AlertTriangle className="mr-2 text-yellow-600" size={20} />
                Improve This Score
              </h3>
              <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
                Collecting the following data could significantly improve this lead's score:
              </p>
              <div className="space-y-3">
                {lead.missing_data.map((alert, index) => (
                  <div key={index} className="flex items-start space-x-3 p-4 bg-white dark:bg-gray-800 rounded-lg border border-yellow-200 dark:border-yellow-700">
                    <span className="text-2xl">{alert.icon}</span>
                    <div className="flex-1">
                      <div className="flex items-center justify-between mb-1">
                        <p className="font-semibold text-gray-900 dark:text-white">
                          {alert.field}
                        </p>
                        <span className={`px-2 py-1 rounded text-xs font-medium ${alert.priority === 'high' ? 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' :
                          'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'
                          }`}>
                          {alert.priority.toUpperCase()}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                        {alert.suggestion}
                      </p>
                      <p className="text-sm font-medium text-yellow-700 dark:text-yellow-400">
                        Potential impact: {alert.potential_impact}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Lead Information */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Contact Info */}
            <div className="card animate-scale-in" style={{ animationDelay: '0.1s' }}>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
                <Mail size={20} className="text-primary-600" />
                Contact Information
              </h3>
              <div className="space-y-3">
                <InfoRow label="Name" value={lead.name} />
                <InfoRow label="Email" value={lead.email} />
                {lead.phone && <InfoRow label="Phone" value={lead.phone} />}
                {lead.company && <InfoRow label="Company" value={lead.company} />}
                {lead.title && <InfoRow label="Title" value={lead.title} />}
              </div>
            </div>

            {/* Lead Source */}
            <div className="card animate-scale-in" style={{ animationDelay: '0.2s' }}>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
                <TrendingUp size={20} className="text-primary-600" />
                Lead Source
              </h3>
              <div className="space-y-3">
                <InfoRow label="Source" value={lead.source || 'N/A'} />
                {lead.campaign && <InfoRow label="Campaign" value={lead.campaign} />}
                {lead.medium && <InfoRow label="Medium" value={lead.medium} />}
                {lead.company_size && <InfoRow label="Company Size" value={lead.company_size} />}
                {lead.industry && <InfoRow label="Industry" value={lead.industry} />}
                {lead.budget && <InfoRow label="Budget" value={lead.budget} />}
              </div>
            </div>
          </div>

          {/* Engagement Metrics */}
          <div className="card animate-scale-in" style={{ animationDelay: '0.3s' }}>
            <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
              <Target size={20} className="text-primary-600" />
              Engagement Metrics
            </h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <MetricCard
                label="Interactions"
                value={lead.past_interactions}
                icon={<Target size={18} />}
              />
              <MetricCard
                label="Pages Visited"
                value={lead.pages_visited}
                icon={<TrendingUp size={18} />}
              />
              <MetricCard
                label="Time on Site"
                value={`${lead.time_on_site.toFixed(1)} min`}
                icon={<Calendar size={18} />}
              />
              <MetricCard
                label="Last Contact"
                value={lead.last_interaction_date ? new Date(lead.last_interaction_date).toLocaleDateString() : 'N/A'}
                icon={<Phone size={18} />}
              />
            </div>
          </div>

          {/* AI Insights */}
          {insights.length > 0 && (
            <div className="card animate-scale-in" style={{ animationDelay: '0.4s' }}>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4 flex items-center space-x-2">
                <Award size={20} className="text-primary-600" />
                AI-Powered Insights
              </h3>
              <div className="space-y-3">
                {insights.map((insight, index) => (
                  <div
                    key={index}
                    className={`p-4 rounded-lg border-2 ${insight.type === 'success'
                      ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'
                      : insight.type === 'warning'
                        ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'
                        : 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800'
                      } hover-lift transition-all duration-300`}
                  >
                    <div className="flex items-start space-x-3">
                      <div className="flex-shrink-0">
                        {insight.icon}
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 dark:text-white mb-1">
                          {insight.title}
                        </h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          {insight.description}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Notes */}
          {lead.notes && (
            <div className="card animate-scale-in" style={{ animationDelay: '0.5s' }}>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Notes</h3>
              <p className="text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                {lead.notes}
              </p>
            </div>
          )}

          {/* Tags */}
          {lead.tags && (
            <div className="card animate-scale-in" style={{ animationDelay: '0.6s' }}>
              <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Tags</h3>
              <div className="flex flex-wrap gap-2">
                {lead.tags.split(',').map((tag, index) => (
                  <span
                    key={index}
                    className="px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full text-sm font-medium"
                  >
                    {tag.trim()}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Metadata */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm text-gray-600 dark:text-gray-400">
            <div>
              <span className="text-gray-500 dark:text-gray-500">Status:</span>{' '}
              <span className={`font-medium capitalize ${lead.converted ? 'text-green-600' : 'text-gray-900 dark:text-white'
                }`}>
                {lead.status}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-500">Converted:</span>{' '}
              <span className={`font-medium ${lead.converted ? 'text-green-600' : 'text-gray-900 dark:text-white'
                }`}>
                {lead.converted ? 'Yes' : 'No'}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-500">Created:</span>{' '}
              <span className="font-medium text-gray-900 dark:text-white">
                {new Date(lead.created_at).toLocaleDateString()}
              </span>
            </div>
            <div>
              <span className="text-gray-500 dark:text-gray-500">Updated:</span>{' '}
              <span className="font-medium text-gray-900 dark:text-white">
                {lead.updated_at ? new Date(lead.updated_at).toLocaleDateString() : 'N/A'}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

/**
 * Info Row Component
 */
function InfoRow({ label, value }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-100 dark:border-gray-700 last:border-0">
      <span className="text-gray-600 dark:text-gray-400">{label}</span>
      <span className="font-medium text-gray-900 dark:text-white">{value}</span>
    </div>
  );
}

/**
 * Metric Card Component
 */
function MetricCard({ label, value, icon }) {
  return (
    <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <div className="flex items-center space-x-2 mb-1">
        {React.cloneElement(icon, { className: 'text-gray-600 dark:text-gray-400' })}
        <span className="text-xs text-gray-500 dark:text-gray-500">{label}</span>
      </div>
      <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
    </div>
  );
}

export default LeadDetailModal;

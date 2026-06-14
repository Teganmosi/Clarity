import React from 'react';
import { User, Shield, Users, AlertCircle, CheckCircle, XCircle } from 'lucide-react';

const ROLE_CONFIG = {
  dm: { label: 'Decision Maker', icon: Shield, color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300', priority: 0 },
  influencer: { label: 'Influencer', icon: Users, color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300', priority: 1 },
  user: { label: 'End User', icon: User, color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300', priority: 2 },
  unknown: { label: 'Unknown', icon: AlertCircle, color: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400', priority: 3 },
};

function BuyingCommitteeMap({ committee }) {
  if (!committee) return null;

  const { committee: members, coverage_score, missing_roles } = committee;

  const sorted = [...(members || [])].sort((a, b) => {
    return (ROLE_CONFIG[a.role]?.priority || 99) - (ROLE_CONFIG[b.role]?.priority || 99);
  });

  return (
    <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Buying Committee</h3>
        <span className={`px-2 py-1 text-xs rounded-full font-medium ${coverage_score >= 70 ? 'bg-green-100 dark:bg-green-900/30 text-green-700' : coverage_score >= 40 ? 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700' : 'bg-red-100 dark:bg-red-900/30 text-red-700'}`}>
          Coverage: {coverage_score}%
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mb-4">
        {sorted.map((m) => {
          const config = ROLE_CONFIG[m.role] || ROLE_CONFIG.unknown;
          const Icon = config.icon;
          return (
            <div key={m.lead_id} className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
              <div className="flex items-center justify-between mb-1">
                <span className="font-medium text-gray-900 dark:text-white text-sm">{m.name}</span>
                <span className={`px-2 py-0.5 text-xs rounded-full ${config.color}`}>
                  {config.label}
                </span>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">{m.title} · {m.email}</p>
              <div className="flex items-center gap-2 mt-2">
                <span className="text-xs text-gray-500">Intent:</span>
                <span className={`text-xs font-bold ${m.intent_score >= 75 ? 'text-green-600' : m.intent_score >= 40 ? 'text-yellow-600' : 'text-gray-500'}`}>
                  {m.intent_score}
                </span>
                <span className={`px-1.5 py-0.5 text-xs rounded-full capitalize ${m.status === 'converted' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' : m.status === 'Meeting Booked' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700' : 'bg-gray-100 dark:bg-gray-700 text-gray-500'}`}>
                  {m.status}
                </span>
              </div>
            </div>
          );
        })}
      </div>

      {missing_roles?.length > 0 && (
        <div className="p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
          <div className="flex items-center gap-2 mb-1">
            <AlertCircle size={16} className="text-yellow-600" />
            <span className="text-sm font-medium text-yellow-700 dark:text-yellow-300">Missing Roles</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {missing_roles.map((role) => (
              <span key={role} className="px-2 py-0.5 bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300 rounded text-xs flex items-center gap-1">
                <XCircle size={12} /> {role}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default BuyingCommitteeMap;

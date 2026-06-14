import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Building2, TrendingUp, Users, Target, AlertCircle, ChevronDown, ChevronUp, RefreshCw, Zap, MessageCircle, Calendar, User, Shield } from 'lucide-react';
import BuyingCommitteeMap from '../components/BuyingCommitteeMap';

function AccountDashboard({ user }) {
  const [accounts, setAccounts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedAccount, setSelectedAccount] = useState(null);
  const [healthData, setHealthData] = useState(null);
  const [committeeData, setCommitteeData] = useState(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      await api.abm.syncAccounts();
      const data = await api.abm.listAccounts();
      setAccounts(data?.accounts || []);
    } catch (err) {
      console.error('Error loading accounts:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewAccount = async (account) => {
    setSelectedAccount(account);
    setLoadingDetail(true);
    try {
      const [health, committee] = await Promise.all([
        api.abm.getAccountHealth(account.id),
        api.abm.getCommittee(account.id),
      ]);
      setHealthData(health);
      setCommitteeData(committee);
    } catch (err) {
      console.error('Error loading account detail:', err);
    } finally {
      setLoadingDetail(false);
    }
  };

  const getHealthColor = (score) => {
    if (score >= 70) return 'text-green-600 bg-green-100 dark:bg-green-900/30';
    if (score >= 40) return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30';
    if (score >= 20) return 'text-blue-600 bg-blue-100 dark:bg-blue-900/30';
    return 'text-gray-600 bg-gray-100 dark:bg-gray-700';
  };

  const getStageIcon = (stage) => {
    switch (stage) {
      case 'pipeline': return <TrendingUp size={16} className="text-green-600" />;
      case 'engaging': return <Zap size={16} className="text-blue-600" />;
      case 'awareness': return <Target size={16} className="text-yellow-600" />;
      default: return <AlertCircle size={16} className="text-gray-500" />;
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Syncing accounts...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Account Dashboard</h1>
          <p className="text-gray-600 dark:text-gray-400">Account-Based Marketing — aggregated health scores and buying committees</p>
        </div>
        <button onClick={loadData} className="btn btn-secondary flex items-center gap-2 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600">
          <RefreshCw size={16} /> Sync
        </button>
      </div>

      {accounts.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
          <Building2 size={48} className="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
          <p>No accounts found. Add leads with company names to auto-create accounts.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Account list */}
          <div className="lg:col-span-1 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
            <div className="p-4 border-b border-gray-200 dark:border-gray-700">
              <h2 className="font-semibold text-gray-900 dark:text-white">Accounts ({accounts.length})</h2>
            </div>
            <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
              {accounts.sort((a, b) => b.health_score - a.health_score).map((acc) => (
                <button key={acc.id} onClick={() => viewAccount(acc)}
                  className={`w-full text-left p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 ${selectedAccount?.id === acc.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900 dark:text-white">{acc.company_name}</span>
                    <span className={`px-2 py-0.5 text-xs rounded-full font-medium ${getHealthColor(acc.health_score)}`}>
                      {acc.health_score}
                    </span>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-500 dark:text-gray-400">
                    {getStageIcon(acc.buying_stage)}
                    <span className="capitalize">{acc.buying_stage}</span>
                    <span>· {acc.employee_count || '?'} emp</span>
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Account Detail */}
          <div className="lg:col-span-2 space-y-6">
            {!selectedAccount ? (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
                <Building2 size={48} className="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                <p>Select an account to view details</p>
              </div>
            ) : loadingDetail ? (
              <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500">Loading account data...</div>
            ) : (
              <>
                {/* Health Overview */}
                <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900 dark:text-white">{selectedAccount.company_name}</h2>
                      <p className="text-sm text-gray-500 dark:text-gray-400">{selectedAccount.domain} · {selectedAccount.industry || 'N/A'}</p>
                    </div>
                    <span className={`px-3 py-1 text-sm rounded-full font-bold ${getHealthColor(healthData?.health_score || 0)}`}>
                      Health: {healthData?.health_score || 0}/100
                    </span>
                  </div>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                      <p className="text-xs text-gray-500">Contacts</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">{healthData?.total_leads || 0}</p>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                      <p className="text-xs text-gray-500">Avg Intent</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">{healthData?.avg_intent_score || 0}</p>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                      <p className="text-xs text-gray-500">Meetings</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">{healthData?.meetings_booked || 0}</p>
                    </div>
                    <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-center">
                      <p className="text-xs text-gray-500">Enriched</p>
                      <p className="text-xl font-bold text-gray-900 dark:text-white">{healthData?.contacts_enriched || 0}</p>
                    </div>
                  </div>
                </div>

                {/* Buying Committee */}
                {committeeData && <BuyingCommitteeMap committee={committeeData} />}
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default AccountDashboard;

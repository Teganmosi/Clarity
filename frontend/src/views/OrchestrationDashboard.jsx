import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Bot, Activity, GitBranch, ArrowRight, AlertCircle, CheckCircle, Clock, User, Zap, MessageCircle, Calendar } from 'lucide-react';

const STAGE_LABELS = {
  new: { label: 'New', color: 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300', icon: User },
  engaging: { label: 'Engaging', color: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300', icon: Zap },
  qualified: { label: 'Qualified', color: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300', icon: MessageCircle },
  meeting_booked: { label: 'Meeting Booked', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300', icon: Calendar },
  closed: { label: 'Closed', color: 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400', icon: CheckCircle },
};

const AGENT_ICONS = {
  enrichment: Zap, intent: Activity, predictive: GitBranch,
  outreach: MessageCircle, conversation: Bot, scheduler: Calendar,
};

function OrchestrationDashboard({ user }) {
  const [status, setStatus] = useState(null);
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedLead, setSelectedLead] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loadingLogs, setLoadingLogs] = useState(false);
  const [stageFilter, setStageFilter] = useState(null);

  useEffect(() => {
    loadData();
  }, [stageFilter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statusData, leadsData] = await Promise.all([
        api.orchestration.getStatus(),
        api.orchestration.getLeads(stageFilter),
      ]);
      setStatus(statusData);
      setLeads(leadsData?.leads || []);
    } catch (err) {
      console.error('Error loading orchestration data:', err);
    } finally {
      setLoading(false);
    }
  };

  const runOrchestration = async (leadId) => {
    try {
      await api.orchestration.run(leadId);
      loadData();
    } catch (err) {
      console.error('Error running orchestration:', err);
    }
  };

  const viewLogs = async (leadId) => {
    try {
      setLoadingLogs(true);
      setSelectedLead(leadId);
      const data = await api.orchestration.getLogs(leadId);
      setLogs(data?.logs || []);
    } catch (err) {
      console.error('Error loading logs:', err);
    } finally {
      setLoadingLogs(false);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600">Loading orchestration dashboard...</div>;
  }

  const stages = ['new', 'engaging', 'qualified', 'meeting_booked', 'closed'];

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Orchestration Dashboard</h1>
        <p className="text-gray-600 dark:text-gray-400">Multi-agent orchestration engine — lifecycle management & task delegation</p>
      </div>

      {/* Pipeline Flow */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Pipeline Flow</h2>
        <div className="flex items-center justify-between overflow-x-auto pb-2">
          {stages.map((stage, i) => {
            const S = STAGE_LABELS[stage];
            const Icon = S.icon;
            const count = status?.stages?.[stage] || 0;
            return (
              <React.Fragment key={stage}>
                <button onClick={() => setStageFilter(stageFilter === stage ? null : stage)}
                  className={`flex flex-col items-center p-4 rounded-lg min-w-[120px] transition-colors ${stageFilter === stage ? 'ring-2 ring-primary-500' : ''}`}>
                  <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-2 ${S.color}`}>
                    <Icon size={24} />
                  </div>
                  <span className="text-sm font-medium text-gray-900 dark:text-white">{S.label}</span>
                  <span className={`text-2xl font-bold mt-1 ${S.color.split(' ')[2] || ''}`}>{count}</span>
                </button>
                {i < stages.length - 1 && <ArrowRight size={20} className="text-gray-300 dark:text-gray-600 flex-shrink-0" />}
              </React.Fragment>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Leads per stage */}
        <div className="lg:col-span-2 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="font-semibold text-gray-900 dark:text-white">Leads by Stage</h2>
          </div>
          {leads.length === 0 ? (
            <div className="p-8 text-center text-gray-500 dark:text-gray-400">No leads found.</div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[500px] overflow-y-auto">
              {leads.map((lead) => {
                const S = STAGE_LABELS[lead.lifecycle_stage] || STAGE_LABELS.new;
                const StageIcon = S.icon;
                const AgentIcon = AGENT_ICONS[lead.active_agent] || Bot;
                return (
                  <div key={lead.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <StageIcon size={16} className={S.color.split(' ')[2] || ''} />
                        <span className="font-medium text-gray-900 dark:text-white">{lead.name}</span>
                        <span className="text-sm text-gray-500">· {lead.company}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        {lead.active_agent && (
                          <span className="flex items-center gap-1 px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs">
                            <AgentIcon size={12} /> {lead.active_agent}
                          </span>
                        )}
                        <button onClick={() => runOrchestration(lead.id)}
                          className="p-1.5 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-xs">
                          Run
                        </button>
                        <button onClick={() => viewLogs(lead.id)}
                          className="p-1.5 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded text-xs">
                          Logs
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                      <span className={`px-2 py-0.5 rounded-full ${S.color}`}>{S.label}</span>
                      <span>Intent: {lead.intent_score || 0}</span>
                      <span>Score: {lead.score || 0}</span>
                    </div>

                    {/* Execution Logs */}
                    {selectedLead === lead.id && (
                      <div className="mt-3 p-3 bg-gray-50 dark:bg-gray-900/30 rounded-lg border border-gray-200 dark:border-gray-700">
                        <p className="text-xs font-semibold text-gray-700 dark:text-gray-300 mb-2">Decision Audit</p>
                        {loadingLogs ? (
                          <p className="text-xs text-gray-500">Loading...</p>
                        ) : logs.length === 0 ? (
                          <p className="text-xs text-gray-500">No orchestration logs yet.</p>
                        ) : (
                          <div className="space-y-2 max-h-[200px] overflow-y-auto">
                            {logs.map((log) => (
                              <div key={log.id} className="p-2 bg-white dark:bg-gray-800 rounded border border-gray-200 dark:border-gray-700 text-xs">
                                <div className="flex items-center justify-between mb-1">
                                  <span className="font-medium text-gray-900 dark:text-white">
                                    {log.previous_stage} → {log.new_stage}
                                  </span>
                                  <span className="text-gray-500 dark:text-gray-400">{log.created_at ? new Date(log.created_at).toLocaleString() : ''}</span>
                                </div>
                                <p className="text-gray-600 dark:text-gray-400 mb-1">{log.trigger_reason}</p>
                                <div className="flex items-center gap-2">
                                  <span className="px-1.5 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs">{log.assigned_agent}</span>
                                  <span className="text-gray-500">{log.action}</span>
                                  <span className={log.outcome ? 'text-green-600' : 'text-gray-500'}>{log.outcome}</span>
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Active Agents & Global Status */}
        <div className="space-y-6">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Active Agents</h2>
            <div className="space-y-3">
              {status?.active_agents && Object.entries(status.active_agents).length > 0 ? (
                Object.entries(status.active_agents).map(([agent, count]) => {
                  const A = AGENT_ICONS[agent] || Bot;
                  return (
                    <div key={agent} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                      <div className="flex items-center gap-2">
                        <A size={18} className="text-primary-600" />
                        <span className="text-sm font-medium text-gray-900 dark:text-white capitalize">{agent}</span>
                      </div>
                      <span className="text-lg font-bold text-gray-900 dark:text-white">{count}</span>
                    </div>
                  );
                })
              ) : (
                <p className="text-sm text-gray-500 dark:text-gray-400 text-center">No agents active</p>
              )}
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Orchestrator Stats</h2>
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Total Leads</span>
                <span className="font-bold text-gray-900 dark:text-white">{status?.total_leads || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Blackboard Events</span>
                <span className="font-bold text-gray-900 dark:text-white">{status?.blackboard_entries || 0}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600 dark:text-gray-400">Active Orchesrations</span>
                <span className="font-bold text-gray-900 dark:text-white">{leads.filter(l => l.active_agent).length}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default OrchestrationDashboard;

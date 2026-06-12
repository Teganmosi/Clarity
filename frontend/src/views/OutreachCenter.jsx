import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Send, Sparkles, FileText, Mail, MessageCircle, Linkedin, Clock, AlertCircle, ChevronDown, ChevronUp, Smartphone } from 'lucide-react';

const CHANNEL_ICONS = { email: Mail, linkedin: Linkedin, sms: Smartphone };
const CHANNEL_LABELS = { email: 'Email', linkedin: 'LinkedIn', sms: 'SMS' };

function OutreachCenter({ user }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [generating, setGenerating] = useState(null);
  const [drafts, setDrafts] = useState({});
  const [editing, setEditing] = useState({});
  const [activeLead, setActiveLead] = useState(null);
  const [history, setHistory] = useState([]);
  const [showHistory, setShowHistory] = useState(null);
  const [activeTab, setActiveTab] = useState('email');
  const [recommendations, setRecommendations] = useState({});

  useEffect(() => {
    loadLeads();
  }, []);

  const loadLeads = async () => {
    try {
      setLoading(true);
      const data = await api.leads.getLeads({ per_page: 50 });
      const leadsData = data?.leads || [];
      setLeads(leadsData);
      leadsData.forEach((l) => suggestForLead(l.id));
    } catch (err) {
      console.error('Error loading leads:', err);
    } finally {
      setLoading(false);
    }
  };

  const suggestForLead = async (leadId) => {
    try {
      const data = await api.multichannel.suggest(leadId, activeTab);
      setRecommendations((prev) => ({ ...prev, [leadId]: data }));
    } catch (err) {
      // silently fail
    }
  };

  useEffect(() => {
    if (leads.length > 0) {
      leads.forEach((l) => suggestForLead(l.id));
    }
  }, [activeTab]);

  const generateDraft = async (lead) => {
    try {
      setGenerating(lead.id);
      let result;
      if (activeTab === 'email') {
        result = await api.outreach.generateDraft(lead.id);
      } else if (activeTab === 'linkedin') {
        result = await api.multichannel.suggest(lead.id, 'linkedin');
        result = result?.draft || { subject: 'LinkedIn Message', body: 'Hi {name}, let us connect!' };
      } else {
        result = await api.multichannel.suggest(lead.id, 'sms');
        result = result?.draft || { subject: 'SMS', body: 'Alert: High intent lead' };
      }
      setDrafts((prev) => ({ ...prev, [lead.id]: result }));
      setEditing((prev) => ({
        ...prev,
        [lead.id]: { subject: result.subject || '', body: result.body || '' },
      }));
    } catch (err) {
      console.error('Error generating draft:', err);
      alert('Failed to generate draft');
    } finally {
      setGenerating(null);
    }
  };

  const sendDraft = async (leadId) => {
    const draft = drafts[leadId];
    if (!draft) return;
    try {
      const lead = leads.find((l) => l.id === leadId);
      await api.multichannel.send(leadId, activeTab, editing[leadId]?.subject, editing[leadId]?.body, lead?.email || '');
      alert(`${CHANNEL_LABELS[activeTab]} sent!`);
      setDrafts((prev) => ({ ...prev, [leadId]: { ...prev[leadId], status: 'sent' } }));
    } catch (err) {
      console.error('Error sending:', err);
      alert('Failed to send');
    }
  };

  const loadHistory = async (leadId) => {
    try {
      const data = await api.multichannel.getHistory(leadId);
      setHistory(data?.history || []);
      setShowHistory(leadId);
    } catch (err) {
      console.error('Error loading history:', err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading outreach center...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Multi-Channel Outreach</h1>
        <p className="text-gray-600 dark:text-gray-400">AI-powered engagement across Email, LinkedIn, and SMS</p>
      </div>

      {/* Channel Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit">
        {['email', 'linkedin', 'sms'].map((ch) => {
          const Icon = CHANNEL_ICONS[ch];
          return (
            <button key={ch} onClick={() => setActiveTab(ch)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === ch ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}`}>
              <Icon size={16} /> {CHANNEL_LABELS[ch]}
            </button>
          );
        })}
      </div>

      {leads.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
          <p>No leads found. Upload leads to get started.</p>
        </div>
      ) : (
        <div className="space-y-4">
          {leads.map((lead) => {
            const rec = recommendations[lead.id];
            const ChannelIcon = CHANNEL_ICONS[activeTab];
            return (
              <div key={lead.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
                <div className="p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white">{lead.name}</h3>
                      <span className="text-sm text-gray-500 dark:text-gray-400">· {lead.company}</span>
                      {rec?.recommended_channel && (
                        <span className="px-2 py-0.5 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs font-medium flex items-center gap-1">
                          {React.createElement(CHANNEL_ICONS[rec.recommended_channel] || Mail, { size: 12 })}
                          Best via {CHANNEL_LABELS[rec.recommended_channel] || rec.recommended_channel}
                        </span>
                      )}
                      {lead.intent_score >= 75 && (
                        <span className="px-2 py-0.5 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded text-xs font-medium">Hot</span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400">{lead.title} · {lead.email}</p>
                    {drafts[lead.id] && (
                      <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                        <div className="flex items-center justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <ChannelIcon size={16} className="text-blue-600" />
                            <span className="text-sm font-medium text-gray-900 dark:text-white">
                              {CHANNEL_LABELS[activeTab]} Draft
                            </span>
                            <span className={`px-2 py-0.5 text-xs rounded-full ${drafts[lead.id].status === 'sent' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300'}`}>
                              {drafts[lead.id].status || 'draft'}
                            </span>
                          </div>
                          <div className="flex items-center gap-2">
                            <button onClick={() => sendDraft(lead.id)}
                              className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                              title="Send" disabled={drafts[lead.id].status === 'sent'}>
                              <Send size={16} />
                            </button>
                            <button onClick={() => setActiveLead(activeLead === lead.id ? null : lead.id)}
                              className="p-1.5 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                              {activeLead === lead.id ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                            </button>
                          </div>
                        </div>
                        {activeLead === lead.id && (
                          <div className="space-y-2">
                            <input type="text" value={editing[lead.id]?.subject || ''}
                              onChange={(e) => setEditing((prev) => ({ ...prev, [lead.id]: { ...prev[lead.id], subject: e.target.value } }))}
                              className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full text-sm" />
                            <textarea value={editing[lead.id]?.body || ''} rows={6}
                              onChange={(e) => setEditing((prev) => ({ ...prev, [lead.id]: { ...prev[lead.id], body: e.target.value } }))}
                              className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full text-sm" />
                            <button onClick={() => sendDraft(lead.id)}
                              className="btn btn-primary flex items-center gap-2 text-sm py-1.5" disabled={drafts[lead.id].status === 'sent'}>
                              <Send size={16} /> Send via {CHANNEL_LABELS[activeTab]}
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                  <div className="flex items-center gap-2 ml-4">
                    <button onClick={() => generateDraft(lead)}
                      disabled={generating === lead.id}
                      className="btn btn-primary flex items-center gap-2 text-sm py-1.5 disabled:opacity-50">
                      {generating === lead.id ? (
                        <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                      ) : (
                        <Sparkles size={16} />
                      )}
                      {generating === lead.id ? 'Generating...' : `Create ${CHANNEL_LABELS[activeTab]}`}
                    </button>
                    <button onClick={() => {
                      if (showHistory === lead.id) { setShowHistory(null); } else { loadHistory(lead.id); }
                    }} className="btn btn-secondary flex items-center gap-2 text-sm py-1.5 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200">
                      <FileText size={16} /> History
                    </button>
                  </div>
                </div>

                {/* Omni-Channel History */}
                {showHistory === lead.id && (
                  <div className="border-t border-gray-200 dark:border-gray-700 p-4 bg-gray-50 dark:bg-gray-900/30">
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Omni-Channel History</h4>
                    {history.length === 0 ? (
                      <p className="text-sm text-gray-500 dark:text-gray-400">No previous outreach for this lead.</p>
                    ) : (
                      <div className="space-y-2">
                        {history.map((h) => {
                          const HIcon = CHANNEL_ICONS[h.channel] || Mail;
                          return (
                            <div key={h.id} className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 flex items-center justify-between text-sm">
                              <div className="flex items-center gap-3">
                                <HIcon size={16} className={h.channel === 'email' ? 'text-blue-600' : h.channel === 'linkedin' ? 'text-sky-600' : 'text-green-600'} />
                                <div>
                                  <p className="font-medium text-gray-900 dark:text-white">{h.subject || h.channel}</p>
                                  <p className="text-xs text-gray-500">
                                    {h.channel} · {h.status} · {h.sent_at ? new Date(h.sent_at).toLocaleDateString() : ''}
                                  </p>
                                </div>
                              </div>
                              <span className={`px-2 py-0.5 text-xs rounded-full capitalize ${
                                h.status === 'sent' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' :
                                h.status === 'opened' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-700' :
                                'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700'
                              }`}>{h.status}</span>
                            </div>
                          );
                        })}
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
  );
}

export default OutreachCenter;

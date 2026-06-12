import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import {
  Plus, Trash2, ToggleLeft, ToggleRight, AlertCircle, ChevronRight,
  ChevronLeft, FileText, Clock, Zap, TrendingUp, RefreshCw, Cpu, Building2, DollarSign
} from 'lucide-react';

const TRIGGER_FIELDS = [
  { value: 'intent_score', label: 'Intent Score' },
  { value: 'score', label: 'Lead Score' },
  { value: 'funding_stage', label: 'Funding Stage' },
  { value: 'employee_count', label: 'Employee Count' },
  { value: 'annual_revenue', label: 'Annual Revenue' },
  { value: 'industry', label: 'Industry' },
  { value: 'status', label: 'Status' },
  { value: 'source', label: 'Source' },
  { value: 'last_interaction_date', label: 'Last Interaction Date' },
];

const OPERATORS = [
  { value: 'equals', label: 'Equals' },
  { value: 'not_equals', label: 'Not Equals' },
  { value: 'greater_than', label: 'Greater Than' },
  { value: 'less_than', label: 'Less Than' },
  { value: 'greater_or_equal', label: 'Greater or Equal' },
  { value: 'less_or_equal', label: 'Less or Equal' },
  { value: 'contains', label: 'Contains' },
  { value: 'is_set', label: 'Is Set' },
  { value: 'in_list', label: 'In List' },
  { value: 'days_since', label: 'Days Since' },
];

const ACTION_TYPES = [
  { value: 'log', label: 'Log Message' },
  { value: 'change_status', label: 'Change Status' },
  { value: 'update_field', label: 'Update Field' },
  { value: 'enrich_lead', label: 'Enrich Lead' },
  { value: 'send_notification', label: 'Send Notification' },
  { value: 'wait', label: 'Wait / Delay' },
  { value: 'webhook', label: 'Webhook Call' },
];

const TEMPLATE_ICONS = { Zap, TrendingUp, RefreshCw, Cpu, Building2, DollarSign, FileText };

function StepIndicator({ current, steps }) {
  return (
    <div className="flex items-center justify-center mb-8">
      {steps.map((s, i) => (
        <React.Fragment key={i}>
          <div className={`flex items-center gap-2 ${i <= current ? 'text-primary-600 dark:text-primary-400' : 'text-gray-400 dark:text-gray-500'}`}>
            <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold ${i <= current ? 'bg-primary-600 text-white' : 'bg-gray-200 dark:bg-gray-700 text-gray-500'}`}>{i + 1}</div>
            <span className="hidden sm:inline text-sm font-medium">{s}</span>
          </div>
          {i < steps.length - 1 && <div className={`w-12 h-0.5 mx-2 ${i < current ? 'bg-primary-600' : 'bg-gray-200 dark:bg-gray-700'}`} />}
        </React.Fragment>
      ))}
    </div>
  );
}

function ExecutionLogModal({ ruleId, ruleName, onClose }) {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadLogs();
  }, [ruleId]);

  const loadLogs = async () => {
    try {
      setLoading(true);
      const data = await api.workflows.getLogsByRule(ruleId);
      setLogs(data?.logs || []);
    } catch (err) {
      console.error('Error loading execution logs:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[80vh] overflow-y-auto">
        <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white">Execution Log: {ruleName}</h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg"><ChevronLeft size={20} /></button>
        </div>
        <div className="p-6">
          {loading ? (
            <p className="text-center text-gray-500 dark:text-gray-400">Loading logs...</p>
          ) : logs.length === 0 ? (
            <p className="text-center text-gray-500 dark:text-gray-400">No execution history for this rule yet.</p>
          ) : (
            <div className="space-y-3">
              {logs.map((log) => (
                <div key={log.id} className="p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600">
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <span className={`px-2 py-0.5 text-xs rounded-full ${log.status === 'executed' ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300'}`}>
                        {log.status}
                      </span>
                      <span className="text-sm font-medium text-gray-900 dark:text-white">{log.lead_name}</span>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">{new Date(log.timestamp).toLocaleString()}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-xs text-gray-600 dark:text-gray-400">
                    <span>Lead ID: {log.lead_id}</span>
                    <span>Action: {log.action_type}</span>
                    <span>Execution: {log.execution_time}s</span>
                    {log.error_message && <span className="text-red-600 col-span-2">Error: {log.error_message}</span>}
                  </div>
                  {log.step_details && (
                    <details className="mt-2">
                      <summary className="text-xs text-gray-500 dark:text-gray-400 cursor-pointer hover:text-gray-700">Step Details</summary>
                      <pre className="mt-1 p-2 bg-gray-100 dark:bg-gray-900 rounded text-xs text-gray-700 dark:text-gray-300 overflow-x-auto">{JSON.stringify(log.step_details, null, 2)}</pre>
                    </details>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function WorkflowBuilder({ user }) {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [step, setStep] = useState(0);
  const [showLogModal, setShowLogModal] = useState(null);
  const [templates, setTemplates] = useState([]);

  const [form, setForm] = useState({
    name: '', trigger_field: 'intent_score', trigger_operator: 'greater_than',
    trigger_value: '75', action_type: 'log', action_params: {}, delay_minutes: 0,
  });

  useEffect(() => {
    loadRules();
    api.workflowTemplates.listTemplates().then(d => setTemplates(d?.templates || [])).catch(() => {});
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await api.workflows.listRules();
      setRules(data || []);
    } catch (err) {
      setError('Failed to load workflow rules');
    } finally {
      setLoading(false);
    }
  };

  const applyTemplate = (template) => {
    if (template.rules?.length > 0) {
      const r = template.rules[0];
      setForm({
        name: template.name,
        trigger_field: r.trigger_field,
        trigger_operator: r.trigger_operator,
        trigger_value: r.trigger_value,
        action_type: r.action_type,
        action_params: r.action_params || {},
        delay_minutes: r.delay_minutes || 0,
      });
      setStep(1);
    }
  };

  const handleCreate = async (e) => {
    e.preventDefault();
    try {
      const params = {};
      if (form.action_type === 'log') {
        params.message = form.action_params.message || 'Workflow triggered for {name}';
      } else if (form.action_type === 'change_status') {
        params.status = form.action_params.status || 'contacted';
      } else if (form.action_type === 'send_notification') {
        params.channel = form.action_params.channel || 'log';
        params.message = form.action_params.message || 'Action required for {name}';
      } else if (form.action_type === 'update_field') {
        params.field = form.action_params.field || 'score';
        params.value = form.action_params.value || 80;
      } else if (form.action_type === 'wait') {
        params.duration_minutes = form.action_params.duration_minutes || 60;
      } else if (form.action_type === 'webhook') {
        params.url = form.action_params.url || '';
        params.payload = form.action_params.payload || {};
      }
      await api.workflows.createRule(
        form.name, form.trigger_field, form.trigger_operator, form.trigger_value,
        form.action_type, params, form.delay_minutes,
      );
      setStep(0);
      setForm({ name: '', trigger_field: 'intent_score', trigger_operator: 'greater_than', trigger_value: '75', action_type: 'log', action_params: {}, delay_minutes: 0 });
      loadRules();
    } catch (err) {
      alert('Failed to create rule');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading workflows...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Workflow Automation</h1>
          <p className="text-gray-600 dark:text-gray-400">Build no-code automation rules for your sales pipeline</p>
        </div>
        <button onClick={() => setStep(step === 0 ? 1 : 0)} className="btn btn-primary flex items-center gap-2">
          {step === 0 ? <><Plus size={18} /> New Rule</> : <><ChevronLeft size={18} /> Back</>}
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-300">
          <AlertCircle size={18} /> {error}
        </div>
      )}

      {/* Multi-Step Wizard */}
      {step > 0 && (
        <>
          <StepIndicator current={step - 1} steps={['Template or Blank', 'Configure Rule', 'Review & Create']} />
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
            {/* Step 1: Template Gallery */}
            {step === 1 && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Choose a Template or Start from Scratch</h2>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
                  {templates.map((t) => {
                    const Icon = TEMPLATE_ICONS[t.icon] || FileText;
                    return (
                      <button key={t.id} onClick={() => applyTemplate(t)}
                        className="text-left p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600 hover:border-primary-500 dark:hover:border-primary-500 transition-colors">
                        <Icon size={24} className="text-primary-600 dark:text-primary-400 mb-2" />
                        <h3 className="font-semibold text-gray-900 dark:text-white">{t.name}</h3>
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">{t.description}</p>
                        <span className="inline-block mt-2 px-2 py-0.5 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded text-xs">{t.category}</span>
                      </button>
                    );
                  })}
                </div>
                <button onClick={() => setStep(2)} className="btn btn-secondary bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600">
                  Skip, build from scratch →
                </button>
              </div>
            )}

            {/* Step 2: Configure */}
            {step === 2 && (
              <form onSubmit={(e) => { e.preventDefault(); setStep(3); }}>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Configure Your Rule</h2>
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Rule Name</label>
                    <input type="text" required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })}
                      className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full" placeholder="e.g. High Intent Alert" />
                  </div>
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-3">IF this condition is met:</p>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
                      <select value={form.trigger_field} onChange={(e) => setForm({ ...form, trigger_field: e.target.value })}
                        className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100">
                        {TRIGGER_FIELDS.map((f) => <option key={f.value} value={f.value}>{f.label}</option>)}
                      </select>
                      <select value={form.trigger_operator} onChange={(e) => setForm({ ...form, trigger_operator: e.target.value })}
                        className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100">
                        {OPERATORS.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                      </select>
                      <input type="text" required value={form.trigger_value} onChange={(e) => setForm({ ...form, trigger_value: e.target.value })}
                        className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100" placeholder="Value" />
                    </div>
                  </div>
                  <div className="p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200 dark:border-green-800">
                    <p className="text-sm font-medium text-green-700 dark:text-green-300 mb-3">THEN execute this action:</p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      <select value={form.action_type} onChange={(e) => setForm({ ...form, action_type: e.target.value })}
                        className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100">
                        {ACTION_TYPES.map((a) => <option key={a.value} value={a.value}>{a.label}</option>)}
                      </select>
                      <div className="flex items-center gap-2">
                        <Clock size={16} className="text-gray-500" />
                        <input type="number" min="0" value={form.delay_minutes} onChange={(e) => setForm({ ...form, delay_minutes: parseInt(e.target.value) || 0 })}
                          className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-24" placeholder="Delay (min)" />
                        <span className="text-xs text-gray-500 dark:text-gray-400">min delay</span>
                      </div>
                    </div>
                    {form.action_type === 'log' && (
                      <input type="text" value={form.action_params.message || ''} onChange={(e) => setForm({ ...form, action_params: { ...form.action_params, message: e.target.value } })}
                        className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full mt-3" placeholder='Message: Workflow triggered for {name}' />
                    )}
                    {form.action_type === 'change_status' && (
                      <select value={form.action_params.status || 'contacted'} onChange={(e) => setForm({ ...form, action_params: { ...form.action_params, status: e.target.value } })}
                        className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full mt-3">
                        <option value="new">New</option>
                        <option value="contacted">Contacted</option>
                        <option value="qualified">Qualified</option>
                        <option value="converted">Converted</option>
                        <option value="lost">Lost</option>
                      </select>
                    )}
                    {form.action_type === 'wait' && (
                      <div className="mt-3 flex items-center gap-2">
                        <span className="text-sm text-gray-600 dark:text-gray-400">Duration:</span>
                        <input type="number" min="1" value={form.action_params.duration_minutes || 60} onChange={(e) => setForm({ ...form, action_params: { ...form.action_params, duration_minutes: parseInt(e.target.value) || 60 } })}
                          className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-24" />
                        <span className="text-sm text-gray-500 dark:text-gray-400">minutes</span>
                      </div>
                    )}
                    {form.action_type === 'webhook' && (
                      <input type="url" value={form.action_params.url || ''} onChange={(e) => setForm({ ...form, action_params: { ...form.action_params, url: e.target.value } })}
                        className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full mt-3" placeholder="https://hooks.example.com/trigger" />
                    )}
                  </div>
                </div>
                <div className="flex gap-2 mt-6">
                  <button type="button" onClick={() => setStep(1)} className="btn btn-secondary bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600">Back</button>
                  <button type="submit" className="btn btn-primary">Review →</button>
                </div>
              </form>
            )}

            {/* Step 3: Review */}
            {step === 3 && (
              <div>
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Review Your Rule</h2>
                <div className="p-6 bg-gray-50 dark:bg-gray-700/50 rounded-lg border border-gray-200 dark:border-gray-600 mb-6">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-4">{form.name}</h3>
                  <div className="space-y-3">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center"><Zap size={20} className="text-blue-600" /></div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">When</p>
                        <p className="font-semibold text-gray-900 dark:text-white">{TRIGGER_FIELDS.find(f => f.value === form.trigger_field)?.label} {OPERATORS.find(o => o.value === form.trigger_operator)?.label} {form.trigger_value}</p>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center"><ChevronRight size={20} className="text-green-600" /></div>
                      <div>
                        <p className="text-sm text-gray-500 dark:text-gray-400">Then</p>
                        <p className="font-semibold text-gray-900 dark:text-white">{ACTION_TYPES.find(a => a.value === form.action_type)?.label}{form.delay_minutes > 0 ? ` (after ${form.delay_minutes} min delay)` : ''}</p>
                      </div>
                    </div>
                  </div>
                </div>
                <div className="flex gap-2">
                  <button onClick={() => setStep(2)} className="btn btn-secondary bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600">Edit</button>
                  <button onClick={handleCreate} className="btn btn-primary">Create Rule</button>
                </div>
              </div>
            )}
          </div>
        </>
      )}

      {/* Rules List */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">Your Rules ({rules.length})</h2>
        <button onClick={loadRules} className="text-sm text-primary-600 dark:text-primary-400 hover:underline">Refresh</button>
      </div>
      {rules.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
          <p className="mb-4">No workflow rules yet. Click "New Rule" to create your first automation.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {rules.map((rule) => (
            <div key={rule.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <h3 className="font-semibold text-gray-900 dark:text-white">{rule.name}</h3>
                  <span className={`px-2 py-0.5 text-xs rounded-full ${rule.active ? 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' : 'bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400'}`}>
                    {rule.active ? 'Active' : 'Inactive'}
                  </span>
                  {rule.delay_minutes > 0 && <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">{rule.delay_minutes}m delay</span>}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  When <strong>{rule.trigger_field}</strong> <strong>{rule.trigger_operator}</strong> <strong>{rule.trigger_value}</strong> → {rule.action_type.replace(/_/g, ' ')}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button onClick={() => setShowLogModal({ id: rule.id, name: rule.name })}
                  className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded hover:bg-gray-100 dark:hover:bg-gray-700" title="Execution History">
                  <FileText size={18} />
                </button>
                <button onClick={async () => { await api.workflows.toggleRule(rule.id); loadRules(); }}
                  className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded hover:bg-gray-100 dark:hover:bg-gray-700" title={rule.active ? 'Deactivate' : 'Activate'}>
                  {rule.active ? <ToggleRight size={20} className="text-green-600" /> : <ToggleLeft size={20} />}
                </button>
                <button onClick={async () => { if (window.confirm('Delete this rule?')) { await api.workflows.deleteRule(rule.id); loadRules(); } }}
                  className="p-2 text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 rounded hover:bg-red-50 dark:hover:bg-red-900/20" title="Delete">
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Execution Log Modal */}
      {showLogModal && (
        <ExecutionLogModal ruleId={showLogModal.id} ruleName={showLogModal.name} onClose={() => setShowLogModal(null)} />
      )}
    </div>
  );
}

export default WorkflowBuilder;

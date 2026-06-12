import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Plus, Trash2, ToggleLeft, ToggleRight, AlertCircle } from 'lucide-react';

const TRIGGER_FIELDS = [
  { value: 'intent_score', label: 'Intent Score' },
  { value: 'score', label: 'Lead Score' },
  { value: 'funding_stage', label: 'Funding Stage' },
  { value: 'employee_count', label: 'Employee Count' },
  { value: 'annual_revenue', label: 'Annual Revenue' },
  { value: 'industry', label: 'Industry' },
  { value: 'status', label: 'Status' },
  { value: 'source', label: 'Source' },
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
];

const ACTION_TYPES = [
  { value: 'log', label: 'Log Message' },
  { value: 'change_status', label: 'Change Status' },
  { value: 'update_field', label: 'Update Field' },
  { value: 'enrich_lead', label: 'Enrich Lead' },
  { value: 'send_notification', label: 'Send Notification' },
];

function WorkflowBuilder({ user }) {
  const [rules, setRules] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    name: '',
    trigger_field: 'intent_score',
    trigger_operator: 'greater_than',
    trigger_value: '75',
    action_type: 'log',
    action_params: {},
  });

  useEffect(() => {
    loadRules();
  }, []);

  const loadRules = async () => {
    try {
      setLoading(true);
      const data = await api.workflows.listRules();
      setRules(data || []);
    } catch (err) {
      console.error('Error loading rules:', err);
      setError('Failed to load workflow rules');
    } finally {
      setLoading(false);
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
      }
      await api.workflows.createRule(
        form.name,
        form.trigger_field,
        form.trigger_operator,
        form.trigger_value,
        form.action_type,
        params,
      );
      setShowForm(false);
      setForm({
        name: '',
        trigger_field: 'intent_score',
        trigger_operator: 'greater_than',
        trigger_value: '75',
        action_type: 'log',
        action_params: {},
      });
      loadRules();
    } catch (err) {
      console.error('Error creating rule:', err);
      alert('Failed to create rule');
    }
  };

  const handleToggle = async (ruleId) => {
    try {
      await api.workflows.toggleRule(ruleId);
      loadRules();
    } catch (err) {
      console.error('Error toggling rule:', err);
    }
  };

  const handleDelete = async (ruleId) => {
    if (!window.confirm('Delete this workflow rule?')) return;
    try {
      await api.workflows.deleteRule(ruleId);
      loadRules();
    } catch (err) {
      console.error('Error deleting rule:', err);
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
          <p className="text-gray-600 dark:text-gray-400">Create "If This Then That" rules for lead automation</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="btn btn-primary flex items-center gap-2"
        >
          <Plus size={18} />
          New Rule
        </button>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-2 text-red-700 dark:text-red-300">
          <AlertCircle size={18} />
          {error}
        </div>
      )}

      {/* Create Rule Form */}
      {showForm && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">New Workflow Rule</h2>
          <form onSubmit={handleCreate} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Rule Name</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                placeholder="e.g. High Intent Alert"
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">When</label>
                <select
                  value={form.trigger_field}
                  onChange={(e) => setForm({ ...form, trigger_field: e.target.value })}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                >
                  {TRIGGER_FIELDS.map((f) => (
                    <option key={f.value} value={f.value}>{f.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">&nbsp;</label>
                <select
                  value={form.trigger_operator}
                  onChange={(e) => setForm({ ...form, trigger_operator: e.target.value })}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                >
                  {OPERATORS.map((o) => (
                    <option key={o.value} value={o.value}>{o.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Value</label>
                <input
                  type="text"
                  required
                  value={form.trigger_value}
                  onChange={(e) => setForm({ ...form, trigger_value: e.target.value })}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                  placeholder="e.g. 75"
                />
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Then Do</label>
                <select
                  value={form.action_type}
                  onChange={(e) => setForm({ ...form, action_type: e.target.value })}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                >
                  {ACTION_TYPES.map((a) => (
                    <option key={a.value} value={a.value}>{a.label}</option>
                  ))}
                </select>
              </div>

              {form.action_type === 'log' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Message</label>
                  <input
                    type="text"
                    value={form.action_params.message || ''}
                    onChange={(e) => setForm({ ...form, action_params: { ...form.action_params, message: e.target.value } })}
                    className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                    placeholder="Workflow triggered for {name}"
                  />
                </div>
              )}

              {form.action_type === 'change_status' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">New Status</label>
                  <select
                    value={form.action_params.status || 'contacted'}
                    onChange={(e) => setForm({ ...form, action_params: { ...form.action_params, status: e.target.value } })}
                    className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                  >
                    <option value="new">New</option>
                    <option value="contacted">Contacted</option>
                    <option value="qualified">Qualified</option>
                    <option value="converted">Converted</option>
                    <option value="lost">Lost</option>
                  </select>
                </div>
              )}
            </div>

            <div className="flex gap-2 pt-2">
              <button type="submit" className="btn btn-primary">Create Rule</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {/* Rules List */}
      {rules.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
          <p className="mb-4">No workflow rules yet. Create your first automation rule.</p>
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
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  When <strong>{rule.trigger_field}</strong> <strong>{rule.trigger_operator}</strong> <strong>{rule.trigger_value}</strong> → {rule.action_type.replace(/_/g, ' ')}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => handleToggle(rule.id)}
                  className="p-2 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white rounded hover:bg-gray-100 dark:hover:bg-gray-700"
                  title={rule.active ? 'Deactivate' : 'Activate'}
                >
                  {rule.active ? <ToggleRight size={20} className="text-green-600" /> : <ToggleLeft size={20} />}
                </button>
                <button
                  onClick={() => handleDelete(rule.id)}
                  className="p-2 text-red-600 dark:text-red-400 hover:text-red-900 dark:hover:text-red-300 rounded hover:bg-red-50 dark:hover:bg-red-900/20"
                  title="Delete"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default WorkflowBuilder;

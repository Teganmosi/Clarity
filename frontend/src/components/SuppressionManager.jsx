import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Plus, Trash2, AlertCircle, Mail, Phone, X } from 'lucide-react';

function SuppressionManager({ user }) {
  const [suppressions, setSuppressions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ email: '', phone: '', reason: 'user_request' });

  useEffect(() => {
    loadSuppressions();
  }, []);

  const loadSuppressions = async () => {
    try {
      setLoading(true);
      const data = await api.multichannel.getSuppressions();
      setSuppressions(data?.suppressions || []);
    } catch (err) {
      console.error('Error loading suppressions:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    try {
      await api.multichannel.addSuppression(form.email || null, form.phone || null, form.reason);
      setShowForm(false);
      setForm({ email: '', phone: '', reason: 'user_request' });
      loadSuppressions();
    } catch (err) {
      alert('Failed to add suppression');
    }
  };

  const handleRemove = async (id) => {
    if (!window.confirm('Remove this entry from the suppression list?')) return;
    try {
      await api.multichannel.removeSuppression(id);
      loadSuppressions();
    } catch (err) {
      alert('Failed to remove');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading suppression list...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Do Not Contact</h1>
          <p className="text-gray-600 dark:text-gray-400">Global suppression list — leads here will not receive any outreach</p>
        </div>
        <button onClick={() => setShowForm(!showForm)} className="btn btn-primary flex items-center gap-2">
          <Plus size={18} /> Add Entry
        </button>
      </div>

      {showForm && (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 mb-6">
          <form onSubmit={handleAdd} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Email</label>
                <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full" placeholder="email@example.com" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Phone</label>
                <input type="text" value={form.phone} onChange={(e) => setForm({ ...form, phone: e.target.value })}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full" placeholder="+1234567890" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Reason</label>
                <select value={form.reason} onChange={(e) => setForm({ ...form, reason: e.target.value })}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full">
                  <option value="user_request">User Request</option>
                  <option value="unsubscribed">Unsubscribed</option>
                  <option value="complaint">Complaint</option>
                  <option value="opted_out">Opted Out</option>
                </select>
              </div>
            </div>
            <div className="flex gap-2">
              <button type="submit" className="btn btn-primary">Add to Suppression</button>
              <button type="button" onClick={() => setShowForm(false)} className="btn btn-secondary bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600">Cancel</button>
            </div>
          </form>
        </div>
      )}

      {suppressions.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
          <p className="mb-4">No entries in the suppression list.</p>
        </div>
      ) : (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
          <table className="w-full">
            <thead className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">Contact</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">Reason</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">Added By</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">Date</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-600 dark:text-gray-400 uppercase">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
              {suppressions.map((s) => (
                <tr key={s.id} className="hover:bg-gray-50 dark:hover:bg-gray-900/40">
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {s.email ? <Mail size={16} className="text-gray-500" /> : <Phone size={16} className="text-gray-500" />}
                      <span className="text-sm font-medium text-gray-900 dark:text-white">{s.email || s.phone}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400 capitalize">{s.reason?.replace(/_/g, ' ')}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{s.added_by || '-'}</td>
                  <td className="px-6 py-4 text-sm text-gray-600 dark:text-gray-400">{s.created_at ? new Date(s.created_at).toLocaleDateString() : '-'}</td>
                  <td className="px-6 py-4 text-right">
                    <button onClick={() => handleRemove(s.id)} className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded" title="Remove">
                      <Trash2 size={16} />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default SuppressionManager;

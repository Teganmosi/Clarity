import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Calendar, Clock, Video, X, CheckCircle, XCircle } from 'lucide-react';

function MeetingManager({ user }) {
  const [meetings, setMeetings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');

  useEffect(() => {
    loadMeetings();
  }, [filter]);

  const loadMeetings = async () => {
    try {
      setLoading(true);
      const data = await api.scheduler.getUpcoming(filter);
      setMeetings(data?.meetings || []);
    } catch (err) {
      console.error('Error loading meetings:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCancel = async (id) => {
    if (!window.confirm('Cancel this meeting?')) return;
    try {
      await api.scheduler.cancel(id);
      loadMeetings();
    } catch (err) {
      alert('Failed to cancel');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading meetings...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Meeting Manager</h1>
          <p className="text-gray-600 dark:text-gray-400">All scheduled meetings across leads</p>
        </div>
        <div className="flex gap-2">
          {['all', 'today', 'week'].map((f) => (
            <button key={f} onClick={() => setFilter(f)}
              className={`px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${filter === f ? 'bg-primary-600 text-white' : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300'}`}>
              {f === 'all' ? 'All' : f === 'today' ? 'Today' : 'This Week'}
            </button>
          ))}
        </div>
      </div>

      {meetings.length === 0 ? (
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
          <Calendar size={48} className="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
          <p>No meetings found. Book a meeting from the Conversation Hub.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {meetings.map((m) => (
            <div key={m.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-primary-100 dark:bg-primary-900/30 flex items-center justify-center">
                  <Calendar size={24} className="text-primary-600" />
                </div>
                <div>
                  <p className="font-semibold text-gray-900 dark:text-white">
                    {m.scheduled_time ? new Date(m.scheduled_time).toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : 'Unknown'}
                  </p>
                  <div className="flex items-center gap-3 text-sm text-gray-500 dark:text-gray-400 mt-1">
                    <span className="flex items-center gap-1"><Clock size={14} /> {m.duration_minutes} min</span>
                    <span className="flex items-center gap-1"><Video size={14} /> {m.timezone}</span>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${m.status === 'scheduled' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' : 'bg-red-100 dark:bg-red-900/30 text-red-700'}`}>
                      {m.status}
                    </span>
                  </div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {m.meeting_link && m.status === 'scheduled' && (
                  <a href={m.meeting_link} target="_blank" rel="noopener noreferrer"
                    className="p-2 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded" title="Join">
                    <Video size={18} />
                  </a>
                )}
                {m.status === 'scheduled' && (
                  <button onClick={() => handleCancel(m.id)}
                    className="p-2 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded" title="Cancel">
                    <XCircle size={18} />
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default MeetingManager;

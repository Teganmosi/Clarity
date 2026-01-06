import React, { useState, useEffect } from 'react';
import { integrationsAPI } from '../services/api';
import {
  Plug2,
  RefreshCw,
  CheckCircle,
  XCircle,
  Clock,
  ExternalLink,
  FileText,
  Settings,
  AlertCircle
} from 'lucide-react';

/**
 * Integrations Component
 * Displays integration status and sync functionality
 */
function Integrations({ user }) {
  const [config, setConfig] = useState(null);
  const [status, setStatus] = useState(null);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchIntegrations();
  }, []);

  const fetchIntegrations = async () => {
    try {
      setLoading(true);
      setError(null);
      const [configRes, statusRes, logsRes] = await Promise.all([
        integrationsAPI.getConfig(),
        integrationsAPI.getStatus(),
        integrationsAPI.getLogs()
      ]);
      setConfig(configRes.data);
      setStatus(statusRes.data);
      setLogs(logsRes.data || []);
    } catch (err) {
      setError('Failed to load integrations');
      console.error('Error fetching integrations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSync = async (platform) => {
    try {
      setSyncing(platform);
      if (platform === 'hubspot') {
        await integrationsAPI.syncHubSpot();
      } else if (platform === 'pipedrive') {
        await integrationsAPI.syncPipedrive();
      }
      await fetchIntegrations();
      alert('Sync completed successfully');
    } catch (err) {
      console.error('Error syncing:', err);
      alert('Sync failed. Please check your configuration.');
    } finally {
      setSyncing(null);
    }
  };

  const getStatusIcon = (platform) => {
    const platformStatus = status?.integrations?.[platform]?.status;
    switch (platformStatus) {
      case 'connected':
        return <CheckCircle size={24} className="text-green-600" />;
      case 'error':
        return <XCircle size={24} className="text-red-600" />;
      default:
        return <AlertCircle size={24} className="text-gray-400" />;
    }
  };

  const getStatusText = (platform) => {
    const platformStatus = status?.integrations?.[platform]?.status;
    switch (platformStatus) {
      case 'connected':
        return 'Connected';
      case 'error':
        return 'Error';
      default:
        return 'Not Connected';
    }
  };

  const getLastSync = (platform) => {
    const lastSync = status?.integrations?.[platform]?.last_sync;
    if (!lastSync) return 'Never';
    return new Date(lastSync).toLocaleString();
  };

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="text-center text-gray-600">Loading integrations...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-red-600">
          {error}
        </div>
      </div>
    );
  }

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Integrations</h1>
        <p className="text-gray-600">Connect and sync with external platforms</p>
      </div>

      {/* Integration Cards */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
        {/* HubSpot */}
        <div className="card">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-orange-100 rounded-lg">
                <Plug2 size={32} className="text-orange-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">HubSpot</h3>
                <p className="text-sm text-gray-600">CRM Integration</p>
              </div>
            </div>
            {getStatusIcon('hubspot')}
          </div>

          <div className="space-y-3 mb-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Status</span>
              <span className={`font-medium ${status?.integrations?.hubspot?.status === 'connected'
                ? 'text-green-600'
                : 'text-gray-600'
                }`}>
                {getStatusText('hubspot')}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Last Sync</span>
              <span className="font-medium text-gray-900">{getLastSync('hubspot')}</span>
            </div>
          </div>

          <button
            onClick={() => handleSync('hubspot')}
            disabled={syncing === 'hubspot'}
            className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncing === 'hubspot' ? (
              <>
                <RefreshCw size={18} className="mr-2 inline animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <RefreshCw size={18} className="mr-2 inline" />
                Sync Now
              </>
            )}
          </button>
        </div>

        {/* Pipedrive */}
        <div className="card">
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div className="p-3 bg-blue-100 rounded-lg">
                <Plug2 size={32} className="text-blue-600" />
              </div>
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Pipedrive</h3>
                <p className="text-sm text-gray-600">CRM Integration</p>
              </div>
            </div>
            {getStatusIcon('pipedrive')}
          </div>

          <div className="space-y-3 mb-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Status</span>
              <span className={`font-medium ${status?.integrations?.pipedrive?.status === 'connected'
                ? 'text-green-600'
                : 'text-gray-600'
                }`}>
                {getStatusText('pipedrive')}
              </span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-gray-600">Last Sync</span>
              <span className="font-medium text-gray-900">{getLastSync('pipedrive')}</span>
            </div>
          </div>

          <button
            onClick={() => handleSync('pipedrive')}
            disabled={syncing === 'pipedrive'}
            className="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {syncing === 'pipedrive' ? (
              <>
                <RefreshCw size={18} className="mr-2 inline animate-spin" />
                Syncing...
              </>
            ) : (
              <>
                <RefreshCw size={18} className="mr-2 inline" />
                Sync Now
              </>
            )}
          </button>
        </div>
      </div>

      {/* Configuration */}
      <div className="card mb-8">
        <div className="flex items-center gap-2 mb-4">
          <Settings size={24} className="text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Configuration</h3>
        </div>
        <div className="space-y-4">
          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">HubSpot Configuration</h4>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">
                <strong>API Key:</strong> {config?.hubspot?.api_key ? '••••••••••••' : 'Not configured'}
              </p>
              <p className="text-sm text-gray-600">
                <strong>Portal ID:</strong> {config?.hubspot?.portal_id || 'Not configured'}
              </p>
            </div>
          </div>

          <div>
            <h4 className="text-sm font-medium text-gray-900 mb-2">Pipedrive Configuration</h4>
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4">
              <p className="text-sm text-gray-600 mb-2">
                <strong>API Token:</strong> {config?.pipedrive?.api_token ? '••••••••••••' : 'Not configured'}
              </p>
              <p className="text-sm text-gray-600">
                <strong>Company Domain:</strong> {config?.pipedrive?.company_domain || 'Not configured'}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Sync History */}
      <div className="card">
        <div className="flex items-center gap-2 mb-4">
          <Clock size={24} className="text-gray-600" />
          <h3 className="text-lg font-semibold text-gray-900">Sync History</h3>
        </div>
        {logs.length > 0 ? (
          <div className="space-y-3">
            {logs.map((log, index) => (
              <div key={index} className="flex items-start justify-between py-3 border-b border-gray-200 last:border-0">
                <div className="flex items-start gap-3">
                  <div className="p-2 bg-gray-100 rounded mt-1">
                    {log.status === 'success' ? (
                      <CheckCircle size={18} className="text-green-600" />
                    ) : (
                      <XCircle size={18} className="text-red-600" />
                    )}
                  </div>
                  <div>
                    <p className="text-sm font-medium text-gray-900 capitalize">
                      {log.platform} Sync
                    </p>
                    <p className="text-xs text-gray-600">
                      {log.message || log.status === 'success' ? 'Sync completed successfully' : 'Sync failed'}
                    </p>
                    {log.details && (
                      <p className="text-xs text-gray-500 mt-1">{log.details}</p>
                    )}
                  </div>
                </div>
                <span className="text-xs text-gray-500 whitespace-nowrap">
                  {new Date(log.timestamp).toLocaleString()}
                </span>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-gray-600">
            <Clock size={48} className="mx-auto mb-3 text-gray-300" />
            <p>No sync history available</p>
          </div>
        )}
      </div>


    </div>
  );
}

export default Integrations;

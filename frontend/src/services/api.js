/**
 * API Service for Clarity
 * Handles all API calls to the backend
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Get API key from localStorage
const getApiKey = () => localStorage.getItem('apiKey') || '';

// Get auth token from localStorage
const getAuthToken = () => localStorage.getItem('authToken') || '';

// Generic API request handler
async function apiRequest(endpoint, options = {}) {
  const url = `${API_BASE_URL}${endpoint}`;

  // Add authentication headers
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers,
  };

  // Try API key first, then auth token
  const apiKey = getApiKey();
  const authToken = getAuthToken();

  if (apiKey) {
    headers['X-API-Key'] = apiKey;
  } else if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  const config = {
    ...options,
    headers,
  };

  try {
    const response = await fetch(url, config);

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'API request failed');
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
}

// Auth API
export const authAPI = {
  /**
   * Register a new user
   */
  register: async (username, email) => {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ username, email }),
    });
  },

  /**
   * Login user
   */
  login: async (username, password) => {
    const formData = new FormData();
    formData.append('username', username);
    formData.append('password', password || username); // For MVP, password is optional

    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      body: formData,
    });

    console.log('Login response status:', response.status);
    console.log('Login response ok:', response.ok);

    if (!response.ok) {
      try {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      } catch (err) {
        // If it was already our error, rethrow it
        if (err.message && err.message !== 'Login failed' && !err.name.includes('SyntaxError')) {
          throw err;
        }
        // Fallback if JSON parsing failed
        throw new Error('Login failed');
      }
    }

    const data = await response.json();
    console.log('Login response data:', data);

    // Store API key and auth token
    if (data.user?.api_key) {
      localStorage.setItem('apiKey', data.user.api_key);
    }
    if (data.access_token) {
      localStorage.setItem('authToken', data.access_token);
    }
    localStorage.setItem('user', JSON.stringify(data.user));

    return data;
  },

  /**
   * Get current user
   */
  getCurrentUser: async () => {
    return apiRequest('/auth/me');
  },

  /**
   * Regenerate API key
   */
  regenerateApiKey: async () => {
    const response = await apiRequest('/auth/regenerate-api-key', {
      method: 'POST',
    });

    if (response.api_key) {
      localStorage.setItem('apiKey', response.api_key);
    }

    return response;
  },

  /**
   * Logout
   */
  logout: () => {
    localStorage.removeItem('apiKey');
    localStorage.removeItem('authToken');
    localStorage.removeItem('user');
  },
};

// Leads API
export const leadsAPI = {
  /**
   * Get all leads with filters and pagination
   */
  getLeads: async (params = {}) => {
    const queryParams = new URLSearchParams(params);
    return apiRequest(`/leads/?${queryParams}`);
  },

  /**
   * Get a single lead
   */
  getLead: async (leadId) => {
    return apiRequest(`/leads/${leadId}`);
  },

  /**
   * Create a new lead
   */
  createLead: async (leadData) => {
    return apiRequest('/leads/', {
      method: 'POST',
      body: JSON.stringify(leadData),
    });
  },

  /**
   * Update a lead
   */
  updateLead: async (leadId, leadData) => {
    return apiRequest(`/leads/${leadId}`, {
      method: 'PUT',
      body: JSON.stringify(leadData),
    });
  },

  /**
   * Delete a lead
   */
  deleteLead: async (leadId) => {
    return apiRequest(`/leads/${leadId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Bulk upload leads
   */
  bulkUpload: async (leads) => {
    return apiRequest('/leads/bulk', {
      method: 'POST',
      body: JSON.stringify({ leads }),
    });
  },

  /**
   * Upload leads from CSV file
   */
  uploadCSV: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${API_BASE_URL}/leads/upload/csv`;
    const apiKey = getApiKey();
    const authToken = getAuthToken();

    const headers = {};
    if (apiKey) {
      headers['X-API-Key'] = apiKey;
    } else if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'CSV upload failed');
    }

    return await response.json();
  },

  /**
   * Upload leads from JSON file
   */
  uploadJSON: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const url = `${API_BASE_URL}/leads/upload/json`;
    const apiKey = getApiKey();
    const authToken = getAuthToken();

    const headers = {};
    if (apiKey) {
      headers['X-API-Key'] = apiKey;
    } else if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: formData,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'JSON upload failed');
    }

    return await response.json();
  },

  /**
   * Export leads
   */
  exportLeads: async (exportRequest) => {
    const url = `${API_BASE_URL}/leads/export`;
    const apiKey = getApiKey();
    const authToken = getAuthToken();

    const headers = {
      'Content-Type': 'application/json',
    };
    if (apiKey) {
      headers['X-API-Key'] = apiKey;
    } else if (authToken) {
      headers['Authorization'] = `Bearer ${authToken}`;
    }

    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(exportRequest),
    });

    if (!response.ok) {
      throw new Error('Export failed');
    }

    return response;
  },

  /**
   * Mark lead as converted
   */
  markConverted: async (leadId) => {
    return apiRequest(`/leads/${leadId}/mark-converted`, {
      method: 'POST',
    });
  },

  /**
   * Retrain scoring model
   */
  retrainModel: async () => {
    return apiRequest('/leads/retrain-model', {
      method: 'POST',
    });
  },
};

// Analytics API
export const analyticsAPI = {
  /**
   * Get conversion rate analytics
   */
  getConversionRate: async () => {
    return apiRequest('/analytics/conversion-rate');
  },

  /**
   * Get score distribution
   */
  getScoreDistribution: async () => {
    return apiRequest('/analytics/score-distribution');
  },

  /**
   * Get dashboard analytics
   */
  getDashboard: async () => {
    return apiRequest('/analytics/dashboard');
  },

  /**
   * Get source performance
   */
  getSourcePerformance: async () => {
    return apiRequest('/analytics/source-performance');
  },

  /**
   * Get campaign performance
   */
  getCampaignPerformance: async () => {
    return apiRequest('/analytics/campaign-performance');
  },

  /**
   * Get trends
   */
  getTrends: async (days = 30) => {
    return apiRequest(`/analytics/trends?days=${days}`);
  },

  /**
   * Get notifications summary
   */
  getNotificationsSummary: async () => {
    return apiRequest('/analytics/notifications-summary');
  },
};

// Integrations API
export const integrationsAPI = {
  /**
   * Get integration configuration
   */
  getConfig: async () => {
    return apiRequest('/integrations/config');
  },

  /**
   * Sync leads to HubSpot
   */
  syncToHubSpot: async (syncRequest) => {
    return apiRequest('/integrations/sync/hubspot', {
      method: 'POST',
      body: JSON.stringify(syncRequest),
    });
  },

  /**
   * Sync leads to Pipedrive
   */
  syncToPipedrive: async (syncRequest) => {
    return apiRequest('/integrations/sync/pipedrive', {
      method: 'POST',
      body: JSON.stringify(syncRequest),
    });
  },

  /**
   * Sync single lead to HubSpot
   */
  syncLeadToHubSpot: async (leadId) => {
    return apiRequest(`/integrations/sync/${leadId}/hubspot`, {
      method: 'POST',
    });
  },

  /**
   * Sync single lead to Pipedrive
   */
  syncLeadToPipedrive: async (leadId) => {
    return apiRequest(`/integrations/sync/${leadId}/pipedrive`, {
      method: 'POST',
    });
  },

  /**
   * Get integration logs
   */
  getLogs: async (params = {}) => {
    const queryParams = new URLSearchParams(params);
    return apiRequest(`/integrations/logs?${queryParams}`);
  },

  /**
   * Get integration status
   */
  getStatus: async () => {
    return apiRequest('/integrations/status');
  },
};

// Enrichment API
export const enrichmentAPI = {
  /**
   * Trigger enrichment for a single lead
   */
  enrichLead: async (leadId) => {
    return apiRequest(`/enrichment/enrich?lead_id=${leadId}`, {
      method: 'POST',
    });
  },

  /**
   * Trigger enrichment for all unenriched leads
   */
  bulkEnrich: async () => {
    return apiRequest('/enrichment/bulk-enrich', {
      method: 'POST',
    });
  },

  /**
   * Refresh enrichment for a lead
   */
  refreshEnrichment: async (leadId) => {
    return apiRequest(`/enrichment/refresh/${leadId}`, {
      method: 'POST',
    });
  },

  /**
   * Get enrichment data for a lead
   */
  getEnrichmentData: async (leadId) => {
    return apiRequest(`/enrichment/${leadId}`);
  },

  /**
   * Get enrichment summary for a lead
   */
  getEnrichmentSummary: async (leadId) => {
    return apiRequest(`/enrichment/summary/${leadId}`);
  },
};

// Workflow Templates API
export const workflowTemplatesAPI = {
  listTemplates: async () => {
    return apiRequest('/workflow-templates/');
  },
  getTemplate: async (templateId) => {
    return apiRequest(`/workflow-templates/${templateId}`);
  },
};

// Workflow API
export const workflowAPI = {
  /**
   * Create a new workflow rule
   */
  createRule: async (name, triggerField, triggerOperator, triggerValue, actionType, actionParams = {}, delayMinutes = 0) => {
    const params = new URLSearchParams({
      name, trigger_field: triggerField, trigger_operator: triggerOperator,
      trigger_value: triggerValue, action_type: actionType, delay_minutes: delayMinutes,
    });
    return apiRequest(`/workflows/rules?${params}`, {
      method: 'POST',
      body: JSON.stringify(actionParams),
      headers: { 'Content-Type': 'application/json' },
    });
  },

  /**
   * List all workflow rules
   */
  listRules: async () => {
    return apiRequest('/workflows/rules');
  },

  /**
   * Toggle a rule active/inactive
   */
  toggleRule: async (ruleId) => {
    return apiRequest(`/workflows/rules/${ruleId}/toggle`, {
      method: 'PUT',
    });
  },

  /**
   * Delete a workflow rule
   */
  deleteRule: async (ruleId) => {
    return apiRequest(`/workflows/rules/${ruleId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get execution logs
   */
  getLogs: async () => {
    return apiRequest('/workflows/logs');
  },

  /**
   * Get execution logs for a specific rule
   */
  getLogsByRule: async (ruleId) => {
    return apiRequest(`/workflows/logs/${ruleId}`);
  },

  /**
   * Clear execution logs
   */
  clearLogs: async () => {
    return apiRequest('/workflows/logs/clear', { method: 'POST' });
  },
};

// Extend analyticsAPI with Sprint 3 endpoints
analyticsAPI.getPipelineValue = async () => {
  return apiRequest('/analytics/pipeline-value');
};

analyticsAPI.getForecast = async (months = 3) => {
  return apiRequest(`/analytics/forecast?months=${months}`);
};

analyticsAPI.trainModel = async () => {
  return apiRequest('/analytics/train-model', { method: 'POST' });
};

// Intent API
export const intentAPI = {
  /**
   * Analyze intent for a single lead
   */
  analyzeIntent: async (leadId) => {
    return apiRequest(`/intent/analyze/${leadId}`, {
      method: 'POST',
    });
  },

  /**
   * Get high-priority leads by intent score threshold
   */
  getHighPriority: async (threshold = 75) => {
    return apiRequest(`/intent/high-priority?threshold=${threshold}`);
  },

  /**
   * Analyze intent for all leads
   */
  analyzeAll: async () => {
    return apiRequest('/intent/analyze-all', {
      method: 'POST',
    });
  },
};

// Outreach API
export const outreachAPI = {
  generateDraft: async (leadId, templateId = null) => {
    let url = `/outreach/generate-draft?lead_id=${leadId}`;
    if (templateId) url += `&template_id=${templateId}`;
    return apiRequest(url, { method: 'POST' });
  },
  send: async (outreachId, recipientEmail) => {
    return apiRequest(`/outreach/send?outreach_id=${outreachId}&recipient_email=${encodeURIComponent(recipientEmail)}`, {
      method: 'POST',
    });
  },
  getTemplates: async () => {
    return apiRequest('/outreach/templates');
  },
  getHistory: async (leadId) => {
    return apiRequest(`/outreach/history/${leadId}`);
  },
};

// Multi-Channel API
export const multichannelAPI = {
  suggest: async (leadId, preferredChannel = null) => {
    let url = `/multichannel/suggest?lead_id=${leadId}`;
    if (preferredChannel) url += `&preferred_channel=${preferredChannel}`;
    return apiRequest(url, { method: 'POST' });
  },
  send: async (leadId, channel, subject = null, body = null, recipient = null) => {
    let url = `/multichannel/send?lead_id=${leadId}&channel=${channel}`;
    if (subject) url += `&subject=${encodeURIComponent(subject)}`;
    if (body) url += `&body=${encodeURIComponent(body)}`;
    if (recipient) url += `&recipient=${encodeURIComponent(recipient)}`;
    return apiRequest(url, { method: 'POST' });
  },
  getHistory: async (leadId) => {
    return apiRequest(`/multichannel/history/${leadId}`);
  },
  getSuppressions: async () => {
    return apiRequest('/multichannel/suppressions');
  },
  addSuppression: async (email, phone, reason = 'user_request') => {
    let url = `/multichannel/suppressions/add?reason=${reason}`;
    if (email) url += `&email=${encodeURIComponent(email)}`;
    if (phone) url += `&phone=${encodeURIComponent(phone)}`;
    return apiRequest(url, { method: 'POST' });
  },
  removeSuppression: async (suppressionId) => {
    return apiRequest(`/multichannel/suppressions/${suppressionId}`, {
      method: 'DELETE',
    });
  },
};

// Conversation API
export const conversationAPI = {
  send: async (leadId, message, channel = 'chat') => {
    const params = new URLSearchParams({ lead_id: leadId, message, channel });
    return apiRequest(`/conversation/send?${params}`, { method: 'POST' });
  },
  get: async (leadId) => {
    return apiRequest(`/conversation/${leadId}`);
  },
  list: async (status = null) => {
    let url = '/conversation/';
    if (status) url += `?status=${status}`;
    return apiRequest(url);
  },
  handoff: async (conversationId) => {
    return apiRequest(`/conversation/handoff/${conversationId}`, { method: 'POST' });
  },
};

export const api = {
  auth: authAPI,
  leads: leadsAPI,
  analytics: analyticsAPI,
  integrations: integrationsAPI,
  enrichment: enrichmentAPI,
  intent: intentAPI,
  workflows: workflowAPI,
  workflowTemplates: workflowTemplatesAPI,
  outreach: outreachAPI,
  multichannel: multichannelAPI,
  conversation: conversationAPI,
};

export default api;

import React, { useState, useEffect } from 'react';
import { leadsAPI, enrichmentAPI, intentAPI } from '../services/api';
import {
  Search,
  Filter,
  Download,
  Upload,
  Plus,
  ChevronLeft,
  ChevronRight,
  FileText,
  CheckCircle,
  XCircle,
  TrendingUp,
  TrendingDown,
  AlertCircle,
  X,
  ExternalLink
} from 'lucide-react';
import LeadDetailModal from './LeadDetailModal';

/**
 * Leads List Component
 * Displays all leads with filtering, sorting, and pagination
 */
function LeadsList({ user }) {
  const [leads, setLeads] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterSource, setFilterSource] = useState('all');
  const [sortBy, setSortBy] = useState('score');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadType, setUploadType] = useState('csv');
  const [uploading, setUploading] = useState(false);
  const [selectedLead, setSelectedLead] = useState(null);
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState('csv');
  const [deletingLeadId, setDeletingLeadId] = useState(null);

  useEffect(() => {
    fetchLeads();
  }, [currentPage, sortBy, sortOrder, filterStatus, filterSource]);

  const fetchLeads = async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page: currentPage,
        per_page: 10,
        sort_by: sortBy,
        sort_order: sortOrder,
      };

      if (filterStatus !== 'all') {
        params.status = filterStatus;
      }

      if (filterSource !== 'all') {
        params.source = filterSource;
      }

      if (searchTerm) {
        params.search = searchTerm;
      }

      const response = await leadsAPI.getLeads(params);
      console.log('Leads Data:', response);
      setLeads(response?.leads || []);
      setTotalPages(Math.ceil((response?.total || 0) / 10));
    } catch (err) {
      setError('Failed to load leads');
      console.error('Error fetching leads:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    setSearchTerm(e.target.value);
    setCurrentPage(1);
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('Are you sure you want to delete this lead?')) {
      return;
    }

    // Prevent multiple simultaneous delete requests for the same lead
    if (deletingLeadId === id) {
      return;
    }

    try {
      setDeletingLeadId(id);
      await leadsAPI.deleteLead(id);
      fetchLeads();
    } catch (err) {
      console.error('Error deleting lead:', err);
      // Only show error if it's not a "Lead not found" error (which means it was already deleted)
      if (!err.message.includes('Lead not found')) {
        alert('Failed to delete lead');
      }
    } finally {
      setDeletingLeadId(null);
    }
  };

  const handleMarkConverted = async (id) => {
    try {
      await leadsAPI.markConverted(id);
      fetchLeads();
    } catch (err) {
      console.error('Error marking lead as converted:', err);
      alert('Failed to mark lead as converted');
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    try {
      setUploading(true);
      if (uploadType === 'csv') {
        await leadsAPI.uploadCSV(uploadFile);
      } else {
        await leadsAPI.uploadJSON(uploadFile);
      }

      setShowUploadModal(false);
      setUploadFile(null);
      fetchLeads();
      alert('File uploaded successfully');
    } catch (err) {
      console.error('Error uploading file:', err);
      alert('Failed to upload file');
    } finally {
      setUploading(false);
    }
  };

  const handleExport = async () => {
    try {
      setExporting(true);
      const response = await leadsAPI.exportLeads({ format: exportFormat });

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `leads-export-${new Date().toISOString().split('T')[0]}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Error exporting leads:', err);
      alert('Failed to export leads');
    } finally {
      setExporting(false);
    }
  };

  const handleEnrich = async (leadId) => {
    try {
      await enrichmentAPI.enrichLead(leadId);
      alert('Enrichment started for lead. Refresh to see updated data.');
    } catch (err) {
      console.error('Error enriching lead:', err);
      alert('Failed to start enrichment');
    }
  };

  const getIntentBadge = (score) => {
    if (score >= 75) return { label: 'High Intent', color: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300' };
    if (score >= 40) return { label: 'Medium Intent', color: 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-700 dark:text-yellow-300' };
    return { label: 'Low Intent', color: 'bg-red-100 dark:bg-red-900/30 text-red-700 dark:text-red-300' };
  };

  const getScoreCategory = (score) => {
    if (score >= 80) return { label: 'Hot', color: 'badge-hot' };
    if (score >= 50) return { label: 'Warm', color: 'badge-warm' };
    return { label: 'Cold', color: 'badge-cold' };
  };

  const getScoreColor = (score) => {
    if (score >= 80) return 'text-red-600 dark:text-red-400';
    if (score >= 50) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-blue-600 dark:text-blue-400';
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'converted':
        return <CheckCircle size={18} className="text-green-600 dark:text-green-400" />;
      case 'lost':
        return <XCircle size={18} className="text-red-600 dark:text-red-400" />;
      default:
        return <AlertCircle size={18} className="text-gray-600 dark:text-gray-400" />;
    }
  };

  const getScoreTrendIcon = (score) => {
    if (score >= 80) return <TrendingUp size={18} className="text-red-600 dark:text-red-400" />;
    if (score >= 50) return <TrendingUp size={18} className="text-yellow-600 dark:text-yellow-400" />;
    return <TrendingDown size={18} className="text-blue-600 dark:text-blue-400" />;
  };

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = !searchTerm ||
      lead.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.email.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.company.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = filterStatus === 'all' || lead.status === filterStatus;
    const matchesSource = filterSource === 'all' || lead.source === filterSource;

    return matchesSearch && matchesStatus && matchesSource;
  });

  return (
    <div className="container mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Leads</h1>
        <p className="text-gray-600 dark:text-gray-400">Manage and track your leads</p>
      </div>

      {/* Actions Bar */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 mb-6">
        <div className="flex flex-col xl:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={20} />
            <input
              type="text"
              placeholder="Search leads..."
              value={searchTerm}
              onChange={handleSearch}
              className="input pl-10 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 placeholder-gray-400"
            />
          </div>

          <div className="flex flex-wrap gap-4 items-center justify-between xl:justify-end">
            {/* Filters */}
            <div className="flex gap-2">
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 min-w-[120px]"
              >
                <option value="all">All Status</option>
                <option value="new">New</option>
                <option value="contacted">Contacted</option>
                <option value="qualified">Qualified</option>
                <option value="converted">Converted</option>
                <option value="lost">Lost</option>
              </select>

              <select
                value={filterSource}
                onChange={(e) => setFilterSource(e.target.value)}
                className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 min-w-[120px]"
              >
                <option value="all">All Sources</option>
                <option value="website">Website</option>
                <option value="referral">Referral</option>
                <option value="social">Social Media</option>
                <option value="email">Email Campaign</option>
                <option value="event">Event</option>
              </select>
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2 items-center">
              <div className="flex items-center gap-2">
                <select
                  value={exportFormat}
                  onChange={(e) => setExportFormat(e.target.value)}
                  className="input py-1.5 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 text-sm"
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>
              <button
                onClick={() => setShowUploadModal(true)}
                className="btn btn-secondary flex items-center gap-2 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                <Upload size={18} />
                <span className="hidden sm:inline">Upload</span>
              </button>
              <button
                onClick={handleExport}
                disabled={exporting}
                className="btn btn-secondary flex items-center gap-2 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-600"
              >
                <Download size={18} />
                <span className="hidden sm:inline">Export</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Leads Table */}
      <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
        {loading ? (
          <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading leads...</div>
        ) : error ? (
          <div className="p-8 text-center text-red-600 dark:text-red-400">{error}</div>
        ) : filteredLeads.length === 0 ? (
          <div className="p-8 text-center text-gray-600 dark:text-gray-400">
            <p className="mb-4">No leads found</p>
            <button
              onClick={() => setShowUploadModal(true)}
              className="btn btn-primary"
            >
              <Upload size={18} className="mr-2 inline" />
              Upload Leads
            </button>
          </div>
        ) : (
          <>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-gray-50 dark:bg-gray-900/50 border-b border-gray-200 dark:border-gray-700">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => handleSort('name')}>
                      Name {sortBy === 'name' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                      Company
                    </th>
                    <th className="hidden lg:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                      Industry
                    </th>
                      <th className="hidden sm:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                        Intent
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800" onClick={() => handleSort('score')}>
                      Score {sortBy === 'score' && (sortOrder === 'asc' ? '↑' : '↓')}
                    </th>
                    <th className="hidden md:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="hidden xl:table-cell px-6 py-3 text-left text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-600 dark:text-gray-400 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                  {filteredLeads.map((lead) => (
                    <tr key={lead.id} className="border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-900/40 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center text-gray-600 dark:text-gray-300 font-medium text-xs mr-3">
                            {lead.name.split(' ').map(n => n[0]).join('')}
                          </div>
                          <div>
                            <div className="text-sm font-medium text-gray-900 dark:text-white">{lead.name}</div>
                            <div className="text-xs text-gray-500 dark:text-gray-400 sm:hidden">{lead.company}</div>
                          </div>
                        </div>
                      </td>
                      <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-700 dark:text-gray-200">{lead.company}</div>
                      </td>
                      <td className="hidden lg:table-cell px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600 dark:text-gray-400">{lead.industry}</div>
                      </td>
                      <td className="hidden sm:table-cell px-6 py-4 whitespace-nowrap">
                        {lead.intent_score !== undefined && lead.intent_score !== null ? (
                          <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getIntentBadge(lead.intent_score).color}`}>
                            {getIntentBadge(lead.intent_score).label} ({lead.intent_score})
                          </span>
                        ) : (
                          <span className="px-2 py-1 rounded-full text-xs font-semibold bg-gray-100 dark:bg-gray-700 text-gray-500 dark:text-gray-400">
                            Not scored
                          </span>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 rounded-full text-xs font-semibold ${getScoreCategory(lead.score).color}`}>
                          {lead.score} - {getScoreCategory(lead.score).label}
                        </span>
                      </td>
                      <td className="hidden md:table-cell px-6 py-4 whitespace-nowrap">
                        <span className="text-sm capitalize text-gray-700 dark:text-gray-200">{lead.status}</span>
                      </td>
                      <td className="hidden xl:table-cell px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-600 dark:text-gray-400">
                          {new Date(lead.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center gap-2" onClick={(e) => e.stopPropagation()}>
                          <button
                            onClick={() => {
                              setSelectedLead(lead);
                              setShowDetailModal(true);
                            }}
                            className="p-1 text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white hover:bg-gray-100 dark:hover:bg-gray-700 rounded"
                            title="View Details"
                          >
                            <FileText size={18} />
                          </button>
                          {lead.status !== 'converted' && (
                            <button
                              onClick={() => handleMarkConverted(lead.id)}
                              className="p-1 text-green-600 dark:text-green-400 hover:text-green-900 dark:hover:text-green-300 hover:bg-green-50 dark:hover:bg-green-900/20 rounded"
                              title="Mark as Converted"
                            >
                              <CheckCircle size={18} />
                            </button>
                          )}
                          <button
                            onClick={() => handleEnrich(lead.id)}
                            className="p-1 text-purple-600 dark:text-purple-400 hover:text-purple-900 dark:hover:text-purple-300 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded"
                            title="Enrich Lead Data"
                          >
                            <TrendingUp size={18} />
                          </button>
                          <button
                            onClick={() => handleDelete(lead.id)}
                            disabled={deletingLeadId === lead.id}
                            className={`p-1 hover:text-red-900 dark:hover:text-red-300 hover:bg-red-50 dark:hover:bg-red-900/20 rounded ${deletingLeadId === lead.id ? 'opacity-50 cursor-not-allowed' : 'text-red-600 dark:text-red-400'}`}
                            title="Delete"
                          >
                            <XCircle size={18} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Pagination */}
            <div className="bg-gray-50 dark:bg-gray-900/50 border-t border-gray-200 dark:border-gray-700 px-6 py-4">
              <div className="flex items-center justify-between">
                <div className="text-sm text-gray-600 dark:text-gray-400">
                  Showing {filteredLeads.length} leads
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                    disabled={currentPage === 1}
                    className="btn btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600"
                  >
                    <ChevronLeft size={18} />
                    Previous
                  </button>
                  <span className="px-3 py-2 text-sm text-gray-600 dark:text-gray-400">
                    Page {currentPage} of {totalPages}
                  </span>
                  <button
                    onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                    disabled={currentPage === totalPages}
                    className="btn btn-secondary flex items-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600"
                  >
                    Next
                    <ChevronRight size={18} />
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white dark:bg-gray-800 rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-bold text-gray-900 dark:text-white">Upload Leads</h2>
              <button
                onClick={() => setShowUploadModal(false)}
                className="text-gray-400 hover:text-gray-600 dark:hover:text-gray-200"
              >
                <X size={24} />
              </button>
            </div>

            <form onSubmit={handleUpload}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  File Type
                </label>
                <select
                  value={uploadType}
                  onChange={(e) => setUploadType(e.target.value)}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                >
                  <option value="csv">CSV</option>
                  <option value="json">JSON</option>
                </select>
              </div>

              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                  Select File
                </label>
                <input
                  type="file"
                  accept={uploadType === 'csv' ? '.csv' : '.json'}
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full"
                  required
                />
              </div>

              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="btn btn-secondary flex-1 bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={uploading || !uploadFile}
                  className="btn btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {uploading ? 'Uploading...' : 'Upload'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lead Detail Modal */}
      {showDetailModal && selectedLead && (
        <LeadDetailModal
          lead={selectedLead}
          onClose={() => setShowDetailModal(false)}
        />
      )}
    </div>
  );
}

export default LeadsList;

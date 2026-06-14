import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { FileText, Send, CreditCard, CheckCircle, XCircle, Eye, Download, ChevronLeft, ChevronRight, AlertTriangle } from 'lucide-react';

const STAGES = ['draft', 'sent', 'signed', 'paid'];
const STAGE_COLORS = {
  draft: 'bg-gray-100 dark:bg-gray-700 text-gray-600 dark:text-gray-300',
  sent: 'bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300',
  signed: 'bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300',
  paid: 'bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300',
};

function DealDesk({ user }) {
  const [deals, setDeals] = useState([]);
  const [loading, setLoading] = useState(true);
  const [viewingDeal, setViewingDeal] = useState(null);
  const [dealDetail, setDealDetail] = useState(null);

  useEffect(() => {
    loadDeals();
  }, []);

  const loadDeals = async () => {
    try {
      setLoading(true);
      const data = await api.closing.listAll();
      setDeals(data?.deals || []);
    } catch (err) {
      console.error('Error loading deals:', err);
    } finally {
      setLoading(false);
    }
  };

  const viewContract = async (deal) => {
    setViewingDeal(deal);
    try {
      const data = await api.closing.getLeadDeals(deal.lead_id);
      const match = data?.deals?.find((d) => d.id === deal.id);
      setDealDetail(match);
    } catch (err) {
      console.error('Error loading deal details:', err);
    }
  };

  const handleSend = async (dealId) => {
    const email = prompt('Enter signer email:');
    if (!email) return;
    try {
      await api.closing.send(dealId, email);
      loadDeals();
    } catch (err) {
      alert('Failed to send');
    }
  };

  const handleSign = async (dealId) => {
    try {
      await api.closing.sign(dealId);
      loadDeals();
    } catch (err) {
      alert('Failed to sign');
    }
  };

  const handlePay = async (dealId) => {
    try {
      await api.closing.pay(dealId);
      loadDeals();
    } catch (err) {
      alert('Failed to process payment');
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading deal desk...</div>;
  }

  const grouped = {};
  STAGES.forEach((s) => (grouped[s] = []));
  deals.forEach((d) => {
    if (grouped[d.status]) grouped[d.status].push(d);
  });

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Deal Desk</h1>
        <p className="text-gray-600 dark:text-gray-400">Autonomous deal closing — Contracts, signatures, and payments</p>
      </div>

      {/* Kanban Board */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        {STAGES.map((stage) => (
          <div key={stage} className="bg-gray-50 dark:bg-gray-900/30 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className={`p-3 rounded-t-lg text-sm font-semibold capitalize ${STAGE_COLORS[stage]}`}>
              {stage} ({grouped[stage]?.length || 0})
            </div>
            <div className="p-2 space-y-2 min-h-[200px]">
              {(grouped[stage] || []).length === 0 ? (
                <p className="text-xs text-gray-400 text-center py-4">No deals</p>
              ) : (
                grouped[stage].map((deal) => (
                  <div key={deal.id} className="p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 text-sm">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900 dark:text-white truncate">{deal.lead_name || `Lead #${deal.lead_id}`}</span>
                      <span className="text-xs font-bold text-gray-900 dark:text-white">{deal.currency} {deal.value?.toLocaleString()}</span>
                    </div>
                    <div className="flex items-center gap-1 mt-2">
                      <button onClick={() => viewContract(deal)} className="p-1 text-gray-600 hover:bg-gray-100 dark:hover:bg-gray-700 rounded" title="View">
                        <Eye size={14} />
                      </button>
                      {deal.status === 'draft' && (
                        <button onClick={() => handleSend(deal.id)} className="p-1 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded" title="Send">
                          <Send size={14} />
                        </button>
                      )}
                      {deal.status === 'sent' && (
                        <button onClick={() => handleSign(deal.id)} className="p-1 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/20 rounded" title="Sign">
                          <CheckCircle size={14} />
                        </button>
                      )}
                      {deal.status === 'signed' && (
                        <button onClick={() => handlePay(deal.id)} className="p-1 text-purple-600 hover:bg-purple-50 dark:hover:bg-purple-900/20 rounded" title="Pay">
                          <CreditCard size={14} />
                        </button>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        ))}
      </div>

      {/* Contract Viewer Modal */}
      {viewingDeal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-3xl w-full max-h-[85vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Contract — {viewingDeal.lead_name || `Deal #${viewingDeal.id}`}</h2>
              <button onClick={() => { setViewingDeal(null); setDealDetail(null); }} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded">
                <ChevronLeft size={20} />
              </button>
            </div>
            <div className="p-6">
              <div className="flex items-center gap-2 mb-4">
                <span className={`px-2 py-1 text-xs rounded-full font-medium ${STAGE_COLORS[viewingDeal.status]}`}>{viewingDeal.status}</span>
                <span className="text-sm font-bold text-gray-900 dark:text-white">{viewingDeal.currency} {viewingDeal.value?.toLocaleString()}</span>
                {viewingDeal.signing_url && viewingDeal.status === 'sent' && (
                  <a href={viewingDeal.signing_url} target="_blank" rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline ml-auto">Signing URL</a>
                )}
              </div>
              <pre className="p-4 bg-gray-50 dark:bg-gray-900/50 rounded-lg border border-gray-200 dark:border-gray-700 text-xs text-gray-700 dark:text-gray-300 whitespace-pre-wrap font-mono max-h-[500px] overflow-y-auto">
                {dealDetail?.contract_content || 'Loading contract...'}
              </pre>
              <div className="flex gap-2 mt-4">
                {viewingDeal.status === 'draft' && (
                  <button onClick={() => handleSend(viewingDeal.id)} className="btn btn-primary flex items-center gap-2 text-sm">
                    <Send size={16} /> Send for Signature
                  </button>
                )}
                {viewingDeal.status === 'sent' && (
                  <button onClick={() => handleSign(viewingDeal.id)} className="btn btn-primary flex items-center gap-2 text-sm">
                    <CheckCircle size={16} /> Simulate Sign
                  </button>
                )}
                {viewingDeal.status === 'signed' && (
                  <button onClick={() => handlePay(viewingDeal.id)} className="btn btn-primary flex items-center gap-2 text-sm">
                    <CreditCard size={16} /> Process Payment
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DealDesk;

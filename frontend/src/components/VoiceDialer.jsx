import React, { useState } from 'react';
import { api } from '../services/api';
import { Phone, PhoneOff, Mic, X, Loader, MessageCircle, AlertCircle, CheckCircle } from 'lucide-react';

function VoiceDialer({ lead, onClose }) {
  const [calling, setCalling] = useState(false);
  const [callResult, setCallResult] = useState(null);
  const [transcribing, setTranscribing] = useState(false);
  const [transcriptResult, setTranscriptResult] = useState(null);
  const [mockTranscript, setMockTranscript] = useState('');

  const startCall = async () => {
    try {
      setCalling(true);
      const result = await api.global.voiceCall(lead.id, lead.phone || '+1234567890');
      setCallResult(result);
      setCalling(false);
    } catch (err) {
      console.error('Call failed:', err);
      setCalling(false);
    }
  };

  const submitTranscript = async () => {
    if (!mockTranscript.trim() || !callResult) return;
    try {
      setTranscribing(true);
      const result = await api.global.transcribeCall(callResult.call_id, mockTranscript);
      setTranscriptResult(result);
    } catch (err) {
      console.error('Transcribe failed:', err);
    } finally {
      setTranscribing(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
      <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full">
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
          <h2 className="text-lg font-bold text-gray-900 dark:text-white flex items-center gap-2">
            <Phone size={20} className="text-green-600" /> Voice Call — {lead.name}
          </h2>
          <button onClick={onClose} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><X size={20} /></button>
        </div>
        <div className="p-6 space-y-4">
          {!callResult ? (
            <div className="text-center space-y-4">
              <div className="w-20 h-20 rounded-full bg-green-100 dark:bg-green-900/30 flex items-center justify-center mx-auto">
                <Phone size={36} className="text-green-600" />
              </div>
              <div>
                <p className="font-semibold text-gray-900 dark:text-white">{lead.name}</p>
                <p className="text-sm text-gray-500 dark:text-gray-400">{lead.phone || 'No phone on file (mock)'} · {lead.company}</p>
              </div>
              <button onClick={startCall} disabled={calling}
                className="btn btn-primary flex items-center gap-2 mx-auto disabled:opacity-50">
                {calling ? <Loader size={18} className="animate-spin" /> : <Phone size={18} />}
                {calling ? 'Calling...' : 'Start Call'}
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className={`p-4 rounded-lg border ${callResult.mocked ? 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800' : 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800'}`}>
                <div className="flex items-center gap-2 mb-2">
                  {callResult.mocked ? <AlertCircle size={18} className="text-yellow-600" /> : <CheckCircle size={18} className="text-green-600" />}
                  <span className="font-medium text-gray-900 dark:text-white">Call {callResult.mocked ? 'Simulated' : 'Initiated'}</span>
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">Call ID: {callResult.call_id}</p>
                <div className="p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg text-sm text-gray-700 dark:text-gray-300 italic">
                  "{callResult.script}"
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">Simulated Transcript</label>
                <textarea value={mockTranscript} onChange={(e) => setMockTranscript(e.target.value)}
                  rows={4} placeholder="Paste or type simulated call transcript here..."
                  className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full" />
                <button onClick={submitTranscript} disabled={transcribing || !mockTranscript.trim()}
                  className="btn btn-primary flex items-center gap-2 mt-2 text-sm disabled:opacity-50">
                  {transcribing ? <Loader size={16} className="animate-spin" /> : <Mic size={16} />}
                  {transcribing ? 'Analyzing...' : 'Analyze Transcript'}
                </button>
              </div>

              {transcriptResult && (
                <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                  <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Call Analysis</h4>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-500">Sentiment</span>
                      <span className="font-medium text-gray-900 dark:text-white">{transcriptResult.sentiment?.label} ({transcriptResult.sentiment?.score})</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Need Score</span>
                      <span className="font-medium text-gray-900 dark:text-white">{transcriptResult.bant?.need}/10</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Authority</span>
                      <span className="font-medium text-gray-900 dark:text-white">{transcriptResult.bant?.authority}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Budget</span>
                      <span className="font-medium text-gray-900 dark:text-white">{transcriptResult.bant?.budget}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-500">Timeline</span>
                      <span className="font-medium text-gray-900 dark:text-white">{transcriptResult.bant?.timeline}</span>
                    </div>
                    <p className="mt-2 p-2 bg-white dark:bg-gray-800 rounded text-xs text-gray-600 dark:text-gray-400">
                      {transcriptResult.summary}
                    </p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default VoiceDialer;

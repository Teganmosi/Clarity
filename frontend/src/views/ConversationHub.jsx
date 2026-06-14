import React, { useState, useEffect, useRef } from 'react';
import { api } from '../services/api';
import VoiceDialer from '../components/VoiceDialer';
import { Send, MessageCircle, User, Bot, AlertTriangle, Phone, X, ChevronRight, DollarSign, Shield, Target, Clock, ThumbsUp, ThumbsDown, Minus, Calendar as CalendarIcon, CheckCircle, Globe, PhoneCall } from 'lucide-react';

function ConversationHub({ user }) {
  const [conversations, setConversations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeConv, setActiveConv] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [bant, setBant] = useState(null);
  const [handoffAlert, setHandoffAlert] = useState(false);
  const [showSlotPicker, setShowSlotPicker] = useState(false);
  const [slots, setSlots] = useState([]);
  const [loadingSlots, setLoadingSlots] = useState(false);
  const [selectedSlot, setSelectedSlot] = useState(null);
  const [bookingResult, setBookingResult] = useState(null);
  const [showVoiceDialer, setShowVoiceDialer] = useState(null);
  const chatEnd = useRef(null);

  useEffect(() => {
    loadConversations();
  }, []);

  useEffect(() => {
    chatEnd.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const loadConversations = async () => {
    try {
      setLoading(true);
      const data = await api.conversation.list();
      setConversations(data?.conversations || []);
    } catch (err) {
      console.error('Error loading conversations:', err);
    } finally {
      setLoading(false);
    }
  };

  const openConversation = async (conv) => {
    setActiveConv(conv);
    setHandoffAlert(false);
    try {
      const data = await api.conversation.get(conv.lead_id);
      setMessages(data?.conversation?.messages || []);
      setBant(data?.conversation?.bant_scores || null);
      if (data?.conversation?.status === 'handed_off') {
        setHandoffAlert(true);
      }
    } catch (err) {
      console.error('Error loading conversation:', err);
    }
  };

  const sendMessage = async () => {
    if (!input.trim() || !activeConv) return;
    const userMsg = input.trim();
    setInput('');
    setMessages((prev) => [...prev, { role: 'user', content: userMsg }]);
    setSending(true);
    try {
      const data = await api.conversation.send(activeConv.lead_id, userMsg);
      setMessages((prev) => [...prev, { role: 'assistant', content: data.response }]);
      setBant(data.bant);
      if (data.handoff) {
        setHandoffAlert(true);
      }
      loadConversations();
    } catch (err) {
      console.error('Error sending:', err);
    } finally {
      setSending(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const getSentimentIcon = (label) => {
    if (label === 'Positive') return <ThumbsUp size={16} className="text-green-600" />;
    if (label === 'Negative') return <ThumbsDown size={16} className="text-red-600" />;
    return <Minus size={16} className="text-gray-500" />;
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading conversations...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Conversation Hub</h1>
        <p className="text-gray-600 dark:text-gray-400">AI qualification agent — BANT-powered lead conversations</p>
      </div>

      {handoffAlert && (
        <div className="mb-6 p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg flex items-center gap-3">
          <AlertTriangle size={24} className="text-red-600 flex-shrink-0" />
          <div>
            <p className="font-semibold text-red-800 dark:text-red-200">Human Handoff Recommended</p>
            <p className="text-sm text-red-600 dark:text-red-400">
              This lead qualifies for immediate human intervention. Assign a sales rep now.
            </p>
          </div>
          <button onClick={() => setHandoffAlert(false)} className="ml-auto p-1.5 text-red-600 hover:bg-red-100 dark:hover:bg-red-900/30 rounded">
            <X size={18} />
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Conversation List */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden lg:col-span-1">
          <div className="p-4 border-b border-gray-200 dark:border-gray-700">
            <h2 className="font-semibold text-gray-900 dark:text-white">Active Conversations</h2>
          </div>
          {conversations.length === 0 ? (
            <div className="p-4 text-sm text-gray-500 dark:text-gray-400 text-center">No conversations yet.</div>
          ) : (
            <div className="divide-y divide-gray-200 dark:divide-gray-700 max-h-[600px] overflow-y-auto">
              {conversations.map((conv) => (
                <button key={conv.id} onClick={() => openConversation(conv)}
                  className={`w-full text-left p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50 transition-colors ${activeConv?.id === conv.id ? 'bg-blue-50 dark:bg-blue-900/20' : ''}`}>
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium text-gray-900 dark:text-white text-sm">{conv.lead_name}</span>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      conv.status === 'active' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' :
                      conv.status === 'handed_off' ? 'bg-red-100 dark:bg-red-900/30 text-red-700' :
                      'bg-gray-100 dark:bg-gray-700 text-gray-500'
                    }`}>{conv.status}</span>
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400 truncate">{conv.last_message}</p>
                  <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">{conv.message_count} messages</p>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Chat Window */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden lg:col-span-1 flex flex-col">
          {activeConv ? (
            <>
              <div className="p-4 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/30">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900 dark:text-white">{activeConv.lead_name}</h3>
                    <p className="text-xs text-gray-500 dark:text-gray-400">{activeConv.lead_company} · {activeConv.channel}</p>
                  </div>
                  {bant?.sentiment && (
                    <div className="flex items-center gap-1 text-xs">
                      {getSentimentIcon(bant.sentiment)}
                      <span className="text-gray-600 dark:text-gray-400">{bant.sentiment}</span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex-1 p-4 space-y-4 overflow-y-auto max-h-[400px]">
                {messages.map((msg, i) => (
                  <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                    <div className={`flex gap-2 max-w-[80%] ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                      <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-primary-100 dark:bg-primary-900/30' : 'bg-gray-100 dark:bg-gray-700'}`}>
                        {msg.role === 'user' ? <User size={16} className="text-primary-600" /> : <Bot size={16} className="text-gray-600 dark:text-gray-400" />}
                      </div>
                      <div className={`p-3 rounded-lg text-sm ${
                        msg.role === 'user'
                          ? 'bg-primary-600 text-white rounded-tr-none'
                          : 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white rounded-tl-none'
                      }`}>
                        {msg.content}
                      </div>
                    </div>
                  </div>
                ))}
                {sending && (
                  <div className="flex justify-start">
                    <div className="flex gap-2">
                      <div className="w-8 h-8 rounded-full bg-gray-100 dark:bg-gray-700 flex items-center justify-center"><Bot size={16} className="text-gray-600" /></div>
                      <div className="p-3 rounded-lg bg-gray-100 dark:bg-gray-700">
                        <div className="flex gap-1">
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                          <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                <div ref={chatEnd} />
              </div>

              {activeConv.status !== 'handed_off' ? (
                <div className="p-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                  <button onClick={openSlotPicker}
                    className="btn btn-secondary w-full flex items-center justify-center gap-2 text-sm py-2 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-600">
                    <CalendarIcon size={16} /> Schedule Meeting
                  </button>
                  <div className="flex gap-2">
                    <textarea value={input} onChange={(e) => setInput(e.target.value)} onKeyDown={handleKeyDown}
                      placeholder="Type your message..."
                      rows={2}
                      className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 flex-1 resize-none" />
                    <button onClick={sendMessage} disabled={sending || !input.trim()}
                      className="btn btn-primary flex items-center gap-2 self-end disabled:opacity-50">
                      <Send size={16} />
                    </button>
                  </div>
                </div>
              ) : (
                <div className="p-4 border-t border-gray-200 dark:border-gray-700 bg-red-50 dark:bg-red-900/20 text-center text-sm text-red-700 dark:text-red-300">
                  Handed off to human agent
                </div>
              )}
            </>
          ) : (
            <div className="flex-1 flex items-center justify-center text-gray-500 dark:text-gray-400 p-8 text-center">
              <div>
                <MessageCircle size={48} className="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                <p>Select a conversation to start chatting</p>
              </div>
            </div>
          )}
        </div>

          {/* Voice Dialer */}
          {showVoiceDialer && (
            <VoiceDialer lead={showVoiceDialer} onClose={() => setShowVoiceDialer(null)} />
          )}

          {/* BANT Dashboard */}
        <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 lg:col-span-1">
          <h3 className="font-semibold text-gray-900 dark:text-white mb-4">BANT Qualification</h3>
          {bant ? (
            <div className="space-y-4">
              <BantRow icon={<DollarSign size={18} className="text-green-600" />} label="Budget" value={bant.budget || 'Unknown'} />
              <BantRow icon={<Shield size={18} className="text-blue-600" />} label="Authority" value={bant.authority || 'Unknown'} />
              <BantRow icon={<Target size={18} className="text-purple-600" />} label="Need" value={`${bant.need || 0}/10`} score />
              <BantRow icon={<Clock size={18} className="text-yellow-600" />} label="Timeline" value={bant.timeline || 'Unknown'} />
              <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-gray-700 dark:text-gray-300">Sentiment</span>
                  <div className="flex items-center gap-1">
                    {getSentimentIcon(bant.sentiment)}
                    <span className="text-sm font-medium text-gray-900 dark:text-white">{bant.sentiment}</span>
                  </div>
                </div>
                {handoffAlert && (
                  <div className="mt-3 p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800 text-center">
                    <p className="text-sm font-semibold text-red-700 dark:text-red-300">🔴 Handoff Required</p>
                    <p className="text-xs text-red-600 dark:text-red-400 mt-1">High BANT score or negative sentiment detected</p>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-gray-500 dark:text-gray-400 text-center py-8">
              {activeConv ? 'Send a message to start BANT extraction' : 'Select a conversation to view BANT data'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
}

  const openSlotPicker = async () => {
    if (!activeConv) return;
    setShowSlotPicker(true);
    setSelectedSlot(null);
    setBookingResult(null);
    setLoadingSlots(true);
    try {
      const today = new Date().toISOString().split('T')[0];
      const data = await api.scheduler.getSlots(today, 30, 'UTC');
      setSlots(data?.slots || []);
    } catch (err) {
      console.error('Error loading slots:', err);
    } finally {
      setLoadingSlots(false);
    }
  };

  const bookSlot = async () => {
    if (!selectedSlot || !activeConv) return;
    try {
      const data = await api.scheduler.book(activeConv.lead_id, selectedSlot.utc, 30, 'UTC');
      setBookingResult(data);
      setMessages((prev) => [...prev, {
        role: 'assistant',
        content: `Meeting booked! ${selectedSlot.display}. Join link: ${data.meeting_link}`,
      }]);
      loadConversations();
    } catch (err) {
      alert('Failed to book meeting');
    }
  };

  return (
    <>
      {/* Slot Picker Modal */}
      {showSlotPicker && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-2xl max-w-lg w-full max-h-[80vh] overflow-y-auto">
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 px-6 py-4 flex items-center justify-between">
              <h2 className="text-lg font-bold text-gray-900 dark:text-white">Select a Time Slot</h2>
              <button onClick={() => setShowSlotPicker(false)} className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded"><X size={20} /></button>
            </div>
            <div className="p-6">
              {bookingResult ? (
                <div className="text-center space-y-4">
                  <CheckCircle size={48} className="mx-auto text-green-600" />
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">Meeting Booked!</h3>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{selectedSlot?.display}</p>
                  {bookingResult.meeting_link && (
                    <a href={bookingResult.meeting_link} target="_blank" rel="noopener noreferrer"
                      className="btn btn-primary inline-flex items-center gap-2">
                      <CalendarIcon size={16} /> Join Meeting
                    </a>
                  )}
                  <button onClick={() => {
                    const blob = new Blob([bookingResult.ics_content], { type: 'text/calendar' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a'); a.href = url;
                    a.download = `meeting-${bookingResult.meeting_id}.ics`;
                    a.click(); URL.revokeObjectURL(url);
                  }} className="btn btn-secondary bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200">
                    Download .ics
                  </button>
                  <button onClick={() => { setShowSlotPicker(false); setBookingResult(null); }}
                    className="block mx-auto text-sm text-gray-500 hover:text-gray-700 mt-4">Close</button>
                </div>
              ) : loadingSlots ? (
                <p className="text-center text-gray-500 dark:text-gray-400 py-8">Loading available slots...</p>
              ) : slots.length === 0 ? (
                <p className="text-center text-gray-500 dark:text-gray-400 py-8">No available slots for today.</p>
              ) : (
                <div className="space-y-2">
                  {slots.map((slot, i) => (
                    <button key={i} onClick={() => setSelectedSlot(slot)}
                      className={`w-full text-left p-3 rounded-lg border text-sm transition-colors ${
                        selectedSlot?.utc === slot.utc
                          ? 'bg-primary-50 dark:bg-primary-900/20 border-primary-500 text-primary-700 dark:text-primary-300'
                          : 'bg-gray-50 dark:bg-gray-700/50 border-gray-200 dark:border-gray-600 text-gray-900 dark:text-white hover:border-primary-300'
                      }`}>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">{slot.display}</span>
                        <span className="text-xs text-gray-500 dark:text-gray-400">{slot.duration_minutes} min</span>
                      </div>
                    </button>
                  ))}
                  <button onClick={bookSlot} disabled={!selectedSlot}
                    className="btn btn-primary w-full mt-4 disabled:opacity-50">
                    {selectedSlot ? `Confirm ${selectedSlot.display}` : 'Select a slot'}
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </>
  );
}

function BantRow({ icon, label, value, score }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
      <div className="flex items-center gap-2">
        {icon}
        <span className="text-sm text-gray-700 dark:text-gray-300">{label}</span>
      </div>
      <span className={`text-sm font-semibold ${score ? 'text-purple-700 dark:text-purple-300' : 'text-gray-900 dark:text-white'}`}>
        {value}
      </span>
    </div>
  );
}

export default ConversationHub;

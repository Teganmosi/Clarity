import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Lightbulb, TrendingUp, BarChart3, FlaskConical, CheckCircle, AlertCircle, RefreshCw, Zap, Target } from 'lucide-react';

function LearningHub({ user }) {
  const [insights, setInsights] = useState(null);
  const [abTests, setAbTests] = useState([]);
  const [optimizeResult, setOptimizeResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('insights');
  const [abForm, setAbForm] = useState({ name: '', aSubject: '', bSubject: '', aBody: '', bBody: '' });
  const [showABForm, setShowABForm] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [ins, tests] = await Promise.all([
        api.learning.getInsights(),
        api.learning.listABTests(),
      ]);
      setInsights(ins);
      setAbTests(tests?.tests || []);
    } catch (err) {
      console.error('Error loading learning data:', err);
    } finally {
      setLoading(false);
    }
  };

  const runOptimize = async () => {
    try {
      const result = await api.learning.optimize(false);
      setOptimizeResult(result);
    } catch (err) {
      console.error('Error optimizing:', err);
    }
  };

  const createABTest = async (e) => {
    e.preventDefault();
    try {
      await api.learning.createABTest(abForm.name, abForm.aSubject, abForm.bSubject, abForm.aBody, abForm.bBody);
      setShowABForm(false);
      setAbForm({ name: '', aSubject: '', bSubject: '', aBody: '', bBody: '' });
      loadData();
    } catch (err) {
      alert('Failed to create A/B test');
    }
  };

  const checkWinner = async (testId) => {
    try {
      const result = await api.learning.getABTestWinner(testId);
      alert(`Test ${result.status}: ${result.winner ? `Winner is ${result.winner} (confidence: ${(result.confidence * 100).toFixed(1)}%)` : 'No clear winner yet'}`);
      loadData();
    } catch (err) {
      console.error('Error checking winner:', err);
    }
  };

  if (loading) {
    return <div className="p-8 text-center text-gray-600 dark:text-gray-400">Loading learning hub...</div>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">Learning & Optimization</h1>
        <p className="text-gray-600 dark:text-gray-400">Self-improving system — pattern mining, weight optimization, A/B testing</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 mb-6 bg-gray-100 dark:bg-gray-800 rounded-lg p-1 w-fit">
        {[
          { id: 'insights', label: 'Insights', icon: Lightbulb },
          { id: 'optimize', label: 'Weight Tuner', icon: Zap },
          { id: 'abtests', label: 'A/B Tests', icon: FlaskConical },
        ].map((tab) => {
          const Icon = tab.icon;
          return (
            <button key={tab.id} onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-md text-sm font-medium transition-colors ${activeTab === tab.id ? 'bg-white dark:bg-gray-700 text-gray-900 dark:text-white shadow-sm' : 'text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-white'}`}>
              <Icon size={16} /> {tab.label}
            </button>
          );
        })}
      </div>

      {/* Insights Tab */}
      {activeTab === 'insights' && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Total Outcomes</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">{insights?.total_outcomes || 0}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Insights Available</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">{insights?.insights?.length || 0}</p>
            </div>
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6 text-center">
              <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">A/B Tests</p>
              <p className="text-3xl font-bold text-gray-900 dark:text-white">{abTests.length}</p>
            </div>
          </div>

          {insights?.insights?.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {insights.insights.map((insight, i) => (
                <div key={i} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
                  <div className="flex items-center gap-2 mb-3">
                    {insight.type === 'channel' ? <TrendingUp size={20} className="text-blue-600" /> :
                     insight.type === 'funding' ? <Target size={20} className="text-purple-600" /> :
                     <BarChart3 size={20} className="text-green-600" />}
                    <h3 className="font-semibold text-gray-900 dark:text-white">{insight.title}</h3>
                    <span className="ml-auto px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                      {(insight.confidence * 100).toFixed(0)}% confidence
                    </span>
                  </div>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mb-3">{insight.detail}</p>
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-xs font-medium text-blue-700 dark:text-blue-300">Recommendation</p>
                    <p className="text-sm text-blue-600 dark:text-blue-400">{insight.recommendation}</p>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
              <Lightbulb size={48} className="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
              <p>{insights?.message || 'Not enough outcome data yet.'}</p>
            </div>
          )}
        </div>
      )}

      {/* Weight Tuner Tab */}
      {activeTab === 'optimize' && (
        <div className="space-y-4">
          <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">Intent Signal Weight Optimization</h2>
            <p className="text-sm text-gray-600 dark:text-gray-400 mb-4">
              Analyzes which intent signals correlate most with positive outcomes and suggests weight adjustments.
            </p>
            <button onClick={runOptimize} className="btn btn-primary flex items-center gap-2">
              <RefreshCw size={16} /> Run Optimization
            </button>

            {optimizeResult && (
              <div className="mt-6 space-y-4">
                <div className={`p-4 rounded-lg border ${optimizeResult.status === 'optimized' || optimizeResult.status === 'dry_run' ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' : 'bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800'}`}>
                  <p className="font-semibold text-gray-900 dark:text-white capitalize">{optimizeResult.status}</p>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{optimizeResult.reason || `${optimizeResult.samples_analyzed} outcomes analyzed`}</p>
                  {optimizeResult.note && <p className="text-xs text-gray-500 mt-1">{optimizeResult.note}</p>}
                </div>
                {optimizeResult.suggested_weights && (
                  <div>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Weight Adjustments</h3>
                    <div className="space-y-2">
                      {Object.entries(optimizeResult.suggested_weights).map(([signal, weight]) => {
                        const original = optimizeResult.original_weights?.[signal];
                        const diff = original ? weight - original : 0;
                        return (
                          <div key={signal} className="flex items-center justify-between p-3 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                            <span className="text-sm text-gray-700 dark:text-gray-300 capitalize">{signal.replace(/_/g, ' ')}</span>
                            <div className="flex items-center gap-2">
                              {original && <span className="text-xs text-gray-400 line-through">{original}</span>}
                              <span className="text-sm font-bold text-gray-900 dark:text-white">{weight}</span>
                              {diff !== 0 && (
                                <span className={`text-xs font-medium ${diff > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                  {diff > 0 ? '+' : ''}{diff}
                                </span>
                              )}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* A/B Tests Tab */}
      {activeTab === 'abtests' && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">A/B Tests</h2>
            <button onClick={() => setShowABForm(!showABForm)} className="btn btn-primary flex items-center gap-2 text-sm py-1.5">
              <FlaskConical size={16} /> New Test
            </button>
          </div>

          {showABForm && (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-6">
              <form onSubmit={createABTest} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">Test Name</label>
                  <input type="text" required value={abForm.name} onChange={(e) => setAbForm({ ...abForm, name: e.target.value })}
                    className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full" placeholder="e.g. Subject Line Test #1" />
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                    <p className="text-sm font-medium text-blue-700 dark:text-blue-300 mb-2">Variant A</p>
                    <input type="text" value={abForm.aSubject} onChange={(e) => setAbForm({ ...abForm, aSubject: e.target.value })}
                      className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full mb-2" placeholder="Subject A" />
                  </div>
                  <div className="p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
                    <p className="text-sm font-medium text-purple-700 dark:text-purple-300 mb-2">Variant B</p>
                    <input type="text" value={abForm.bSubject} onChange={(e) => setAbForm({ ...abForm, bSubject: e.target.value })}
                      className="input bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-900 dark:text-gray-100 w-full mb-2" placeholder="Subject B" />
                  </div>
                </div>
                <div className="flex gap-2">
                  <button type="submit" className="btn btn-primary">Start Test</button>
                  <button type="button" onClick={() => setShowABForm(false)} className="btn btn-secondary bg-white dark:bg-gray-700 text-gray-700 dark:text-gray-200 border-gray-300 dark:border-gray-600">Cancel</button>
                </div>
              </form>
            </div>
          )}

          {abTests.length === 0 ? (
            <div className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-8 text-center text-gray-500 dark:text-gray-400">
              <FlaskConical size={48} className="mx-auto mb-4 text-gray-300 dark:text-gray-600" />
              <p>No A/B tests created yet.</p>
            </div>
          ) : (
            <div className="space-y-3">
              {abTests.map((test) => (
                <div key={test.id} className="bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg p-4 flex items-center justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="font-semibold text-gray-900 dark:text-white">{test.name}</h3>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${test.status === 'running' ? 'bg-green-100 dark:bg-green-900/30 text-green-700' : 'bg-gray-100 dark:bg-gray-700 text-gray-500'}`}>
                        {test.status}
                      </span>
                      {test.winner && (
                        <span className="px-2 py-0.5 text-xs rounded-full bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300">
                          Winner: {test.winner}
                        </span>
                      )}
                    </div>
                    <p className="text-xs text-gray-500 dark:text-gray-400">Metric: {test.metric} · A: "{test.variant_a?.subject}" vs B: "{test.variant_b?.subject}"</p>
                  </div>
                  <button onClick={() => checkWinner(test.id)}
                    className="btn btn-secondary text-sm py-1 px-3 bg-white dark:bg-gray-700 border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-200">
                    Check Winner
                  </button>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default LearningHub;

import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { api } from './services/api';
import Login from './components/Login';
import Dashboard from './components/Dashboard';
import LeadsList from './components/LeadsList';
import Analytics from './components/Analytics';
import Integrations from './components/Integrations';
import AnalyticsDashboard from './views/AnalyticsDashboard';
import WorkflowBuilder from './components/WorkflowBuilder';
import OutreachCenter from './views/OutreachCenter';
import SuppressionManager from './components/SuppressionManager';
import ConversationHub from './views/ConversationHub';
import MeetingManager from './components/MeetingManager';
import OrchestrationDashboard from './views/OrchestrationDashboard';
import LearningHub from './views/LearningHub';
import Header from './components/Header';
import { ThemeProvider } from './context/ThemeContext';

/**
 * Main Application Component
 * Handles routing and authentication state
 */
function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check if user is logged in on mount
    const storedUser = localStorage.getItem('user');
    if (storedUser) {
      setUser(JSON.parse(storedUser));
    }
    setLoading(false);
  }, []);

  const handleLogin = (userData) => {
    setUser(userData.user);
  };

  const handleLogout = () => {
    api.auth.logout();
    setUser(null);
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="flex flex-col items-center space-y-4">
          <div className="w-12 h-12 border-4 border-gray-900 border-t-transparent rounded-full animate-spin"></div>
          <div className="text-xl text-gray-600">Loading...</div>
        </div>
      </div>
    );
  }

  if (!user) {
    return <Login onLogin={handleLogin} />;
  }

  return (
    <ThemeProvider>
      <Router>
        <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
          <Header user={user} onLogout={handleLogout} />
          <main className="container mx-auto px-4 py-8">
            <Routes>
              <Route path="/" element={<Navigate to="/dashboard" replace />} />
              <Route path="/dashboard" element={<Dashboard user={user} />} />
              <Route path="/leads" element={<LeadsList user={user} />} />
              <Route path="/analytics" element={<Analytics user={user} />} />
              <Route path="/integrations" element={<Integrations user={user} />} />
              <Route path="/analytics-dashboard" element={<AnalyticsDashboard user={user} />} />
              <Route path="/workflows" element={<WorkflowBuilder user={user} />} />
              <Route path="/outreach" element={<OutreachCenter user={user} />} />
              <Route path="/suppressions" element={<SuppressionManager user={user} />} />
              <Route path="/conversations" element={<ConversationHub user={user} />} />
              <Route path="/meetings" element={<MeetingManager user={user} />} />
              <Route path="/orchestration" element={<OrchestrationDashboard user={user} />} />
              <Route path="/learning" element={<LearningHub user={user} />} />
            </Routes>
          </main>
        </div>
      </Router>
    </ThemeProvider>
  );

}

export default App;

import { useState, useEffect, useCallback } from 'react';
import { AuthModal } from './components/Auth/AuthModal';
import { Sidebar } from './components/Sidebar/Sidebar';
import { ChatCanvas } from './components/Chat/ChatCanvas';
import { PromptBar } from './components/Chat/PromptBar';
import { IntegrationsModal } from './components/Integrations/IntegrationsModal';
import { api } from './services/api';
import { Thread, Message, HITLEvent, IntegrationStatus } from './types';

export default function App() {
  const [token, setToken] = useState<string | null>(localStorage.getItem('major1_token'));
  const [userEmail, setUserEmail] = useState<string | null>(localStorage.getItem('major1_email'));

  const [threads, setThreads] = useState<Thread[]>([]);
  const [activeThreadId, setActiveThreadId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [pendingHITL, setPendingHITL] = useState<HITLEvent | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [hitlLoading, setHitlLoading] = useState<boolean>(false);

  const [integrations, setIntegrations] = useState<IntegrationStatus>({
    github_connected: false,
    gmail_connected: false,
  });
  const [isIntegrationsOpen, setIsIntegrationsOpen] = useState<boolean>(false);

  // ── Load Threads ────────────────────────────────────────────────────────
  const fetchThreads = useCallback(async (authToken: string) => {
    const res = await api.listThreads(authToken);
    if (!res.error && res.threads) {
      setThreads(res.threads);
      if (res.threads.length > 0 && !activeThreadId) {
        setActiveThreadId(String(res.threads[0].thread_id));
      }
    }
  }, [activeThreadId]);

  // ── Load Integrations ──────────────────────────────────────────────────
  const fetchIntegrations = useCallback(async (authToken: string) => {
    const status = await api.getIntegrationStatus(authToken);
    setIntegrations(status);
  }, []);

  // ── Load Conversation History ──────────────────────────────────────────
  const fetchHistory = useCallback(async (threadId: string, authToken: string) => {
    const history = await api.loadConversation(threadId, authToken);
    setMessages(history);
    setPendingHITL(null);
  }, []);

  // Sync state on token change
  useEffect(() => {
    if (token) {
      fetchThreads(token);
      fetchIntegrations(token);
    }
  }, [token, fetchThreads, fetchIntegrations]);

  // Sync conversation on activeThreadId change
  useEffect(() => {
    if (token && activeThreadId) {
      fetchHistory(activeThreadId, token);
    }
  }, [activeThreadId, token, fetchHistory]);

  // ── Auth Handlers ──────────────────────────────────────────────────────
  const handleAuthSuccess = (newToken: string, email: string) => {
    localStorage.setItem('major1_token', newToken);
    localStorage.setItem('major1_email', email);
    setToken(newToken);
    setUserEmail(email);
  };

  const handleLogout = () => {
    localStorage.removeItem('major1_token');
    localStorage.removeItem('major1_email');
    setToken(null);
    setUserEmail(null);
    setThreads([]);
    setActiveThreadId(null);
    setMessages([]);
    setPendingHITL(null);
  };

  // ── Thread Handlers ────────────────────────────────────────────────────
  const handleNewThread = async () => {
    if (!token) return;
    const res = await api.createThread('New Conversation', token);
    if (res.thread_id) {
      const newId = String(res.thread_id);
      await fetchThreads(token);
      setActiveThreadId(newId);
      setMessages([]);
      setPendingHITL(null);
    }
  };

  const handleSelectThread = (threadId: string) => {
    if (threadId !== activeThreadId) {
      setActiveThreadId(threadId);
    }
  };

  const handleDeleteThread = async (threadId: string) => {
    if (!token) return;
    const ok = await api.deleteThread(threadId, token);
    if (ok) {
      const remaining = threads.filter((t) => String(t.thread_id) !== String(threadId));
      setThreads(remaining);
      if (activeThreadId === threadId) {
        if (remaining.length > 0) {
          setActiveThreadId(String(remaining[0].thread_id));
        } else {
          setActiveThreadId(null);
          setMessages([]);
        }
      }
    }
  };

  // ── Chat & Prompt Handlers ─────────────────────────────────────────────
  const handleSendPrompt = async (prompt: string) => {
    if (!token) return;

    // Append user message immediately
    const userMsg: Message = { role: 'user', content: prompt };
    setMessages((prev) => [...prev, userMsg]);
    setLoading(true);

    try {
      const res = await api.askQuestion(prompt, activeThreadId, token);
      if (res.thread_id && res.thread_id !== activeThreadId) {
        setActiveThreadId(String(res.thread_id));
        fetchThreads(token);
      }

      if (res.status === 'pending' && res.hitl_event) {
        setPendingHITL({
          thread_id: res.thread_id,
          hitl_event: res.hitl_event,
        });
      } else {
        setPendingHITL(null);
        if (res.answer) {
          const assistantMsg: Message = {
            role: 'assistant',
            content: res.answer,
            tools_called: res.tools_called,
          };
          setMessages((prev) => [...prev, assistantMsg]);
        }
      }
    } finally {
      setLoading(false);
    }
  };

  // ── HITL Handlers ──────────────────────────────────────────────────────
  const handleResumeHITL = async (approval: 'yes' | 'no') => {
    if (!token || !pendingHITL) return;
    setHitlLoading(true);

    try {
      const res = await api.resumeAction(pendingHITL.thread_id, approval, token);
      if (res.status === 'done') {
        const assistantMsg: Message = {
          role: 'assistant',
          content: res.answer || (approval === 'yes' ? 'Action approved and executed.' : 'Action rejected.'),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        setPendingHITL(null);
      } else if (res.status === 'pending' && res.hitl_event) {
        // Subsequent chained HITL event
        setPendingHITL({
          thread_id: res.thread_id,
          hitl_event: res.hitl_event,
        });
      }
    } finally {
      setHitlLoading(false);
    }
  };

  if (!token) {
    return <AuthModal onSuccess={handleAuthSuccess} />;
  }

  const activeThread = threads.find((t) => String(t.thread_id) === String(activeThreadId));
  const activeTitle = activeThread?.thread_title || 'Active Conversation';

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-white">
      {/* Sidebar Navigation */}
      <Sidebar
        userEmail={userEmail || 'operator'}
        threads={threads}
        activeThreadId={activeThreadId}
        integrations={integrations}
        onSelectThread={handleSelectThread}
        onNewThread={handleNewThread}
        onDeleteThread={handleDeleteThread}
        onOpenIntegrations={() => setIsIntegrationsOpen(true)}
        onLogout={handleLogout}
      />

      {/* Main Chat Workspace */}
      <div className="flex-1 flex flex-col h-screen relative overflow-hidden">
        <ChatCanvas
          threadTitle={activeTitle}
          messages={messages}
          pendingHITL={pendingHITL}
          loading={loading}
          onApproveHITL={() => handleResumeHITL('yes')}
          onRejectHITL={() => handleResumeHITL('no')}
          hitlLoading={hitlLoading}
        />

        {/* Floating Action Prompt Bar */}
        <PromptBar
          onSend={handleSendPrompt}
          disabled={loading || pendingHITL !== null}
        />
      </div>

      {/* MCP Integrations Drawer / Modal */}
      {isIntegrationsOpen && (
        <IntegrationsModal
          token={token}
          integrations={integrations}
          onClose={() => setIsIntegrationsOpen(false)}
          onRefresh={() => fetchIntegrations(token)}
        />
      )}
    </div>
  );
}

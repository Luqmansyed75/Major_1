import { AskResponse, IntegrationStatus, Message, Thread } from '../types';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

function getHeaders(token?: string) {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  return headers;
}

export const api = {
  // Auth
  async login(email: string, password: string): Promise<{ access_token?: string; error?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { error: data.detail || 'Login failed' };
      }
      return { access_token: data.access_token };
    } catch (err: any) {
      return { error: `Cannot reach backend at ${API_BASE_URL}. Ensure FastAPI is running.` };
    }
  },

  async register(email: string, password: string): Promise<{ access_token?: string; error?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/auth/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      });
      const data = await res.json();
      if (!res.ok) {
        return { error: data.detail || 'Registration failed' };
      }
      return { access_token: data.access_token };
    } catch (err: any) {
      return { error: `Cannot reach backend at ${API_BASE_URL}. Ensure FastAPI is running.` };
    }
  },

  // Threads
  async listThreads(token: string): Promise<{ threads: Thread[]; error?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/threads`, {
        headers: getHeaders(token),
      });
      const data = await res.json();
      if (!res.ok) return { threads: [], error: data.detail };
      return { threads: data.threads || [] };
    } catch (err: any) {
      return { threads: [], error: err.message };
    }
  },

  async createThread(title: string, token: string): Promise<{ thread_id?: string; thread_title?: string; error?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/threads`, {
        method: 'POST',
        headers: getHeaders(token),
        body: JSON.stringify({ thread_title: title }),
      });
      const data = await res.json();
      if (!res.ok) return { error: data.detail };
      return { thread_id: String(data.thread_id), thread_title: data.thread_title };
    } catch (err: any) {
      return { error: err.message };
    }
  },

  async loadConversation(threadId: string, token: string): Promise<Message[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/chat/history/${threadId}`, {
        headers: getHeaders(token),
      });
      if (!res.ok) return [];
      const data = await res.json();
      return Array.isArray(data) ? data : [];
    } catch {
      return [];
    }
  },

  async deleteThread(threadId: string, token: string): Promise<boolean> {
    try {
      const res = await fetch(`${API_BASE_URL}/threads/${threadId}`, {
        method: 'DELETE',
        headers: getHeaders(token),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  // Chat & HITL
  async askQuestion(question: string, threadId: string | null, token: string): Promise<AskResponse> {
    try {
      const res = await fetch(`${API_BASE_URL}/chat/ask`, {
        method: 'POST',
        headers: getHeaders(token),
        body: JSON.stringify({
          question,
          ...(threadId ? { thread_id: threadId } : {}),
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          status: 'done',
          thread_id: threadId || '',
          answer: `⚠️ Error: ${data.detail || 'Failed to process request'}`,
        };
      }
      return data;
    } catch (err: any) {
      return {
        status: 'done',
        thread_id: threadId || '',
        answer: `❌ Connection error with backend: ${err.message}`,
      };
    }
  },

  async resumeAction(threadId: string, approval: 'yes' | 'no', token: string): Promise<AskResponse> {
    try {
      const res = await fetch(`${API_BASE_URL}/chat/resume`, {
        method: 'POST',
        headers: getHeaders(token),
        body: JSON.stringify({
          thread_id: threadId,
          approval,
        }),
      });
      const data = await res.json();
      if (!res.ok) {
        return {
          status: 'done',
          thread_id: threadId,
          answer: `⚠️ Error: ${data.detail || 'Failed to resume action'}`,
        };
      }
      return data;
    } catch (err: any) {
      return {
        status: 'done',
        thread_id: threadId,
        answer: `❌ Connection error with backend: ${err.message}`,
      };
    }
  },

  // Integrations
  async getIntegrationStatus(token: string): Promise<IntegrationStatus> {
    try {
      const res = await fetch(`${API_BASE_URL}/integrations/status`, {
        headers: getHeaders(token),
      });
      if (res.ok) {
        return await res.json();
      }
      return { github_connected: false, gmail_connected: false };
    } catch {
      return { github_connected: false, gmail_connected: false };
    }
  },

  async saveGithubToken(githubToken: string, token: string): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/integrations/github`, {
        method: 'POST',
        headers: getHeaders(token),
        body: JSON.stringify({ github_token: githubToken }),
      });
      const data = await res.json();
      if (!res.ok) return { success: false, error: data.detail };
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message };
    }
  },

  async saveGmailToken(gmailTokenJson: string, token: string): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/integrations/gmail`, {
        method: 'POST',
        headers: getHeaders(token),
        body: JSON.stringify({ gmail_token_json: gmailTokenJson }),
      });
      const data = await res.json();
      if (!res.ok) return { success: false, error: data.detail };
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message };
    }
  },

  async disconnectIntegration(service: 'github' | 'gmail', token: string): Promise<{ success: boolean; error?: string }> {
    try {
      const res = await fetch(`${API_BASE_URL}/integrations/${service}`, {
        method: 'DELETE',
        headers: getHeaders(token),
      });
      const data = await res.json();
      if (!res.ok) return { success: false, error: data.detail };
      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message };
    }
  },
};

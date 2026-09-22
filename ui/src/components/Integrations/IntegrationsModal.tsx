import React, { useState } from 'react';
import { 
  X, GitBranch, Mail, CheckCircle2, XCircle, 
  Key, AlertCircle, Loader2, Info
} from 'lucide-react';
import { IntegrationStatus } from '../../types';
import { api } from '../../services/api';

interface IntegrationsModalProps {
  token: string;
  integrations: IntegrationStatus;
  onClose: () => void;
  onRefresh: () => void;
}

export const IntegrationsModal: React.FC<IntegrationsModalProps> = ({
  token,
  integrations,
  onClose,
  onRefresh,
}) => {
  const [ghToken, setGhToken] = useState('');
  const [gmailJson, setGmailJson] = useState('');
  const [loadingGh, setLoadingGh] = useState(false);
  const [loadingGm, setLoadingGm] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  const handleConnectGitHub = async () => {
    if (!ghToken.trim()) {
      setError('Please provide a valid GitHub Personal Access Token.');
      return;
    }
    setError(null);
    setLoadingGh(true);
    const res = await api.saveGithubToken(ghToken.trim(), token);
    setLoadingGh(false);
    if (!res.success) {
      setError(res.error || 'Failed to save GitHub token.');
    } else {
      setSuccess('✅ GitHub MCP connected successfully!');
      setGhToken('');
      onRefresh();
    }
  };

  const handleDisconnectGitHub = async () => {
    setError(null);
    setLoadingGh(true);
    const res = await api.disconnectIntegration('github', token);
    setLoadingGh(false);
    if (!res.success) {
      setError(res.error || 'Failed to disconnect GitHub.');
    } else {
      setSuccess('GitHub integration disconnected.');
      onRefresh();
    }
  };

  const handleConnectGmail = async () => {
    if (!gmailJson.trim()) {
      setError('Please paste your Gmail token.json content.');
      return;
    }
    try {
      JSON.parse(gmailJson.trim());
    } catch {
      setError('Invalid JSON format. Please paste the exact JSON from token.json.');
      return;
    }

    setError(null);
    setLoadingGm(true);
    const res = await api.saveGmailToken(gmailJson.trim(), token);
    setLoadingGm(false);
    if (!res.success) {
      setError(res.error || 'Failed to save Gmail token.');
    } else {
      setSuccess('✅ Gmail MCP connected successfully!');
      setGmailJson('');
      onRefresh();
    }
  };

  const handleDisconnectGmail = async () => {
    setError(null);
    setLoadingGm(true);
    const res = await api.disconnectIntegration('gmail', token);
    setLoadingGm(false);
    if (!res.success) {
      setError(res.error || 'Failed to disconnect Gmail.');
    } else {
      setSuccess('Gmail integration disconnected.');
      onRefresh();
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-md animate-fadeIn">
      <div className="relative w-full max-w-2xl bg-white border border-brand-100 rounded-2xl shadow-stitch-frosted p-6 text-slate-800 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-lg font-bold font-sans text-slate-900">
              Model Context Protocol (MCP) Integrations
            </h3>
            <p className="text-xs text-slate-500">
              Bind your personal workspace tools to the autonomous LangGraph agent.
            </p>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Notifications */}
        {error && (
          <div className="mt-4 p-3 rounded-xl bg-red-50 border border-red-200 text-red-700 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}
        {success && (
          <div className="mt-4 p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0 text-emerald-600" />
            <span>{success}</span>
          </div>
        )}

        {/* ── Integration 1: GitHub ───────────────────────────────────── */}
        <div className="mt-6 p-4 rounded-xl border border-slate-200 bg-slate-50/50">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-slate-900 text-white">
                <GitBranch className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">GitHub MCP Server</h4>
                <p className="text-[11px] text-slate-500">
                  Search repositories, read code, list pull requests, and manage issues.
                </p>
              </div>
            </div>
            {integrations.github_connected ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-200/80 text-slate-600 text-xs font-medium">
                <XCircle className="w-3.5 h-3.5" /> Offline
              </span>
            )}
          </div>

          {integrations.github_connected ? (
            <div className="mt-3 flex items-center justify-between pt-3 border-t border-slate-200/60">
              <span className="text-xs text-slate-600 font-medium">
                Agent is authenticated using your personal access token.
              </span>
              <button
                type="button"
                disabled={loadingGh}
                onClick={handleDisconnectGitHub}
                className="py-1.5 px-3 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold transition-all disabled:opacity-50"
              >
                {loadingGh ? 'Disconnecting...' : 'Disconnect'}
              </button>
            </div>
          ) : (
            <div className="mt-3 space-y-2 pt-3 border-t border-slate-200/60">
              <div className="flex gap-2">
                <div className="relative flex-1">
                  <Key className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
                  <input
                    type="password"
                    value={ghToken}
                    onChange={(e) => setGhToken(e.target.value)}
                    placeholder="ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
                    className="w-full pl-9 pr-3 py-2 bg-white border border-slate-200 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand-400/20 focus:border-brand-500"
                  />
                </div>
                <button
                  type="button"
                  disabled={loadingGh || !ghToken.trim()}
                  onClick={handleConnectGitHub}
                  className="py-2 px-4 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs transition-all disabled:opacity-50 shrink-0 flex items-center gap-1.5"
                >
                  {loadingGh && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Connect</span>
                </button>
              </div>
              <p className="text-[11px] text-slate-500 flex items-center gap-1">
                <Info className="w-3 h-3 text-slate-400" />
                Required PAT scopes: <code className="font-mono text-brand-700">repo</code>, <code className="font-mono text-brand-700">read:user</code>
              </p>
            </div>
          )}
        </div>

        {/* ── Integration 2: Gmail ────────────────────────────────────── */}
        <div className="mt-4 p-4 rounded-xl border border-slate-200 bg-slate-50/50">
          <div className="flex items-center justify-between mb-2">
            <div className="flex items-center gap-2">
              <div className="p-2 rounded-lg bg-red-600 text-white">
                <Mail className="w-4 h-4" />
              </div>
              <div>
                <h4 className="text-sm font-bold text-slate-900">Gmail MCP Server</h4>
                <p className="text-[11px] text-slate-500">
                  Search messages, read correspondence, and prepare draft replies.
                </p>
              </div>
            </div>
            {integrations.gmail_connected ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-100 text-emerald-800 text-xs font-semibold">
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-200/80 text-slate-600 text-xs font-medium">
                <XCircle className="w-3.5 h-3.5" /> Offline
              </span>
            )}
          </div>

          {integrations.gmail_connected ? (
            <div className="mt-3 flex items-center justify-between pt-3 border-t border-slate-200/60">
              <span className="text-xs text-slate-600 font-medium">
                Agent is authenticated using your personal OAuth token.
              </span>
              <button
                type="button"
                disabled={loadingGm}
                onClick={handleDisconnectGmail}
                className="py-1.5 px-3 rounded-lg border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold transition-all disabled:opacity-50"
              >
                {loadingGm ? 'Disconnecting...' : 'Disconnect'}
              </button>
            </div>
          ) : (
            <div className="mt-3 space-y-2 pt-3 border-t border-slate-200/60">
              <textarea
                rows={3}
                value={gmailJson}
                onChange={(e) => setGmailJson(e.target.value)}
                placeholder='{"token": "...", "refresh_token": "...", "client_id": "..."}'
                className="w-full p-2.5 bg-white border border-slate-200 rounded-lg text-xs font-mono focus:outline-none focus:ring-2 focus:ring-brand-400/20 focus:border-brand-500 resize-none"
              />
              <div className="flex items-center justify-between">
                <p className="text-[11px] text-slate-500">
                  Run <code className="font-mono text-brand-700">python auth_gmail.py</code> locally to generate <code className="font-mono">token.json</code>
                </p>
                <button
                  type="button"
                  disabled={loadingGm || !gmailJson.trim()}
                  onClick={handleConnectGmail}
                  className="py-2 px-4 rounded-lg bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs transition-all disabled:opacity-50 shrink-0 flex items-center gap-1.5"
                >
                  {loadingGm && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
                  <span>Save Gmail Token</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

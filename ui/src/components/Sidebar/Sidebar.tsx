import React from 'react';
import { 
  Bot, Plus, MessageSquare, LogOut, Settings2, Trash2, 
  ShieldCheck, GitBranch, Mail, CheckCircle2, XCircle, Sparkles
} from 'lucide-react';
import { Thread, IntegrationStatus } from '../../types';

interface SidebarProps {
  userEmail: string;
  threads: Thread[];
  activeThreadId: string | null;
  integrations: IntegrationStatus;
  onSelectThread: (threadId: string) => void;
  onNewThread: () => void;
  onDeleteThread: (threadId: string) => void;
  onOpenIntegrations: () => void;
  onLogout: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({
  userEmail,
  threads,
  activeThreadId,
  integrations,
  onSelectThread,
  onNewThread,
  onDeleteThread,
  onOpenIntegrations,
  onLogout,
}) => {
  return (
    <aside className="w-72 bg-white border-r border-brand-100/80 flex flex-col h-screen select-none shrink-0 shadow-sm">
      {/* ── Brand & App Header ────────────────────────────────────────── */}
      <div className="p-4 border-b border-slate-100 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center text-white shadow-sm shadow-brand-500/20">
            <Bot className="w-5 h-5" />
          </div>
          <div>
            <div className="font-sans font-bold text-slate-900 text-sm tracking-tight flex items-center gap-1">
              Major1 <span className="text-brand-600 font-extrabold">AI</span>
              <Sparkles className="w-3 h-3 text-brand-500 fill-brand-400" />
            </div>
            <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider">
              Agentic RAG Core
            </div>
          </div>
        </div>
      </div>

      {/* ── Action: New Conversation ───────────────────────────────────── */}
      <div className="p-3">
        <button
          onClick={onNewThread}
          className="w-full py-2.5 px-3.5 bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white font-semibold text-xs rounded-xl shadow-stitch-card hover:shadow-stitch-hover transition-all duration-200 flex items-center justify-center gap-2"
        >
          <Plus className="w-4 h-4 stroke-[2.5]" />
          <span>New Conversation</span>
        </button>
      </div>

      {/* ── Integrations Status Card ───────────────────────────────────── */}
      <div className="px-3 py-2">
        <div className="bg-brand-50/60 border border-brand-100/90 rounded-xl p-3">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-bold text-slate-700 tracking-wider uppercase flex items-center gap-1.5">
              <Settings2 className="w-3.5 h-3.5 text-brand-600" />
              Connected Tools
            </span>
            <button
              onClick={onOpenIntegrations}
              className="text-[10px] text-brand-700 hover:text-brand-900 font-semibold hover:underline"
            >
              Manage
            </button>
          </div>

          <div className="space-y-1.5 text-xs">
            <div className="flex items-center justify-between text-slate-600 py-0.5">
              <span className="flex items-center gap-1.5">
                <GitBranch className="w-3.5 h-3.5 text-slate-700" />
                GitHub MCP
              </span>
              {integrations.github_connected ? (
                <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-emerald-700 bg-emerald-100/70 px-1.5 py-0.5 rounded-full">
                  <CheckCircle2 className="w-2.5 h-2.5" /> Active
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded-full">
                  <XCircle className="w-2.5 h-2.5" /> Offline
                </span>
              )}
            </div>

            <div className="flex items-center justify-between text-slate-600 py-0.5">
              <span className="flex items-center gap-1.5">
                <Mail className="w-3.5 h-3.5 text-slate-700" />
                Gmail MCP
              </span>
              {integrations.gmail_connected ? (
                <span className="inline-flex items-center gap-1 text-[10px] font-mono font-semibold text-emerald-700 bg-emerald-100/70 px-1.5 py-0.5 rounded-full">
                  <CheckCircle2 className="w-2.5 h-2.5" /> Active
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[10px] font-mono font-medium text-slate-400 bg-slate-100 px-1.5 py-0.5 rounded-full">
                  <XCircle className="w-2.5 h-2.5" /> Offline
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── Thread History List ────────────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-3 py-2 space-y-1">
        <div className="text-[11px] font-bold text-slate-400 uppercase tracking-wider px-2 py-1">
          Recent Threads
        </div>

        {threads.length === 0 ? (
          <div className="text-center py-6 text-xs text-slate-400">
            No past conversations
          </div>
        ) : (
          threads.map((thread) => {
            const isActive = thread.thread_id === activeThreadId;
            return (
              <div
                key={thread.thread_id}
                onClick={() => onSelectThread(thread.thread_id)}
                className={`group flex items-center justify-between px-3 py-2 rounded-xl text-xs cursor-pointer transition-all duration-150 ${
                  isActive
                    ? 'bg-brand-50 text-brand-900 font-semibold border border-brand-200/80 shadow-xs'
                    : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900 border border-transparent'
                }`}
              >
                <div className="flex items-center gap-2 truncate pr-1">
                  <MessageSquare
                    className={`w-3.5 h-3.5 shrink-0 ${
                      isActive ? 'text-brand-600' : 'text-slate-400 group-hover:text-slate-600'
                    }`}
                  />
                  <span className="truncate">{thread.thread_title || 'Untitled Thread'}</span>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onDeleteThread(thread.thread_id);
                  }}
                  className="opacity-0 group-hover:opacity-100 p-1 text-slate-400 hover:text-red-500 rounded hover:bg-red-50 transition-all"
                  title="Delete conversation"
                >
                  <Trash2 className="w-3 h-3" />
                </button>
              </div>
            );
          })
        )}
      </div>

      {/* ── System Guardrails Info ─────────────────────────────────────── */}
      <div className="p-3 border-t border-slate-100 bg-slate-50/50">
        <div className="flex items-center gap-2 text-slate-500 text-[11px] font-medium">
          <ShieldCheck className="w-4 h-4 text-brand-600 shrink-0" />
          <span>HITL & PII Guardrails Active</span>
        </div>
      </div>

      {/* ── User Profile & Logout Footer ───────────────────────────────── */}
      <div className="p-3 border-t border-slate-100 bg-white flex items-center justify-between">
        <div className="flex items-center gap-2 truncate pr-2">
          <div className="w-7 h-7 rounded-full bg-brand-100 text-brand-700 font-bold text-xs flex items-center justify-center shrink-0 uppercase">
            {userEmail ? userEmail.charAt(0) : 'U'}
          </div>
          <span className="text-xs text-slate-700 font-medium truncate" title={userEmail}>
            {userEmail}
          </span>
        </div>
        <button
          onClick={onLogout}
          className="p-1.5 text-slate-400 hover:text-slate-700 hover:bg-slate-100 rounded-lg transition-colors"
          title="Sign Out"
        >
          <LogOut className="w-4 h-4" />
        </button>
      </div>
    </aside>
  );
};

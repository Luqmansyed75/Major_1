import React, { useEffect, useRef } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Bot, User as UserIcon, Cpu, Loader2, Sparkles, Terminal } from 'lucide-react';
import { Message, HITLEvent } from '../../types';
import { HITLApprovalCard } from './HITLApprovalCard';

interface ChatCanvasProps {
  threadTitle: string;
  messages: Message[];
  pendingHITL: HITLEvent | null;
  loading: boolean;
  onApproveHITL: () => void;
  onRejectHITL: () => void;
  hitlLoading: boolean;
}

export const ChatCanvas: React.FC<ChatCanvasProps> = ({
  threadTitle,
  messages,
  pendingHITL,
  loading,
  onApproveHITL,
  onRejectHITL,
  hitlLoading,
}) => {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, pendingHITL, loading]);

  return (
    <main className="flex-1 flex flex-col h-screen overflow-hidden bg-slate-50/60">
      {/* ── Chat Header ─────────────────────────────────────────────── */}
      <header className="h-16 px-6 border-b border-brand-100/80 bg-white/80 backdrop-blur-md flex items-center justify-between z-10 shrink-0">
        <div>
          <h2 className="text-sm font-bold font-sans text-slate-900 truncate max-w-md">
            {threadTitle || 'Live Agent Session'}
          </h2>
          <p className="text-[11px] text-slate-400 font-mono">
            LangGraph MemorySaver • Persistent Multi-Turn RAG
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-brand-50 border border-brand-200/60 text-brand-700 text-xs font-mono font-medium shadow-2xs">
            <span className="w-2 h-2 rounded-full bg-brand-500 animate-pulse" />
            <Cpu className="w-3.5 h-3.5" />
            <span>Groq LLaMA-3</span>
          </div>
        </div>
      </header>

      {/* ── Scrollable Message Feed ──────────────────────────────────── */}
      <div className="flex-1 overflow-y-auto px-6 py-6 space-y-6">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center max-w-md mx-auto py-12">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-brand-500 to-brand-300 flex items-center justify-center text-white shadow-lg shadow-brand-500/20 mb-4">
              <Sparkles className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold font-sans text-slate-900 mb-1">
              How can I assist your operations today?
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed mb-6">
              I can orchestrate repository issues on GitHub, read and draft Gmail correspondence,
              and retrieve grounded context with Human-In-The-Loop safety gates.
            </p>
          </div>
        ) : (
          messages.map((msg, index) => {
            const isUser = msg.role === 'user';

            return (
              <div
                key={index}
                className={`flex gap-3 max-w-4xl mx-auto ${
                  isUser ? 'justify-end' : 'justify-start'
                } animate-fadeIn`}
              >
                {!isUser && (
                  <div className="w-8 h-8 rounded-xl bg-brand-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`relative px-4 py-3.5 rounded-2xl text-sm leading-relaxed ${
                    isUser
                      ? 'bg-brand-50/90 text-brand-950 border border-brand-200/80 shadow-2xs max-w-xl'
                      : 'bg-white text-slate-800 border border-brand-100 shadow-stitch-card flex-1'
                  }`}
                >
                  {/* Tool execution badges if any */}
                  {msg.tools_called && msg.tools_called.length > 0 && (
                    <div className="mb-2.5 pb-2 border-b border-slate-100 flex flex-wrap gap-1.5">
                      {msg.tools_called.map((tool, tIdx) => (
                        <span
                          key={tIdx}
                          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-mono text-[10px] font-semibold border border-slate-200"
                        >
                          <Terminal className="w-2.5 h-2.5 text-brand-600" />
                          <span>Ran tool: {tool}</span>
                        </span>
                      ))}
                    </div>
                  )}

                  {isUser ? (
                    <div className="whitespace-pre-wrap">{msg.content}</div>
                  ) : (
                    <div className="prose-assistant text-slate-800 text-[13.5px]">
                      <ReactMarkdown remarkPlugins={[remarkGfm]}>
                        {msg.content}
                      </ReactMarkdown>
                    </div>
                  )}
                </div>

                {isUser && (
                  <div className="w-8 h-8 rounded-xl bg-slate-200 text-slate-700 flex items-center justify-center shrink-0 shadow-sm mt-0.5 font-bold text-xs">
                    <UserIcon className="w-4 h-4" />
                  </div>
                )}
              </div>
            );
          })
        )}

        {/* HITL Card Intercept */}
        {pendingHITL && (
          <HITLApprovalCard
            hitl={pendingHITL}
            onApprove={onApproveHITL}
            onReject={onRejectHITL}
            loading={hitlLoading}
          />
        )}

        {/* Agent Thinking indicator */}
        {loading && (
          <div className="flex items-center gap-3 max-w-4xl mx-auto text-slate-500 text-xs font-mono animate-pulse">
            <div className="w-8 h-8 rounded-xl bg-brand-50 border border-brand-200 text-brand-600 flex items-center justify-center shrink-0">
              <Loader2 className="w-4 h-4 animate-spin" />
            </div>
            <div className="flex items-center gap-2 bg-white px-3 py-2 rounded-xl border border-brand-100 shadow-2xs">
              <Sparkles className="w-3.5 h-3.5 text-brand-500 animate-spin" />
              <span>Orchestrating agent graph & MCP tools...</span>
            </div>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </main>
  );
};

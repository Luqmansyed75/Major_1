import React, { useState, useRef, useEffect } from 'react';
import { ArrowUp, Sparkles, CornerDownLeft } from 'lucide-react';

interface PromptBarProps {
  onSend: (message: string) => void;
  disabled: boolean;
}

const SUGGESTIONS = [
  '🔍 Search latest issues on GitHub',
  '✉️ Summarize my unread emails',
  '🚀 Draft a reply email regarding the project',
];

export const PromptBar: React.FC<PromptBarProps> = ({ onSend, disabled }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 160)}px`;
    }
  }, [input]);

  const handleSend = () => {
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput('');
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="sticky bottom-4 left-0 right-0 max-w-4xl mx-auto px-4 z-20">
      {/* Quick Suggestion Chips */}
      <div className="flex items-center gap-2 mb-2 overflow-x-auto pb-1 no-scrollbar">
        <span className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider flex items-center gap-1 shrink-0">
          <Sparkles className="w-3 h-3 text-brand-500" />
          Suggested:
        </span>
        {SUGGESTIONS.map((s, idx) => (
          <button
            key={idx}
            type="button"
            disabled={disabled}
            onClick={() => onSend(s.replace(/^[^\s]+\s/, ''))}
            className="text-xs bg-white/90 hover:bg-brand-50 hover:text-brand-700 hover:border-brand-200 border border-slate-200 text-slate-600 rounded-full px-3 py-1 font-medium transition-all shadow-2xs shrink-0 disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>

      {/* Floating Prompt Bar */}
      <div className="relative bg-white/95 backdrop-blur-xl border border-brand-200/90 rounded-2xl shadow-stitch-frosted p-2 transition-all focus-within:border-brand-500 focus-within:ring-2 focus-within:ring-brand-400/20">
        <div className="flex items-end gap-2">
          <textarea
            ref={textareaRef}
            rows={1}
            value={input}
            disabled={disabled}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              disabled
                ? 'Action pending approval...'
                : 'Ask anything, query GitHub repos, or draft an email...'
            }
            className="flex-1 max-h-36 bg-transparent resize-none px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none leading-relaxed disabled:opacity-60"
          />

          <button
            type="button"
            disabled={!input.trim() || disabled}
            onClick={handleSend}
            className="p-2.5 rounded-xl bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white shadow-sm transition-all duration-150 disabled:opacity-40 disabled:hover:bg-brand-600 shrink-0"
            title="Send prompt (Enter)"
          >
            <ArrowUp className="w-4 h-4 stroke-[2.5]" />
          </button>
        </div>

        <div className="flex items-center justify-between px-3 pt-1 text-[10px] text-slate-400 font-mono">
          <span>Groq LLaMA-3 • LangGraph State Machine</span>
          <span className="flex items-center gap-1">
            <CornerDownLeft className="w-2.5 h-2.5" /> Return to send
          </span>
        </div>
      </div>
    </div>
  );
};

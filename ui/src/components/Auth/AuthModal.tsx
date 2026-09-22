import React, { useState } from 'react';
import { Bot, KeyRound, UserPlus, AlertCircle, Loader2, Sparkles } from 'lucide-react';
import { api } from '../../services/api';

interface AuthModalProps {
  onSuccess: (token: string, email: string) => void;
}

export const AuthModal: React.FC<AuthModalProps> = ({ onSuccess }) => {
  const [tab, setTab] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email.trim() || !password.trim()) {
      setError('Please fill in all required fields.');
      return;
    }

    if (tab === 'register') {
      if (password !== confirmPassword) {
        setError('Passwords do not match.');
        return;
      }
      if (password.length < 8) {
        setError('Password must be at least 8 characters long.');
        return;
      }
    }

    setLoading(true);
    try {
      if (tab === 'login') {
        const res = await api.login(email.trim(), password);
        if (res.error) {
          setError(res.error);
        } else if (res.access_token) {
          onSuccess(res.access_token, email.trim());
        }
      } else {
        const res = await api.register(email.trim(), password);
        if (res.error) {
          setError(res.error);
        } else if (res.access_token) {
          onSuccess(res.access_token, email.trim());
        }
      }
    } catch (err: any) {
      setError(err.message || 'An unexpected error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/40 backdrop-blur-md animate-fadeIn">
      {/* Ambient background glow */}
      <div className="absolute w-96 h-96 bg-brand-300/30 rounded-full blur-3xl pointer-events-none -top-10 -left-10" />
      <div className="absolute w-96 h-96 bg-brand-500/20 rounded-full blur-3xl pointer-events-none -bottom-10 -right-10" />

      <div className="relative w-full max-w-md bg-white border border-brand-100 rounded-2xl shadow-stitch-frosted p-8 text-slate-800">
        {/* Brand Header */}
        <div className="flex flex-col items-center text-center mb-6">
          <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-brand-600 to-brand-400 flex items-center justify-center shadow-lg shadow-brand-500/25 mb-3 text-white">
            <Bot className="w-8 h-8" />
          </div>
          <h1 className="text-2xl font-extrabold font-sans tracking-tight text-slate-900 flex items-center gap-1.5">
            Major1 <span className="text-brand-600">AI Assistant</span>
            <Sparkles className="w-4 h-4 text-brand-400 fill-brand-400" />
          </h1>
          <p className="text-xs font-medium text-slate-500 mt-1 uppercase tracking-wider">
            Enterprise Agentic RAG • LangGraph & MCP
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="grid grid-cols-2 p-1 bg-slate-100/80 rounded-xl mb-6 border border-slate-200/60">
          <button
            type="button"
            onClick={() => { setTab('login'); setError(null); }}
            className={`flex items-center justify-center gap-2 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
              tab === 'login'
                ? 'bg-white text-brand-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <KeyRound className="w-4 h-4" />
            Sign In
          </button>
          <button
            type="button"
            onClick={() => { setTab('register'); setError(null); }}
            className={`flex items-center justify-center gap-2 py-2 text-sm font-semibold rounded-lg transition-all duration-200 ${
              tab === 'register'
                ? 'bg-white text-brand-700 shadow-sm'
                : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            <UserPlus className="w-4 h-4" />
            Register
          </button>
        </div>

        {/* Error Notification */}
        {error && (
          <div className="mb-4 p-3 rounded-lg bg-red-50 border border-red-200 text-red-700 text-xs flex items-start gap-2 animate-fadeIn">
            <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
            <div className="flex-1">{error}</div>
          </div>
        )}

        {/* Auth Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Work Email
            </label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="operator@enterprise.com"
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
              Password
            </label>
            <input
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder={tab === 'register' ? 'Min. 8 characters' : '••••••••'}
              className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
            />
          </div>

          {tab === 'register' && (
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-1.5">
                Confirm Password
              </label>
              <input
                type="password"
                required
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Repeat password"
                className="w-full px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
              />
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="w-full mt-2 py-3 px-4 bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white font-semibold rounded-xl text-sm shadow-md shadow-brand-500/25 transition-all flex items-center justify-center gap-2 disabled:opacity-60"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Processing...</span>
              </>
            ) : tab === 'login' ? (
              'Sign In to Assistant →'
            ) : (
              'Create Account →'
            )}
          </button>
        </form>
      </div>
    </div>
  );
};

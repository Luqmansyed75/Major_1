import React, { useState } from 'react';
import { ShieldAlert, ChevronDown, ChevronUp, Check, X, Loader2, Code2 } from 'lucide-react';
import { HITLEvent } from '../../types';

interface HITLApprovalCardProps {
  hitl: HITLEvent;
  onApprove: () => void;
  onReject: () => void;
  loading: boolean;
}

export const HITLApprovalCard: React.FC<HITLApprovalCardProps> = ({
  hitl,
  onApprove,
  onReject,
  loading,
}) => {
  const [showDetails, setShowDetails] = useState(true);
  const toolName = hitl.hitl_event.tool_name || 'Unknown Action';
  const args = hitl.hitl_event.args || {};

  return (
    <div className="my-4 rounded-2xl bg-white/90 backdrop-blur-md border-2 border-amber-300 shadow-stitch-frosted p-5 max-w-3xl mx-auto animate-fadeIn">
      {/* Header */}
      <div className="flex items-start gap-3">
        <div className="p-2.5 rounded-xl bg-amber-100/80 text-amber-800 shrink-0">
          <ShieldAlert className="w-5 h-5 stroke-[2.5]" />
        </div>
        <div className="flex-1">
          <div className="flex items-center justify-between">
            <h4 className="text-sm font-bold font-sans text-slate-900 flex items-center gap-2">
              High-Risk Action Intercepted
              <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-200">
                HITL Gate
              </span>
            </h4>
          </div>
          <p className="text-xs text-slate-600 mt-1">
            The assistant is requesting explicit human approval before executing this external operation:
          </p>
          <div className="mt-2 inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 font-mono text-xs text-brand-700 font-medium border border-slate-200">
            <Code2 className="w-3.5 h-3.5 text-slate-500" />
            <span>{toolName}</span>
          </div>
        </div>
      </div>

      {/* Parameter inspection */}
      <div className="mt-4 border border-slate-200/80 rounded-xl overflow-hidden bg-slate-50/50">
        <button
          type="button"
          onClick={() => setShowDetails(!showDetails)}
          className="w-full px-3.5 py-2 flex items-center justify-between text-xs font-semibold text-slate-700 hover:bg-slate-100/60 transition-colors"
        >
          <span className="flex items-center gap-1.5 font-mono text-[11px]">
            Payload Arguments ({Object.keys(args).length} params)
          </span>
          {showDetails ? (
            <ChevronUp className="w-3.5 h-3.5 text-slate-500" />
          ) : (
            <ChevronDown className="w-3.5 h-3.5 text-slate-500" />
          )}
        </button>

        {showDetails && (
          <div className="p-3 bg-slate-900 text-slate-200 font-mono text-xs overflow-x-auto border-t border-slate-200 max-h-56">
            <pre className="text-[11px] leading-relaxed">
              {JSON.stringify(args, null, 2)}
            </pre>
          </div>
        )}
      </div>

      {/* Decision Buttons */}
      <div className="mt-4 flex items-center justify-end gap-3 pt-2">
        <button
          type="button"
          disabled={loading}
          onClick={onReject}
          className="py-2.5 px-4 rounded-xl border border-slate-200 bg-white hover:bg-slate-50 active:bg-slate-100 text-slate-700 font-semibold text-xs transition-all flex items-center gap-1.5 disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <X className="w-3.5 h-3.5 text-red-500 stroke-[2.5]" />
          )}
          <span>Reject Action</span>
        </button>

        <button
          type="button"
          disabled={loading}
          onClick={onApprove}
          className="py-2.5 px-4 rounded-xl bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white font-semibold text-xs shadow-stitch-card transition-all flex items-center gap-1.5 disabled:opacity-50"
        >
          {loading ? (
            <Loader2 className="w-3.5 h-3.5 animate-spin" />
          ) : (
            <Check className="w-3.5 h-3.5 stroke-[2.5]" />
          )}
          <span>Approve & Execute</span>
        </button>
      </div>
    </div>
  );
};

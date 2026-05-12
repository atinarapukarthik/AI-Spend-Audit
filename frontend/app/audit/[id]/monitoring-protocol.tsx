"use client";

import { useState } from "react";
import { useToasts, default as ToastContainer } from "../../components/toast-container";

interface MonitoringProtocolProps {
  auditId: string;
}

export default function MonitoringProtocol({ auditId }: MonitoringProtocolProps) {
  const { toasts, addToast, removeToast } = useToasts();
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    if (!email) {
      addToast("Field empty", "error");
      return;
    }
    if (loading) return;
    setLoading(true);
    addToast("Article generation started...", "info");
    try {
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/generate-blueprint`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ email, audit_id: auditId }),
        }
      );
      if (res.ok) {
        addToast("Check your inbox for the Strategic Blueprint", "success");
      } else {
        addToast("Generation failed", "error");
      }
    } catch {
      addToast("Network error", "error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="border border-zinc-800 rounded-xl sm:rounded-2xl bg-zinc-900/50 px-4 sm:px-8 py-5 sm:py-6">
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      <p className="text-[10px] sm:text-xs text-zinc-500 font-mono uppercase tracking-widest mb-2 sm:mb-3">
        Protocol: Continuous Monitoring
      </p>
      <p className="text-xs sm:text-sm text-zinc-400 font-mono mb-4 sm:mb-5">
        Activate monitoring to receive tactical alerts if market variables (pricing) shift
        or if higher-yield assets emerge.
      </p>
      <div className="flex flex-col sm:flex-row gap-2 sm:gap-3 max-w-lg">
        <input
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          placeholder="Email address"
          className="w-full flex-1 px-4 py-3 bg-zinc-900 border border-zinc-700 text-zinc-200 font-mono text-sm placeholder:text-zinc-600 focus:outline-none focus:border-zinc-500 transition-colors"
        />
        <button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full sm:w-auto px-6 py-3 bg-zinc-800 hover:bg-zinc-700 disabled:bg-zinc-900 disabled:text-zinc-600 text-zinc-300 border border-zinc-700 disabled:border-zinc-800 font-mono text-xs sm:text-sm uppercase tracking-wider transition-colors whitespace-nowrap cursor-pointer disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {loading && (
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          )}
          {loading ? "Generating..." : "Initialize Monitoring"}
        </button>
      </div>
    </div>
  );
}

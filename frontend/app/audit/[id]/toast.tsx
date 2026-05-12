"use client";

import { useEffect } from "react";

interface ToastProps {
  message: string;
  type?: "success" | "error";
  onClose: () => void;
}

export default function Toast({ message, type = "success", onClose }: ToastProps) {
  useEffect(() => {
    const timer = setTimeout(onClose, 4000);
    return () => clearTimeout(timer);
  }, [onClose]);

  return (
    <div className="fixed bottom-4 sm:bottom-6 left-1/2 -translate-x-1/2 z-50 w-[calc(100%-2rem)] sm:w-auto animate-slide-up">
      <div
        className={`border px-4 sm:px-6 py-3 font-mono text-xs sm:text-sm shadow-xl flex items-center gap-3 ${
          type === "success"
            ? "bg-zinc-900 border-zinc-700 text-zinc-200"
            : "bg-red-950 border-red-800 text-red-200"
        }`}
      >
        <span className="flex-1">{message}</span>
        <button
          onClick={onClose}
          className="text-zinc-500 hover:text-zinc-300 ml-2 text-lg leading-none cursor-pointer"
        >
          ×
        </button>
      </div>
    </div>
  );
}

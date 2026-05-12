"use client";

import { useEffect } from "react";

interface ToastData {
  id: number;
  message: string;
  type: "info" | "success" | "error";
}

interface ToastItemProps {
  toast: ToastData;
  onClose: (id: number) => void;
}

function ToastItem({ toast, onClose }: ToastItemProps) {
  useEffect(() => {
    const timer = setTimeout(() => onClose(toast.id), 4000);
    return () => clearTimeout(timer);
  }, [toast.id, onClose]);

  const border = {
    info: "border-zinc-700",
    success: "border-emerald-700",
    error: "border-red-700",
  }[toast.type];

  const bg = {
    info: "bg-zinc-900",
    success: "bg-zinc-900",
    error: "bg-red-950",
  }[toast.type];

  const text = {
    info: "text-zinc-200",
    success: "text-emerald-200",
    error: "text-red-200",
  }[toast.type];

  return (
    <div className={`border ${border} ${bg} ${text} px-4 py-3 font-mono text-xs sm:text-sm shadow-xl flex items-center gap-3 animate-toast-in`}>
      <span className="flex-1">{toast.message}</span>
      <button onClick={() => onClose(toast.id)} className="text-zinc-500 hover:text-zinc-300 ml-2 text-lg leading-none cursor-pointer">×</button>
    </div>
  );
}

export type { ToastData };

export default ToastItem;

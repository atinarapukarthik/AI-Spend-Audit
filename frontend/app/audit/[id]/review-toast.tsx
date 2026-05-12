"use client";

import { useEffect, useState } from "react";
import { useToasts, default as ToastContainer } from "../../components/toast-container";

export default function ReviewToast() {
  const { toasts, addToast, removeToast } = useToasts();
  const [shown, setShown] = useState(false);

  useEffect(() => {
    if (!shown) {
      addToast("Audit review completed", "success");
      setShown(true);
    }
  }, [shown, addToast]);

  return <ToastContainer toasts={toasts} removeToast={removeToast} />;
}

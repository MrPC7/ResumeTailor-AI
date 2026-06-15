"use client";

import { useEffect, useState } from "react";
import { AlertCircle, CheckCircle2, Info } from "lucide-react";
import { APP_TOAST_EVENT, type ToastPayload } from "@/lib/toast";
import { cn } from "@/lib/utils";

type ToastItem = ToastPayload & { id: number };

function toastIcon(type: ToastPayload["type"]) {
  if (type === "success") return <CheckCircle2 className="h-4 w-4" />;
  if (type === "info") return <Info className="h-4 w-4" />;
  return <AlertCircle className="h-4 w-4" />;
}

export function ToastCenter() {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  useEffect(() => {
    const onToast = (event: Event) => {
      const custom = event as CustomEvent<ToastPayload>;
      const payload = custom.detail;
      if (!payload?.message) return;

      const id = Date.now() + Math.floor(Math.random() * 1000);
      setToasts((prev) => [...prev, { ...payload, id }]);
      window.setTimeout(() => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
      }, 4200);
    };

    window.addEventListener(APP_TOAST_EVENT, onToast);
    return () => window.removeEventListener(APP_TOAST_EVENT, onToast);
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="pointer-events-none fixed right-4 top-4 z-50 flex w-[min(92vw,380px)] flex-col gap-2">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          role="status"
          className={cn(
            "pointer-events-auto rounded-lg border px-3 py-2 text-sm shadow-md backdrop-blur",
            toast.type === "error" && "border-red-200 bg-red-50 text-red-700",
            toast.type === "success" && "border-emerald-200 bg-emerald-50 text-emerald-700",
            toast.type === "info" && "border-blue-200 bg-blue-50 text-blue-700",
          )}
        >
          <div className="flex items-start gap-2">
            <span className="mt-0.5 shrink-0">{toastIcon(toast.type)}</span>
            <p>{toast.message}</p>
          </div>
        </div>
      ))}
    </div>
  );
}

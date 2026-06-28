/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React from "react";
import { AlertCircle, CheckCircle, Loader2, XCircle, X } from "lucide-react";

export interface ToastMessage {
  id: string;
  type: "success" | "error" | "info" | "loading";
  message: string;
}

interface ToastProps {
  toasts: ToastMessage[];
  onClose: (id: string) => void;
}

export default function ToastContainer({ toasts, onClose }: ToastProps) {
  if (toasts.length === 0) return null;

  return (
    <div id="toast-container" className="fixed bottom-4 right-4 z-50 flex flex-col gap-2 max-w-sm w-full pointer-events-none">
      {toasts.map((toast) => (
        <div
          key={toast.id}
          id={`toast-${toast.id}`}
          className="pointer-events-auto flex items-start gap-3 p-4 rounded-lg bg-white border border-gray-200 shadow-lg text-sm transition-all duration-300 animate-slide-in"
        >
          <div className="flex-shrink-0 mt-0.5">
            {toast.type === "success" && (
              <CheckCircle className="h-5 w-5 text-emerald-500" />
            )}
            {toast.type === "error" && (
              <XCircle className="h-5 w-5 text-rose-500" />
            )}
            {toast.type === "loading" && (
              <Loader2 className="h-5 w-5 text-blue-500 animate-spin" />
            )}
            {toast.type === "info" && (
              <AlertCircle className="h-5 w-5 text-amber-500" />
            )}
          </div>
          <div className="flex-1 text-gray-700 font-medium">{toast.message}</div>
          <button
            onClick={() => onClose(toast.id)}
            className="flex-shrink-0 text-gray-400 hover:text-gray-600 focus:outline-none"
            aria-label="关闭通知"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      ))}
    </div>
  );
}

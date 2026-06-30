"use client";

import { useState, useEffect, useCallback, createContext, useContext, ReactNode } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, Info, AlertCircle, CheckCircle2 } from "lucide-react";

type ToastType = "info" | "success" | "error";

interface Toast {
  id: string;
  message: string;
  type: ToastType;
}

interface ToastContextType {
  showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType>({ showToast: () => {} });

export function useToast() {
  return useContext(ToastContext);
}

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const showToast = useCallback((message: string, type: ToastType = "info") => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const icons = { info: Info, success: CheckCircle2, error: AlertCircle };
  const colors = {
    info: "border-[#64FFDA]/30 bg-[#112240]",
    success: "border-green-500/30 bg-[#112240]",
    error: "border-red-500/30 bg-[#112240]",
  };

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {/* Toast container — fixed bottom-center */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-[200] flex flex-col gap-2 pointer-events-none">
        <AnimatePresence>
          {toasts.map((t) => {
            const Icon = icons[t.type];
            return (
              <motion.div
                key={t.id}
                initial={{ opacity: 0, y: 20, scale: 0.95 }}
                animate={{ opacity: 1, y: 0, scale: 1 }}
                exit={{ opacity: 0, y: -10, scale: 0.95 }}
                className={`pointer-events-auto flex items-center gap-3 px-5 py-3 rounded-xl border shadow-lg ${colors[t.type]}`}
              >
                <Icon className={`w-4 h-4 flex-shrink-0 ${t.type === "info" ? "text-[#64FFDA]" : t.type === "success" ? "text-green-400" : "text-red-400"}`} />
                <span className="text-sm text-[#E6F1FF]">{t.message}</span>
                <button onClick={() => removeToast(t.id)} className="ml-2 text-[#495670] hover:text-[#E6F1FF] cursor-pointer">
                  <X className="w-3.5 h-3.5" />
                </button>
              </motion.div>
            );
          })}
        </AnimatePresence>
      </div>
    </ToastContext.Provider>
  );
}

"use client";

import { X, CheckCircle2, AlertCircle } from "lucide-react";
import { TaskProgress } from "@/lib/hooks/useTaskPolling";

interface Props {
  progress: TaskProgress;
  onCancel?: () => void;
}

const STAGE_MESSAGES: Record<number, string> = {
  0.0: "Initializing...",
  0.1: "Analyzing content structure...",
  0.3: "Designing slide layouts...",
  0.6: "Translating & formatting...",
  0.7: "Generating visual assets...",
  0.85: "Finalizing presentation...",
  0.95: "Almost done...",
};

export function TaskProgressBar({ progress, onCancel }: Props) {
  const percent = Math.round(progress.progress * 100);
  const isComplete = progress.status === "completed";
  const isFailed = progress.status === "failed";

  return (
    <div className="px-4 py-3 border-t border-[#64FFDA]/10 bg-[#0A192F]/60">
      {/* Status header */}
      <div className="flex items-center justify-between mb-2">
        <div className="flex items-center gap-2">
          {isComplete ? (
            <CheckCircle2 className="w-4 h-4 text-[#64FFDA]" />
          ) : isFailed ? (
            <AlertCircle className="w-4 h-4 text-red-400" />
          ) : (
            <div className="w-4 h-4 rounded-full border-2 border-[#64FFDA]/30 border-t-[#64FFDA] animate-spin" />
          )}
          <span className="text-xs font-medium text-[#8892B0]">
            {isComplete
              ? "Complete"
              : isFailed
              ? "Failed"
              : progress.message || "Processing..."}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs text-[#64FFDA] font-mono">{percent}%</span>
          {!isComplete && !isFailed && onCancel && (
            <button
              onClick={onCancel}
              className="text-[#495670] hover:text-red-400 transition-colors"
            >
              <X className="w-3.5 h-3.5" />
            </button>
          )}
        </div>
      </div>

      {/* Progress bar */}
      <div className="h-1.5 bg-[#112240] rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ease-out ${
            isFailed
              ? "bg-red-400"
              : isComplete
              ? "bg-[#64FFDA]"
              : "bg-gradient-to-r from-[#64FFDA] to-[#45E0BE]"
          }`}
          style={{ width: `${percent}%` }}
        />
      </div>

      {/* Stage indicators */}
      {!isComplete && !isFailed && (
        <div className="flex justify-between mt-2 px-0.5">
          {[
            { pct: 10, label: "Analyze" },
            { pct: 50, label: "Design" },
            { pct: 80, label: "Visuals" },
            { pct: 95, label: "Finalize" },
          ].map((stage) => (
            <div key={stage.pct} className="flex flex-col items-center">
              <div
                className={`w-1.5 h-1.5 rounded-full mb-0.5 ${
                  percent >= stage.pct ? "bg-[#64FFDA]" : "bg-[#1A2744]"
                }`}
              />
              <span
                className={`text-[8px] ${
                  percent >= stage.pct ? "text-[#64FFDA]" : "text-[#495670]"
                }`}
              >
                {stage.label}
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Error message */}
      {isFailed && progress.error && (
        <p className="text-xs text-red-400 mt-2">{progress.error}</p>
      )}
    </div>
  );
}

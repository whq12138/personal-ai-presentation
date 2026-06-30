"use client";

import { useEffect, useState, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Loader2, Sparkles, CheckCircle2, AlertCircle } from "lucide-react";
import { TaskProgress } from "@/lib/hooks/useTaskPolling";

interface Props {
  progress: TaskProgress;
  onCancel?: () => void;
}

const STAGES = [
  { pct: 0,   label: "解析" },
  { pct: 30,  label: "排版" },
  { pct: 65,  label: "配图" },
  { pct: 90,  label: "保存" },
] as const;

/**
 * 画布中央发光进度遮罩。
 * 渲染在 16:9 SlideCanvas 内部，用绝对定位覆盖整个画布区域。
 * 特效: 脉冲光晕 + 渐变进度条 + 阶段指示器 + 滚动消息。
 */
export function CanvasProgressOverlay({ progress, onCancel }: Props) {
  const percent = Math.round(progress.progress * 100);
  const isComplete = progress.status === "completed";
  const isFailed = progress.status === "failed";
  const messageRef = useRef<HTMLParagraphElement>(null);
  const [displayMsg, setDisplayMsg] = useState(progress.message || "");

  // 消息淡入切换
  useEffect(() => {
    if (progress.message && progress.message !== displayMsg) {
      setDisplayMsg(progress.message);
    }
  }, [progress.message]);

  // 完成时自动消失（由父组件控制 visible）
  if (isComplete) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.3 }}
        className="absolute inset-0 z-30 flex items-center justify-center"
      >
        {/* 半透明暗色遮罩 — 不用 backdrop-blur (在 transform:scale() 下渲染异常) */}
        <div className="absolute inset-0 bg-[#0A192F]/90" />

        {/* 中央进度卡片 */}
        <motion.div
          initial={{ scale: 0.9, y: 10 }}
          animate={{ scale: 1, y: 0 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="relative z-10 w-[460px] px-10 py-9 rounded-2xl
                     bg-[#112240] border border-[#64FFDA]/10
                     shadow-[0_0_80px_rgba(100,255,218,0.08),0_0_200px_rgba(100,255,218,0.03)]"
        >
          {/* ——— 发光线框 ——— */}
          <div
            className="absolute inset-0 rounded-2xl pointer-events-none"
            style={{
              background: `
                conic-gradient(
                  from 0deg,
                  rgba(100,255,218,0) 0%,
                  rgba(100,255,218,0.08) 25%,
                  rgba(100,255,218,0) 50%,
                  rgba(100,255,218,0.08) 75%,
                  rgba(100,255,218,0) 100%
                )
              `,
              animation: "gradient-rotate 4s linear infinite",
              mask: "linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0)",
              maskComposite: "exclude",
              padding: "1px",
            }}
          />

          {/* ——— 状态图标 + 标题 ——— */}
          <div className="flex items-center gap-3 mb-6">
            {isFailed ? (
              <AlertCircle className="w-6 h-6 text-red-400 flex-shrink-0" />
            ) : (
              <div className="relative flex-shrink-0">
                <Sparkles
                  className="w-6 h-6 text-[#64FFDA]"
                  style={{
                    filter: "drop-shadow(0 0 6px rgba(100,255,218,0.5))",
                    animation: "pulse-glow 2s ease-in-out infinite",
                  }}
                />
                {/* 外圈脉冲 */}
                <div
                  className="absolute inset-0 rounded-full"
                  style={{
                    animation: "pulse-glow 2s ease-in-out infinite",
                  }}
                />
              </div>
            )}
            <div>
              <h3 className="text-base font-bold text-[#E6F1FF]">
                {isFailed ? "生成失败" : "AI 正在生成幻灯片"}
              </h3>
              <p className="text-xs text-[#64FFDA]/60 mt-0.5 font-mono">
                {percent}% 完成
              </p>
            </div>
          </div>

          {/* ——— 渐变进度条 + 光带 ——— */}
          <div className="relative mb-5">
            {/* 背景轨道 */}
            <div className="h-2 bg-[#0A192F] rounded-full overflow-hidden border border-[#64FFDA]/5">
              {/* 填充条 + 流光 */}
              <motion.div
                className={`h-full rounded-full relative overflow-hidden ${
                  isFailed
                    ? "bg-red-400"
                    : "bg-gradient-to-r from-[#64FFDA] via-[#45E0BE] to-[#64FFDA]"
                }`}
                initial={{ width: "0%" }}
                animate={{ width: `${percent}%` }}
                transition={{ duration: 0.6, ease: "easeOut" }}
              >
                {/* 光带扫描效果 */}
                {!isFailed && (
                  <div
                    className="absolute inset-y-0 w-20"
                    style={{
                      background: `
                        linear-gradient(
                          90deg,
                          transparent 0%,
                          rgba(255,255,255,0.3) 50%,
                          transparent 100%
                        )
                      `,
                      animation: "scan 1.5s ease-in-out infinite",
                    }}
                  />
                )}
              </motion.div>
            </div>

            {/* 发光底部反射 */}
            <div
              className="absolute -bottom-1 left-0 h-[2px] rounded-full blur-sm opacity-30"
              style={{
                width: `${percent}%`,
                background: isFailed
                  ? "#f87171"
                  : "linear-gradient(90deg, #64FFDA, #45E0BE)",
                transition: "width 0.6s ease-out",
              }}
            />
          </div>

          {/* ——— 四阶段指示器 ——— */}
          <div className="flex justify-between mb-5">
            {STAGES.map((stage, i) => {
              const active = percent >= stage.pct;
              const current =
                percent >= stage.pct &&
                (i === STAGES.length - 1 || percent < STAGES[i + 1].pct);
              return (
                <div key={stage.pct} className="flex flex-col items-center gap-1">
                  <div className="relative">
                    <div
                      className={`w-2.5 h-2.5 rounded-full transition-all duration-500 ${
                        active
                          ? current
                            ? "bg-[#64FFDA] shadow-[0_0_8px_rgba(100,255,218,0.6)]"
                            : "bg-[#64FFDA]/40"
                          : "bg-[#1A2744]"
                      }`}
                    />
                    {current && (
                      <div
                        className="absolute inset-0 rounded-full animate-ping"
                        style={{
                          background: "rgba(100,255,218,0.2)",
                          animationDuration: "1.5s",
                        }}
                      />
                    )}
                  </div>
                  <span
                    className={`text-[10px] transition-colors duration-300 ${
                      active ? "text-[#64FFDA]" : "text-[#495670]"
                    }`}
                  >
                    {stage.label}
                  </span>
                </div>
              );
            })}
          </div>

          {/* ——— 滚动消息 ——— */}
          <div className="min-h-[40px] flex items-center">
            <motion.p
              key={displayMsg}
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3 }}
              className={`text-sm leading-relaxed ${
                isFailed ? "text-red-400" : "text-[#8892B0]"
              }`}
            >
              {isFailed
                ? progress.error || "未知错误，请重试"
                : displayMsg || "准备中..."}
            </motion.p>
          </div>

          {/* ——— 取消按钮 ——— */}
          {!isComplete && !isFailed && onCancel && (
            <button
              onClick={onCancel}
              className="mt-4 w-full py-2 text-xs text-[#495670] hover:text-red-400
                         border border-[#64FFDA]/5 hover:border-red-500/20
                         rounded-lg transition-colors cursor-pointer"
            >
              取消生成
            </button>
          )}
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}

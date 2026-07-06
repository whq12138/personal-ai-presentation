"use client";

/* ------------------------------------------------------------------ */
/*  所有 Hooks 一律放在组件最顶部，严禁出现在条件分支或早返之后          */
/* ------------------------------------------------------------------ */
import { useState, useCallback, useEffect, useMemo } from "react";
import { useRouter } from "next/navigation";
import { Navbar } from "@/components/layout/Navbar";
import { AppShell } from "@/components/layout/AppShell";
import { ChatPanel } from "@/components/panel/ChatPanel";
import { HistoryPanel } from "@/components/panel/HistoryPanel";
import { SlideCanvas } from "@/components/canvas/SlideCanvas";
import { SlideRenderer } from "@/components/canvas/SlideRenderer";
import { CanvasProgressOverlay } from "@/components/canvas/CanvasProgressOverlay";
import { useAuth } from "@/lib/auth/AuthContext";
import { useTaskPolling } from "@/lib/hooks/useTaskPolling";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { useToast } from "@/components/ui/Toast";
import type { ChatMessage, Presentation, GenerationStatus } from "@/lib/types";
import { generateId, sanitizePresentation } from "@/lib/utils";
import { DEMO_PRESENTATION } from "@/lib/demo-data";

export default function Home() {
  /* ---- 外部 Context hooks ---- */
  const router = useRouter();
  const { t } = useLanguage();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const { taskProgress, startPolling, cancelPolling, authFetch } = useTaskPolling();
  const { showToast } = useToast();

  /* ---- 组件内状态 ---- */
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [presentation, setPresentation] = useState<Presentation | null>(null);
  const [activeSlideIndex, setActiveSlideIndex] = useState(0);
  const [generationStatus, setGenerationStatus] = useState<GenerationStatus>("idle");
  const [isExporting, setIsExporting] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  /* ---- Side effects ---- */
  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.replace("/login");
  }, [authLoading, isAuthenticated, router]);

  /* ---- 回调 — 全部 useCallback 放这里 ---- */

  const handleLoadDemo = useCallback(() => {
    setPresentation(DEMO_PRESENTATION);
    setActiveSlideIndex(0);
    setMessages([{
      id: generateId(), role: "assistant",
      content: t("msg.demoLoaded"), timestamp: Date.now(),
      presentation: DEMO_PRESENTATION,
    }]);
    setGenerationStatus("done");
  }, [t]);

  const handleSubmit = useCallback(async (text: string) => {
    setMessages(prev => [...prev, { id: generateId(), role: "user", content: text, timestamp: Date.now() }]);
    setGenerationStatus("generating");
    try {
      const res = await authFetch("/generate", { method: "POST", body: JSON.stringify({ text }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || t("status.error"));
      startPolling(data.task_id, (result) => {
        if (result.success && result.presentation) {
          const pres = sanitizePresentation(result.presentation);
          setPresentation(pres);
          setActiveSlideIndex(0);
          setMessages(prev => [...prev, {
            id: generateId(), role: "assistant",
            content: t("msg.generated", pres.slides.length, pres.metadata.title),
            timestamp: Date.now(), presentation: pres,
          }]);
        }
        setGenerationStatus("done");
      }, (err) => {
        setGenerationStatus("error");
        setMessages(prev => [...prev, { id: generateId(), role: "assistant", content: err || t("msg.error"), timestamp: Date.now() }]);
      });
    } catch (err: any) {
      setGenerationStatus("error");
      setMessages(prev => [...prev, { id: generateId(), role: "assistant", content: err.message || t("msg.error"), timestamp: Date.now() }]);
    }
  }, [t, authFetch, startPolling]);

  const handleEdit = useCallback(async (instruction: string) => {
    if (!presentation) return;
    setMessages(prev => [...prev, { id: generateId(), role: "user", content: instruction, timestamp: Date.now() }]);
    setGenerationStatus("editing");
    try {
      const res = await authFetch("/generate/edit", { method: "POST", body: JSON.stringify({ presentation, instruction }) });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Edit failed");
      startPolling(data.task_id, (result) => {
        if (result.success && result.presentation) {
          const pres = sanitizePresentation(result.presentation);
          setPresentation(pres);
          setMessages(prev => [...prev, {
            id: generateId(), role: "assistant",
            content: t("msg.editApplied", result.changed_slide_ids?.length || pres.slides.length),
            timestamp: Date.now(), presentation: pres,
          }]);
        }
        setGenerationStatus("done");
      }, () => setGenerationStatus("error"));
    } catch { setGenerationStatus("error"); }
  }, [presentation, t, authFetch, startPolling]);

  /* ---- PPTX 导出 — 调用后端 python-pptx 引擎 ---- */
  const handleExport = useCallback(async () => {
    if (!presentation) return;
    setIsExporting(true);
    try {
      const filename = `${presentation.metadata.title || "presentation"}.pptx`;
      const res = await authFetch("/export", {
        method: "POST",
        headers: { "Content-Type": "application/json" } as Record<string, string>,
        body: JSON.stringify({ presentation, filename }),
      });
      if (!res.ok) throw new Error("Export failed");
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url; a.download = filename;
      document.body.appendChild(a); a.click(); document.body.removeChild(a);
      setTimeout(() => URL.revokeObjectURL(url), 1000);
      showToast("PPTX downloaded successfully!", "success");
    } catch (err: any) {
      showToast(err.message || t("msg.exportError"), "error");
    } finally {
      setIsExporting(false);
    }
  }, [presentation, t, authFetch, showToast]);

  /* ---- 从历史加载文稿 ---- */
  const handleLoadFromHistory = useCallback(async (savedId: string) => {
    setShowHistory(false);
    try {
      const res = await authFetch(`/presentation/load/${savedId}`);
      if (!res.ok) throw new Error("Load failed");
      const data = await res.json();
      if (data.success && data.presentation) {
        const pres = sanitizePresentation(data.presentation);
        setPresentation(pres);
        setActiveSlideIndex(0);
        showToast("Presentation loaded!", "success");
      }
    } catch {
      showToast("Failed to load presentation", "error");
    }
  }, [authFetch, showToast]);

  /* ---- 派生值 ---- */
  const activeSlide = useMemo(() => presentation?.slides[activeSlideIndex] || null, [presentation, activeSlideIndex]);
  const isGenerating = useMemo(() => generationStatus === "generating" || generationStatus === "editing", [generationStatus]);

  /* ─────────────────────────────────────────────── */
  /*  条件返回 (所有 Hook 之后)                       */
  /* ─────────────────────────────────────────────── */
  if (authLoading) {
    return (
      <div className="h-screen bg-[#0A192F] flex items-center justify-center">
        <div className="w-8 h-8 rounded-full border-2 border-[#64FFDA]/30 border-t-[#64FFDA] animate-spin" />
      </div>
    );
  }
  if (!isAuthenticated) return null;

  return (
    <div className="h-screen bg-[#0A192F] flex flex-col">
      <Navbar />
      <AppShell
        sidebar={
          showHistory ? (
            <HistoryPanel
              onLoad={handleLoadFromHistory}
              onClose={() => setShowHistory(false)}
            />
          ) : (
            <ChatPanel
              messages={messages}
              generationStatus={isGenerating ? "generating" : generationStatus}
              onSubmit={handleSubmit}
              onEdit={presentation ? handleEdit : undefined}
              onLoadDemo={presentation ? undefined : handleLoadDemo}
              onToggleHistory={() => setShowHistory(true)}
            />
          )
        }
        canvas={
          <SlideCanvas
            slideCount={presentation?.slides.length || 0}
            activeIndex={activeSlideIndex}
            onSlideChange={setActiveSlideIndex}
            onExport={presentation ? handleExport : undefined}
            isExporting={isExporting}
            presentationTitle={presentation?.metadata.title}
            onLoadDemo={presentation ? undefined : handleLoadDemo}
            overlay={
              isGenerating && taskProgress.taskId ? (
                <CanvasProgressOverlay progress={taskProgress} onCancel={cancelPolling} />
              ) : null
            }
          >
            {activeSlide && <SlideRenderer slide={activeSlide} />}
          </SlideCanvas>
        }
      />
    </div>
  );
}

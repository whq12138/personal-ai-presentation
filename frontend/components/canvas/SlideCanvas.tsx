"use client";

import { useRef, useState, useEffect, useCallback, ReactNode, forwardRef, useImperativeHandle } from "react";
import { ChevronLeft, ChevronRight, Presentation, Play, Download } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useLanguage } from "@/lib/i18n/LanguageContext";

const SLIDE_W = 1280;
const SLIDE_H = 720;
const RATIO = SLIDE_W / SLIDE_H;

export interface SlideCanvasHandle {
  /** 获取用于 html2canvas 截图的 DOM 元素 */
  getCaptureElement: () => HTMLDivElement | null;
}

interface SlideCanvasProps {
  children: ReactNode;
  slideCount: number;
  activeIndex: number;
  onSlideChange: (index: number) => void;
  onExport?: () => void;
  isExporting?: boolean;
  presentationTitle?: string;
  onLoadDemo?: () => void;
  overlay?: ReactNode;
}

/**
 * 16:9 完美等比例自适应画布。
 * - wrapper 预缩放置，确保不溢出
 * - inner 固定 1280×720, transform: scale(s), origin: top left
 * - overlay 在 inner 内部，随画布等比缩放
 * - 导出时通过 getCaptureElement() 获取 inner DOM 节点供 html2canvas 截图
 */
export const SlideCanvas = forwardRef<SlideCanvasHandle, SlideCanvasProps>(function SlideCanvas({
  children, slideCount, activeIndex, onSlideChange,
  onExport, isExporting = false, presentationTitle, onLoadDemo, overlay,
}, ref) {
  const { t } = useLanguage();
  const containerRef = useRef<HTMLDivElement>(null);
  const innerRef = useRef<HTMLDivElement>(null);

  const [wrapperSize, setWrapperSize] = useState({ w: SLIDE_W, h: SLIDE_H });
  const [scale, setScale] = useState(1);

  useImperativeHandle(ref, () => ({
    getCaptureElement: () => innerRef.current,
  }), []);

  const recalc = useCallback(() => {
    const el = containerRef.current;
    if (!el) return;
    const cw = el.clientWidth;
    const ch = el.clientHeight;
    let w: number, h: number;
    if (cw / ch > RATIO) { h = ch; w = ch * RATIO; }
    else { w = cw; h = cw / RATIO; }
    setWrapperSize({ w: Math.floor(w), h: Math.floor(h) });
    setScale(w / SLIDE_W);
  }, []);

  useEffect(() => {
    recalc();
    const ro = new ResizeObserver(recalc);
    if (containerRef.current) ro.observe(containerRef.current);
    return () => ro.disconnect();
  }, [recalc]);

  const hasSlides = slideCount > 0;

  return (
    <div ref={containerRef} className="w-full h-full relative overflow-hidden">
      {hasSlides && (
        <div className="absolute top-4 left-4 right-4 flex items-center justify-between z-20">
          <div className="flex items-center gap-3">
            <Badge variant="accent">
              {t("canvas.slide")} {activeIndex + 1} {t("canvas.of")} {slideCount}
            </Badge>
            {presentationTitle && (
              <span className="text-sm text-[#8892B0] truncate max-w-[300px]">{presentationTitle}</span>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Button variant="secondary" size="sm" onClick={() => onSlideChange(Math.max(0, activeIndex - 1))} disabled={activeIndex === 0}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <Button variant="secondary" size="sm" onClick={() => onSlideChange(Math.min(slideCount - 1, activeIndex + 1))} disabled={activeIndex === slideCount - 1}>
              <ChevronRight className="w-4 h-4" />
            </Button>
            {onExport && (
              <Button variant="primary" size="sm" onClick={onExport} isLoading={isExporting}
                leftIcon={!isExporting ? <Download className="w-4 h-4" /> : undefined}>
                {t("canvas.export")}
              </Button>
            )}
          </div>
        </div>
      )}

      <div className="w-full h-full flex items-center justify-center">
        <div className="relative rounded-lg shadow-2xl flex-shrink-0" style={{ width: wrapperSize.w, height: wrapperSize.h }}>
          {/* 缩放原点层 */}
          <div ref={innerRef} data-slide-capture
            className="absolute top-0 left-0 rounded-lg overflow-hidden"
            style={{ width: SLIDE_W, height: SLIDE_H, transform: `scale(${scale})`, transformOrigin: "top left" }}>
            <div className="absolute inset-0 bg-gradient-to-br from-[#0A192F] via-[#112240] to-[#0A192F]" />
            <div className="absolute inset-0 opacity-[0.03]"
              style={{ backgroundImage: "linear-gradient(rgba(100,255,218,0.3) 1px, transparent 1px), linear-gradient(90deg, rgba(100,255,218,0.3) 1px, transparent 1px)", backgroundSize: "40px 40px" }} />
            <div className="absolute inset-0 overflow-hidden pointer-events-none">
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-[#64FFDA]/10" style={{ animation: "scan 3s linear infinite" }} />
            </div>
            <div className="relative z-10 w-full h-full flex items-center justify-center">
              {children}
            </div>
            {/* === 进度遮罩 — 绝对定位在 inner 内部，随 scale 等比缩放 === */}
            {overlay}
          </div>
        </div>
      </div>

      {!hasSlides && (
        <div className="absolute inset-0 flex flex-col items-center justify-center text-center z-10 pointer-events-none">
          <div className="w-20 h-20 bg-[#112240] border border-[#64FFDA]/10 rounded-2xl flex items-center justify-center mb-6">
            <Presentation className="w-10 h-10 text-[#495670]" />
          </div>
          <h3 className="text-lg font-semibold text-[#8892B0] mb-2">{t("canvas.emptyTitle")}</h3>
          <p className="text-sm text-[#495670] max-w-md leading-relaxed mb-5">{t("canvas.emptyDesc")}</p>
          {onLoadDemo && (
            <span className="pointer-events-auto">
              <Button variant="secondary" size="sm" onClick={onLoadDemo} leftIcon={<Play className="w-4 h-4" />}>
                {t("canvas.loadDemo")}
              </Button>
            </span>
          )}
        </div>
      )}
    </div>
  );
});

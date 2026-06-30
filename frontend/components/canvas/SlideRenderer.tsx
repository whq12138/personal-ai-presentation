"use client";

import { AnimatePresence, motion } from "framer-motion";
import { Slide } from "@/lib/types";
import { TitleSlide } from "./layouts/TitleSlide";
import { TwoColumnSlide } from "./layouts/TwoColumnSlide";
import { HighlightNumberSlide } from "./layouts/HighlightNumberSlide";
import { TableSlide } from "./layouts/TableSlide";
import { BulletListSlide } from "./layouts/BulletListSlide";

interface SlideRendererProps {
  slide: Slide;
}

/**
 * Dispatches a slide to its appropriate layout component.
 * Uses Framer Motion AnimatePresence for smooth slide transitions.
 */
export function SlideRenderer({ slide }: SlideRendererProps) {
  const layoutMap: Record<string, React.ComponentType<{ slide: Slide }>> = {
    title: TitleSlide,
    "two-column": TwoColumnSlide,
    "highlight-number": HighlightNumberSlide,
    table: TableSlide,
    "bullet-list": BulletListSlide,
  };

  const Component = layoutMap[slide.layout] || TitleSlide;

  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={slide.id}
        initial={{ opacity: 0, x: 20 }}
        animate={{ opacity: 1, x: 0 }}
        exit={{ opacity: 0, x: -20 }}
        transition={{ duration: 0.25, ease: "easeInOut" }}
        className="w-full h-full"
      >
        <Component slide={slide} />
      </motion.div>
    </AnimatePresence>
  );
}

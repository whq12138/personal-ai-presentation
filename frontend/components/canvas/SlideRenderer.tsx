"use client";

import { useMemo, ComponentType } from "react";
import { AnimatePresence, motion } from "framer-motion";
import { Slide } from "@/lib/types";

import { TitleSlide } from "./layouts/TitleSlide";
import { TwoColumnSlide } from "./layouts/TwoColumnSlide";
import { HighlightNumberSlide } from "./layouts/HighlightNumberSlide";
import { TableSlide } from "./layouts/TableSlide";
import { BulletListSlide } from "./layouts/BulletListSlide";
import { DefaultFallback } from "./layouts/DefaultFallback";

// ============================================================
// Type-safe Layout Registry (Strategy Pattern)
//
// Adding a new layout:
//   1. Import the component above
//   2. Add one line to LAYOUT_REGISTRY below
//   3. Done — SlideRenderer picks it up automatically
//
// Unknown layouts → DefaultFallback + console.warn (no white screen)
// ============================================================

interface SlideComponentProps {
  slide: Slide;
}

const LAYOUT_REGISTRY: Readonly<Record<string, ComponentType<SlideComponentProps>>> = {
  title: TitleSlide,
  "two-column": TwoColumnSlide,
  "highlight-number": HighlightNumberSlide,
  table: TableSlide,
  "bullet-list": BulletListSlide,
  // ↑ existing 5 layouts
  //
  // ↓ future layouts — add one import + one line each:
  // chart: ChartSlide,
  // "bleed-image": BleedImageSlide,
  // timeline: TimelineSlide,
  // comparison: ComparisonSlide,
};

interface SlideRendererProps {
  slide: Slide;
}

/**
 * Dynamic layout dispatcher using TypeScript strategy pattern.
 * Lookup is O(1), no switch/if-else chains, fully extensible.
 */
export function SlideRenderer({ slide }: SlideRendererProps) {
  const Component = useMemo(() => {
    const found = LAYOUT_REGISTRY[slide.layout];

    if (!found) {
      if (typeof window !== "undefined") {
        console.warn(
          `[SlideRenderer] Unknown layout "${slide.layout}" — ` +
          `rendering DefaultFallback. Available layouts: ${Object.keys(LAYOUT_REGISTRY).join(", ")}`
        );
      }
      return DefaultFallback;
    }

    return found;
  }, [slide.layout]);

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

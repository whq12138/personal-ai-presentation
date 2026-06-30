import { Slide, Presentation } from "./types";
import { SLIDE_ASPECT_RATIO } from "./constants";

/**
 * Calculate the scale factor to fit a 16:9 slide within a container.
 */
export function calculateSlideScale(
  containerWidth: number,
  containerHeight: number
): number {
  const containerRatio = containerWidth / containerHeight;
  if (containerRatio > SLIDE_ASPECT_RATIO) {
    return containerHeight / 720;
  }
  return containerWidth / 1280;
}

/** Generate a unique ID */
export function generateId(): string {
  return `${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

/** Deep clone a presentation */
export function clonePresentation(p: Presentation): Presentation {
  return JSON.parse(JSON.stringify(p));
}

/**
 * Sanitize a slide object by filling in defaults for any missing fields.
 * Gracefully handles incomplete LLM output.
 */
export function sanitizeSlide(slide: Partial<Slide>, index: number): Slide {
  return {
    id: slide.id || `slide-${index}`,
    layout: slide.layout || "title",
    title: slide.title || "",
    subtitle: slide.subtitle || undefined,
    body: slide.body || undefined,
    columns: slide.columns || undefined,
    highlightNumber: slide.highlightNumber || undefined,
    table: slide.table || undefined,
    background: slide.background || undefined,
    notes: slide.notes || undefined,
    image_prompt: slide.image_prompt || undefined,
    image_url: slide.image_url || undefined,
  };
}

/**
 * Sanitize an entire presentation by filling defaults.
 */
export function sanitizePresentation(raw: Partial<Presentation>): Presentation {
  return {
    metadata: {
      title: raw.metadata?.title || "AI Generated Slides",
      author: raw.metadata?.author || "Personal AI Presentation",
      createdAt: raw.metadata?.createdAt || new Date().toISOString(),
      slideCount: raw.slides?.length || 0,
    },
    slides: (raw.slides || []).map((s, i) => sanitizeSlide(s, i)),
  };
}

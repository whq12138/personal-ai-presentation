// ============================================================
// Personal AI Presentation — Core TypeScript Type Definitions
// Phase 2: image_prompt, image_url, target_lang, incremental edit types
// ============================================================

export type SlideLayout =
  | "title"
  | "two-column"
  | "highlight-number"
  | "table"
  | "bullet-list";

export interface ContentBlock {
  type: "paragraph" | "heading" | "image" | "list";
  text?: string;
  level?: 1 | 2 | 3;
  imageUrl?: string;
  imageAlt?: string;
  items?: string[];
}

export interface Columns {
  left: ContentBlock[];
  right: ContentBlock[];
}

export interface HighlightNumber {
  value: string;
  label: string;
  suffix?: string;
}

export interface TableData {
  headers: string[];
  rows: string[][];
}

export interface SlideBackground {
  color?: string;
  imageUrl?: string;
}

export interface Slide {
  id: string;
  layout: SlideLayout;
  title?: string;
  subtitle?: string;
  body?: string | string[];
  columns?: Columns;
  highlightNumber?: HighlightNumber;
  table?: TableData;
  background?: SlideBackground;
  notes?: string;
  // Phase 2: Image pipeline
  image_prompt?: string;
  image_url?: string;
}

export interface PresentationMetadata {
  title: string;
  author?: string;
  createdAt: string;
  slideCount?: number;
}

export interface Presentation {
  metadata: PresentationMetadata;
  slides: Slide[];
}

// ============================================================
// Chat & UI Types
// ============================================================

export type MessageRole = "user" | "assistant" | "system";

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: number;
  presentation?: Presentation;
  changedSlideIds?: string[]; // for incremental edit responses
}

export type LanguageCode = "en" | "zh" | "auto";
export type GenerationStatus = "idle" | "generating" | "editing" | "done" | "error";

export interface AppState {
  messages: ChatMessage[];
  presentation: Presentation | null;
  activeSlideIndex: number;
  generationStatus: GenerationStatus;
  errorMessage: string | null;
}

// ============================================================
// API Types
// ============================================================

export interface GenerateRequest {
  text: string;
  style?: string;
  target_lang?: LanguageCode;
  enable_images?: boolean;
}

export interface GenerateResponse {
  success: boolean;
  presentation?: Presentation;
  error?: string;
  was_repaired?: boolean;
}

export interface EditRequest {
  presentation: Presentation;
  instruction: string;
  target_lang?: LanguageCode;
}

export interface EditResponse {
  success: boolean;
  presentation?: Presentation;
  error?: string;
  changed_slide_ids?: string[];
}

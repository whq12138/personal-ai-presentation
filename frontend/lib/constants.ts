// ============================================================
// Design System Constants — Dark OLED + AI Native UI
// ============================================================

/** Primary color palette */
export const COLORS = {
  // Backgrounds
  bgPrimary: "#0A192F",
  bgSecondary: "#050A1A",
  bgSurface: "#112240",
  bgSurfaceHover: "#1A2744",

  // Accent
  accent: "#64FFDA",
  accentHover: "#45E0BE",
  accentDim: "rgba(100, 255, 218, 0.1)",

  // Secondary accent
  secondary: "#FFD700",
  secondaryDim: "rgba(255, 215, 0, 0.15)",

  // Text
  textPrimary: "#E6F1FF",
  textSecondary: "#8892B0",
  textMuted: "#495670",

  // Borders
  border: "rgba(100, 255, 218, 0.1)",
  borderVisible: "rgba(100, 255, 218, 0.2)",

  // Status
  success: "#64FFDA",
  error: "#FF6B6B",
  warning: "#FFD700",
} as const;

/** Slide canvas dimensions (16:9 ratio) */
export const SLIDE_ASPECT_RATIO = 16 / 9;
export const SLIDE_WIDTH_PX = 1280;
export const SLIDE_HEIGHT_PX = 720;

/** Layout dimensions */
export const LAYOUT = {
  chatPanelWidth: 420,
  navHeight: 56,
} as const;

/** Default slide metadata */
export const DEFAULT_METADATA = {
  author: "Personal AI Presentation",
} as const;

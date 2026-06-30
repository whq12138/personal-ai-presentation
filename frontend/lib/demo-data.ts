// Demo presentation — showcases all 5 slide layouts without needing an API key.
import { Presentation } from "./types";

export const DEMO_PRESENTATION: Presentation = {
  metadata: {
    title: "Personal AI Presentation — Demo",
    author: "AI Engine",
    createdAt: new Date().toISOString(),
    slideCount: 5,
  },
  slides: [
    {
      id: "slide-1",
      layout: "title",
      title: "🚀 The Future of AI Presentations",
      subtitle: "Generate Beautiful Slides from Plain Text",
      body: "Personal AI Presentation · 2026",
      notes: "Welcome everyone to this demo.",
    },
    {
      id: "slide-2",
      layout: "two-column",
      title: "Why AI-Powered Presentations?",
      columns: {
        left: [
          { type: "heading", text: "The Problem", level: 2 },
          { type: "paragraph", text: "Traditional slide creation takes hours of manual layout work, font tweaking, and alignment wrestling. Content and design remain painfully disconnected." },
          { type: "list", items: ["Hours wasted on formatting", "Inconsistent design language", "Content-design disconnect"] },
        ],
        right: [
          { type: "heading", text: "Our Solution", level: 2 },
          { type: "paragraph", text: "AI instantly transforms your text into professionally designed slides. You focus on ideas — we handle the pixels." },
          { type: "list", items: ["Instant generation from text", "5 intelligent layout types", "One-click PPTX export"] },
        ],
      },
    },
    {
      id: "slide-3",
      layout: "highlight-number",
      title: "Measurable Impact",
      highlightNumber: { value: "10×", label: "Faster Slide Creation", suffix: "vs. manual" },
      body: [
        "Average slide deck: 3 hours → 3 minutes",
        "Zero design skills required",
        "Export-ready PowerPoint files",
        "AI-powered content structuring",
      ],
    },
    {
      id: "slide-4",
      layout: "table",
      title: "Feature Comparison",
      table: {
        headers: ["Feature", "Manual Design", "Personal AI"],
        rows: [
          ["Creation Speed", "3-5 hours", "2-3 minutes"],
          ["Design Consistency", "Manual effort", "Automatic"],
          ["Layout Variety", "Limited by skill", "5 smart layouts"],
          ["Export Format", "PPTX", "PPTX + Future"],
          ["Content Suggestions", "None", "AI-powered"],
        ],
      },
    },
    {
      id: "slide-5",
      layout: "bullet-list",
      title: "Getting Started in 3 Steps",
      body: [
        "Paste your Markdown, text, or describe your presentation topic in the chat panel",
        "AI analyzes your content and selects the optimal slide layouts for each section",
        "Browse your slides, make refinements via chat, and export to PowerPoint with one click",
      ],
    },
  ],
};

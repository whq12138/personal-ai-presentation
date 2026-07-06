// Demo presentation — showcases all 8 layouts.
import { Presentation } from "./types";

export const DEMO_PRESENTATION: Presentation = {
  metadata: {
    title: "Personal AI Presentation — Demo",
    author: "AI Engine",
    createdAt: new Date().toISOString(),
    slideCount: 8,
  },
  slides: [
    {
      id: "slide-1",
      layout: "title",
      title: "The Future of AI Presentations",
      subtitle: "Generate Beautiful Slides from Plain Text",
      body: "Personal AI Presentation · 2026",
    },
    {
      id: "slide-2",
      layout: "two-column",
      title: "Why AI-Powered Presentations?",
      columns: {
        left: [
          { type: "heading" as const, text: "The Problem", level: 2 },
          { type: "paragraph" as const, text: "Traditional slide creation takes hours of manual layout work, font tweaking, and alignment wrestling." },
          { type: "list" as const, items: ["Hours on formatting", "Design inconsistency", "Content-design gap"] },
        ],
        right: [
          { type: "heading" as const, text: "Our Solution", level: 2 },
          { type: "paragraph" as const, text: "AI transforms your text into professionally designed slides instantly." },
          { type: "list" as const, items: ["Instant generation", "9 layout types", "Bilingual output"] },
        ],
      },
    },
    {
      id: "slide-3",
      layout: "highlight-number",
      title: "Measurable Impact",
      highlightNumber: { value: "10x", label: "Faster Slide Creation", suffix: "vs. manual" },
      body: ["Average slide deck: 3 hours → 3 minutes", "Zero design skills required", "AI-powered content structuring"],
    },
    {
      id: "slide-4",
      layout: "chart",
      title: "Monthly Active Users (k)",
      subtitle: "Steady growth across 2026",
    },
    {
      id: "slide-5",
      layout: "timeline",
      title: "Product Roadmap",
      body: [
        { date: "2026 Q1", title: "MVP Launch", desc: "Basic AI generation + 5 layouts" } as any,
        { date: "2026 Q2", title: "Multi-Model", desc: "DeepSeek + GLM + i18n support" } as any,
        { date: "2026 Q3", title: "SaaS Platform", desc: "JWT auth, payments, rate limiting" } as any,
        { date: "2026 Q4", title: "Enterprise", desc: "Team sharing + custom templates" } as any,
      ],
    },
    {
      id: "slide-6",
      layout: "table",
      title: "Feature Comparison",
      table: {
        headers: ["Feature", "Manual", "Personal AI"],
        rows: [
          ["Creation Speed", "3-5 hours", "2-3 min"],
          ["Consistency", "Manual", "Auto"],
          ["Layouts", "Limited", "9 types"],
          ["Languages", "Single", "Bilingual"],
          ["Export", "PPTX", "PDF + PPTX"],
        ],
      },
    },
    {
      id: "slide-7",
      layout: "bleed-image",
      title: "Your Ideas, Amplified",
      subtitle: "AI-powered design that scales with you",
      background: { color: "#0A192F" },
    },
    {
      id: "slide-8",
      layout: "bullet-list",
      title: "Getting Started in 3 Steps",
      body: [
        "Paste your Markdown or describe your topic in the chat panel",
        "AI analyzes content and selects optimal layouts for each section",
        "Browse, refine via chat, and export your presentation",
      ],
    },
  ],
};

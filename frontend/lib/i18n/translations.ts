// ============================================================
// Personal AI Presentation — Bilingual Translation Dictionary
// ============================================================

export type Language = "en" | "zh";
export type TranslationKey = keyof typeof en;

const en = {
  // Brand & Nav
  "brand.name": "Personal AI",
  "brand.tagline": "Presentation",
  "brand.badge": "MVP",
  "brand.poweredBy": "AI-Powered",

  // Chat Panel
  "chat.title": "AI Chat",
  "chat.shortcut": "⌘+↵ to send",
  "chat.emptyTitle": "Start Creating",
  "chat.emptyDesc":
    "Paste your Markdown, text, or describe what you want to present. AI will generate beautiful slides instantly.",
  "chat.loadDemo": "Load Demo Slides",
  "chat.typing": "AI is thinking...",

  // Input
  "input.placeholder": "Paste your markdown or describe your presentation...",
  "input.generate": "Generate",
  "input.editPlaceholder": "Edit instruction, e.g. \"make slide 2 two-column\"...",
  "input.edit": "Apply Edit",

  // Canvas
  "canvas.slide": "Slide",
  "canvas.of": "/",
  "canvas.export": "Export PDF",
  "canvas.emptyTitle": "Ready to Create",
  "canvas.emptyDesc":
    "Enter your content in the chat panel on the left. AI will generate beautifully formatted slides here.",
  "canvas.loadDemo": "Load Demo Slides",

  // Status messages
  "status.generating": "AI is thinking...",
  "status.layouting": "Designing slide layouts...",
  "status.images": "Generating high-quality visuals...",
  "status.done": "Done!",
  "status.error": "Generation failed",

  // Messages
  "msg.demoLoaded":
    "Loaded a 5-slide demo! Browse all layout types: Title, Two-Column, Highlight Number, Table, and Bullet List. Use the arrow buttons or click Export PDF to download.",
  "msg.generated": (count: number, title: string) =>
    `Created a ${count}-slide presentation: "${title}". Browse with arrows, export to PDF when ready.`,
  "msg.editApplied": (changedCount: number) =>
    `Updated ${changedCount} slide${changedCount !== 1 ? "s" : ""}.`,
  "msg.slidesGenerated": (count: number) => `${count} slides generated`,
  "msg.error": "Something went wrong. You can still try the Demo to see the UI.",
  "msg.exportError": "Failed to export. Is the backend running?",
  "msg.connectError": "Failed to connect to AI service. Is the backend running?",

  // Layout labels
  "layout.title": "Title Slide",
  "layout.two-column": "Two Columns",
  "layout.highlight-number": "Key Number",
  "layout.table": "Data Table",
  "layout.bullet-list": "Bullet Points",

  // Metadata
  "meta.title": "Personal AI Presentation",
  "meta.description":
    "AI-powered presentation generation. Convert text to beautiful slides instantly, export to PowerPoint.",
  "meta.keywords": "AI, presentation, slides, PDF, markdown, generator",

  // Language
  "lang.switch": "中文",
  "lang.label": "EN",
};

const zh: typeof en = {
  // 品牌与导航
  "brand.name": "Personal AI",
  "brand.tagline": "演示文稿",
  "brand.badge": "内测",
  "brand.poweredBy": "AI 驱动",

  // 对话面板
  "chat.title": "AI 对话",
  "chat.shortcut": "⌘+↵ 发送",
  "chat.emptyTitle": "开始创建",
  "chat.emptyDesc": "粘贴您的 Markdown、文本，或描述您想要展示的内容。AI 将瞬间生成精美的幻灯片。",
  "chat.loadDemo": "加载演示文稿",
  "chat.typing": "AI 思考中...",

  // 输入区域
  "input.placeholder": "粘贴 Markdown 或描述您的演示主题...",
  "input.generate": "生成",
  "input.editPlaceholder": "编辑指令，如：\"把第二页改成两栏布局\"...",
  "input.edit": "应用编辑",

  // 画布
  "canvas.slide": "第",
  "canvas.of": "/",
  "canvas.export": "导出 PDF",
  "canvas.emptyTitle": "准备就绪",
  "canvas.emptyDesc": "在左侧面板输入您的内容，AI 将在此处生成精美的幻灯片。",
  "canvas.loadDemo": "加载演示文稿",

  // 状态提示
  "status.generating": "AI 思考中...",
  "status.layouting": "正在设计幻灯片版式...",
  "status.images": "正在生成高质量视觉配图...",
  "status.done": "完成！",
  "status.error": "生成失败",

  // 消息
  "msg.demoLoaded":
    "已加载包含 5 张幻灯片的演示！浏览所有布局类型：标题页、两栏、数字强调、表格和要点列表。使用箭头翻页，点击导出 PDF 下载。",
  "msg.generated": (count: number, title: string) =>
    `已创建包含 ${count} 张幻灯片的演示文稿："${title}"。使用箭头浏览，准备好后导出为 PDF。`,
  "msg.editApplied": (changedCount: number) =>
    `已更新 ${changedCount} 张幻灯片。`,
  "msg.slidesGenerated": (count: number) => `已生成 ${count} 张幻灯片`,
  "msg.error": "抱歉，出了一些问题。您可以先看看 Demo 效果。",
  "msg.exportError": "导出失败，后端服务是否在运行？",
  "msg.connectError": "无法连接 AI 服务，后端是否在运行？",

  // 布局标签
  "layout.title": "标题页",
  "layout.two-column": "双栏布局",
  "layout.highlight-number": "数字强调",
  "layout.table": "数据表格",
  "layout.bullet-list": "要点列表",

  // 元数据
  "meta.title": "Personal AI Presentation",
  "meta.description": "AI 驱动的演示文稿生成器。瞬间将文本转化为精美幻灯片，一键导出 PDF。",
  "meta.keywords": "AI, 演示文稿, 幻灯片, PDF, Markdown, 生成器",

  // 语言
  "lang.switch": "English",
  "lang.label": "中",
};

export const translations: Record<Language, typeof en> = { en, zh };

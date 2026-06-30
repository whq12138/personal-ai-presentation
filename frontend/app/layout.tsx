import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "./providers";

export const metadata: Metadata = {
  title: "Personal AI Presentation",
  description:
    "AI-powered presentation generation. Convert text to beautiful slides instantly, export to PowerPoint. | AI 驱动的演示文稿生成器",
  keywords: ["AI", "presentation", "slides", "PPTX", "markdown", "generator"],
};

export const viewport: Viewport = {
  width: "device-width",
  initialScale: 1,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="h-full bg-[#0A192F] text-[#E6F1FF] overflow-hidden">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}

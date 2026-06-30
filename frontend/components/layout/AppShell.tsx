"use client";

import { ReactNode } from "react";

interface AppShellProps {
  sidebar: ReactNode;
  canvas: ReactNode;
}

/**
 * Main app layout — CSS Grid 2-column split.
 * Left: 420px chat/control panel. Right: flexible 16:9 canvas.
 * Responsive: stacks vertically on small screens.
 */
export function AppShell({ sidebar, canvas }: AppShellProps) {
  return (
    <div className="flex h-[calc(100vh-3.5rem)] mt-14">
      {/* Left Panel — Chat & Controls */}
      <aside className="w-[420px] flex-shrink-0 border-r border-[#64FFDA]/10 bg-[#0A192F] overflow-hidden flex flex-col max-sm:hidden">
        {sidebar}
      </aside>

      {/* Mobile: sidebar shown as overlay via parent state */}

      {/* Right Panel — Slide Canvas */}
      <main className="flex-1 bg-[#050A1A] overflow-hidden flex items-center justify-center">
        {canvas}
      </main>
    </div>
  );
}

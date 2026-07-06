"use client";

import { AlertTriangle } from "lucide-react";
import { Slide } from "@/lib/types";

interface Props {
  slide: Slide;
}

/**
 * Graceful fallback for unknown or unimplemented layout types.
 *
 * Renders a clean warning card instead of a white screen.
 * Production systems log the layout name so future plugins can be prioritised.
 */
export function DefaultFallback({ slide }: Props) {
  return (
    <div className="w-full h-full flex items-center justify-center">
      <div className="max-w-lg px-12 py-8 text-center">
        {/* Warning icon */}
        <div className="w-14 h-14 mx-auto mb-4 rounded-xl bg-[#FFD700]/10 border border-[#FFD700]/20 flex items-center justify-center">
          <AlertTriangle className="w-6 h-6 text-[#FFD700]" />
        </div>

        {/* Slide title (still shown if available) */}
        {slide.title && (
          <h2 className="text-2xl font-bold text-[#E6F1FF] mb-3">
            {slide.title}
          </h2>
        )}

        {/* Layout hint */}
        <div className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#64FFDA]/5 border border-[#64FFDA]/10 rounded-full text-xs text-[#64FFDA] font-mono mb-3">
          <span className="text-[#495670]">layout:</span> {slide.layout}
        </div>

        {/* Message */}
        <p className="text-sm text-[#8892B0] leading-relaxed">
          This layout type is not yet implemented.{" "}
          {slide.body && typeof slide.body === "string" && (
            <span>Content will be rendered in the default format once available.</span>
          )}
        </p>
        {slide.body && typeof slide.body !== "string" && Array.isArray(slide.body) && (
          <ul className="mt-4 space-y-2 text-left">
            {slide.body.map((item, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-[#8892B0]">
                <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#64FFDA]/40 flex-shrink-0" />
                {item}
              </li>
            ))}
          </ul>
        )}

        {/* Console warning for developers */}
        <p className="mt-6 text-[10px] text-[#495670]">
          Check the browser console for the missing layout details.
        </p>
      </div>
    </div>
  );
}

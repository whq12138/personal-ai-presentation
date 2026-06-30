"use client";

import { Slide } from "@/lib/types";

interface Props {
  slide: Slide;
}

export function TitleSlide({ slide }: Props) {
  return (
    <div className="w-full h-full flex flex-col items-center justify-center text-center px-24">
      {/* Decorative accent line */}
      <div className="w-20 h-1 bg-gradient-to-r from-transparent via-[#64FFDA] to-transparent mb-8 rounded-full" />

      {/* Title */}
      <h1 className="text-5xl font-bold text-[#E6F1FF] leading-tight mb-4 tracking-tight">
        {slide.title || "Untitled"}
      </h1>

      {/* Subtitle */}
      {slide.subtitle && (
        <p className="text-xl text-[#64FFDA] mb-6 font-medium">
          {slide.subtitle}
        </p>
      )}

      {/* Decorative bottom line */}
      <div className="w-32 h-0.5 bg-gradient-to-r from-transparent via-[#64FFDA]/40 to-transparent rounded-full" />

      {/* Body / Date */}
      {slide.body && (
        <p className="mt-8 text-sm text-[#8892B0]">
          {typeof slide.body === "string" ? slide.body : slide.body[0]}
        </p>
      )}
    </div>
  );
}

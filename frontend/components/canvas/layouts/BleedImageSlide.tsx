"use client";

import { Slide } from "@/lib/types";

interface Props {
  slide: Slide;
}

/**
 * Bleed Image layout — full-bleed background image with text overlay.
 * Uses `background.imageUrl` or `image_url` as the background.
 * Text is rendered in a translucent dark card overlaid on the image.
 */
export function BleedImageSlide({ slide }: Props) {
  const bgUrl = slide.background?.imageUrl || slide.image_url || "";
  const bgColor = slide.background?.color || "#0A192F";

  return (
    <div className="w-full h-full relative overflow-hidden">
      {/* Background image with gradient overlay */}
      <div
        className="absolute inset-0 bg-cover bg-center"
        style={{
          backgroundImage: bgUrl
            ? `url(${bgUrl})`
            : `linear-gradient(135deg, ${bgColor}, #0A192F)`,
          backgroundSize: "cover",
        }}
      />
      {/* Dark gradient overlay for text readability */}
      <div className="absolute inset-0 bg-gradient-to-t from-[#0A192F]/90 via-[#0A192F]/40 to-[#0A192F]/60" />

      {/* Text content — translucent card */}
      <div className="relative z-10 w-full h-full flex items-center justify-center px-24">
        <div className="bg-[#0A192F]/80 backdrop-blur-lg border border-[#64FFDA]/10 rounded-2xl px-12 py-10 max-w-2xl text-center">
          {slide.title && (
            <h1 className="text-4xl font-bold text-[#E6F1FF] mb-4 leading-tight">
              {slide.title}
            </h1>
          )}

          {slide.subtitle && (
            <p className="text-lg text-[#64FFDA] mb-6">{slide.subtitle}</p>
          )}

          {slide.body && (
            <p className="text-sm text-[#8892B0] leading-relaxed">
              {Array.isArray(slide.body) ? slide.body.join(" · ") : slide.body}
            </p>
          )}
        </div>
      </div>

      {/* Bottom corner attribution — if background is an image URL */}
      {bgUrl && (
        <div className="absolute bottom-4 right-6 z-10 text-[10px] text-[#495670]">
          Image source: {new URL(bgUrl).hostname}
        </div>
      )}
    </div>
  );
}

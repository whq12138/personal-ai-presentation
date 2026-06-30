"use client";

import { Slide } from "@/lib/types";

interface Props {
  slide: Slide;
}

export function BulletListSlide({ slide }: Props) {
  const items = slide.body
    ? Array.isArray(slide.body)
      ? slide.body
      : [slide.body]
    : [];

  return (
    <div className="w-full h-full flex flex-col px-16 py-12">
      {/* Title */}
      {slide.title && (
        <h2 className="text-3xl font-bold text-[#E6F1FF] mb-12">
          {slide.title}
        </h2>
      )}

      {/* Bullet list */}
      <div className="flex-1 flex flex-col justify-center space-y-4">
        {items.map((item, i) => (
          <div key={i} className="flex items-start gap-4 group">
            {/* Number/index indicator */}
            <div className="w-8 h-8 rounded-lg bg-[#64FFDA]/10 border border-[#64FFDA]/20 flex items-center justify-center flex-shrink-0 mt-0.5 group-hover:bg-[#64FFDA]/20 transition-colors">
              <span className="text-sm font-bold text-[#64FFDA]">{i + 1}</span>
            </div>

            {/* Content */}
            <p className="text-lg text-[#E6F1FF] leading-relaxed pt-1">
              {item}
            </p>
          </div>
        ))}
      </div>

      {/* Decorative bottom bar */}
      <div className="mt-8 h-1 w-full bg-gradient-to-r from-[#64FFDA]/20 via-[#64FFDA]/5 to-transparent rounded-full" />
    </div>
  );
}

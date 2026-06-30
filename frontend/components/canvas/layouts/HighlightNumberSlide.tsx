"use client";

import { Slide } from "@/lib/types";

interface Props {
  slide: Slide;
}

export function HighlightNumberSlide({ slide }: Props) {
  const hn = slide.highlightNumber;

  return (
    <div className="w-full h-full flex px-16 py-12">
      {/* Left: Big Number + Label */}
      <div className="flex-1 flex flex-col items-center justify-center">
        {hn && (
          <>
            {/* Glowing big number */}
            <div
              className="text-[120px] font-black text-[#64FFDA] leading-none tracking-tighter"
              style={{ textShadow: "0 0 40px rgba(100,255,218,0.3)" }}
            >
              {hn.value}
            </div>

            {/* Label */}
            <p className="text-lg text-[#E6F1FF] font-medium mt-4 text-center max-w-[300px]">
              {hn.label}
            </p>

            {/* Suffix / change indicator */}
            {hn.suffix && (
              <span className="inline-flex items-center mt-2 px-3 py-1 bg-[#64FFDA]/10 border border-[#64FFDA]/20 rounded-full text-sm text-[#64FFDA]">
                {hn.suffix}
              </span>
            )}
          </>
        )}
      </div>

      {/* Divider */}
      <div className="w-px mx-12 bg-gradient-to-b from-transparent via-[#64FFDA]/20 to-transparent" />

      {/* Right: Title + Supporting points */}
      <div className="flex-1 flex flex-col justify-center space-y-6">
        {slide.title && (
          <h2 className="text-3xl font-bold text-[#E6F1FF]">
            {slide.title}
          </h2>
        )}

        {slide.body && (
          <ul className="space-y-3">
            {(Array.isArray(slide.body) ? slide.body : [slide.body]).map(
              (item, i) => (
                <li
                  key={i}
                  className="flex items-start gap-3 text-sm text-[#8892B0]"
                >
                  <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#64FFDA]/60 flex-shrink-0" />
                  {item}
                </li>
              )
            )}
          </ul>
        )}
      </div>
    </div>
  );
}

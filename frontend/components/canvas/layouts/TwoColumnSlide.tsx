"use client";

import { Slide, ContentBlock } from "@/lib/types";

interface Props {
  slide: Slide;
}

function ContentBlockRenderer({ block }: { block: ContentBlock }) {
  switch (block.type) {
    case "heading":
      return (
        <h3 className="text-xl font-bold text-[#64FFDA] mb-3">
          {block.text}
        </h3>
      );
    case "list":
      return (
        <ul className="space-y-2">
          {block.items?.map((item, i) => (
            <li key={i} className="flex items-start gap-2 text-sm text-[#E6F1FF]">
              <span className="mt-1.5 w-1.5 h-1.5 rounded-full bg-[#64FFDA]/60 flex-shrink-0" />
              {item}
            </li>
          ))}
        </ul>
      );
    default:
      return (
        <p className="text-sm text-[#8892B0] leading-relaxed">
          {block.text}
        </p>
      );
  }
}

export function TwoColumnSlide({ slide }: Props) {
  return (
    <div className="w-full h-full flex flex-col px-16 py-12">
      {/* Title */}
      {slide.title && (
        <h2 className="text-3xl font-bold text-[#E6F1FF] mb-10">
          {slide.title}
        </h2>
      )}

      {/* Two columns */}
      <div className="flex-1 grid grid-cols-2 gap-12">
        {/* Left Column */}
        <div className="space-y-4">
          {slide.columns?.left.map((block, i) => (
            <ContentBlockRenderer key={`left-${i}`} block={block} />
          ))}
        </div>

        {/* Divider */}
        <div className="absolute left-1/2 top-[120px] bottom-16 w-px bg-gradient-to-b from-transparent via-[#64FFDA]/20 to-transparent" />

        {/* Right Column */}
        <div className="space-y-4">
          {slide.columns?.right.map((block, i) => (
            <ContentBlockRenderer key={`right-${i}`} block={block} />
          ))}
        </div>
      </div>
    </div>
  );
}

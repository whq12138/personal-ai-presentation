"use client";

import { Slide } from "@/lib/types";

interface Props {
  slide: Slide;
}

/**
 * Timeline layout — chronological event sequence.
 * Body field is expected to be a list of { date: string, title: string, desc: string } objects.
 * Renders a vertical timeline with glowing nodes and alternating content.
 */
export function TimelineSlide({ slide }: Props) {
  const events: Array<{ date: string; title?: string; text?: string; desc?: string }> =
    Array.isArray(slide.body)
      ? slide.body.map((item: any) =>
          typeof item === "string" ? { date: item, text: item } : item
        )
      : [];

  return (
    <div className="w-full h-full flex flex-col px-16 py-12">
      {slide.title && (
        <h2 className="text-3xl font-bold text-[#E6F1FF] mb-10">{slide.title}</h2>
      )}

      <div className="flex-1 relative">
        {/* Vertical line */}
        <div className="absolute left-6 top-0 bottom-0 w-px bg-gradient-to-b from-[#64FFDA]/40 via-[#64FFDA]/20 to-transparent" />

        <div className="space-y-8 pl-16">
          {events.map((event, i) => (
            <div key={i} className="relative group">
              {/* Timeline node */}
              <div className="absolute -left-[37px] top-1.5 w-3 h-3 rounded-full bg-[#64FFDA] shadow-[0_0_8px_rgba(100,255,218,0.4)] group-hover:shadow-[0_0_16px_rgba(100,255,218,0.6)] transition-shadow" />

              {/* Date */}
              <span className="text-xs text-[#64FFDA] font-mono mb-1 block">
                {event.date || ""}
              </span>

              {/* Title */}
              {(event.title || event.text) && (
                <h3 className="text-lg font-semibold text-[#E6F1FF] mb-1">
                  {event.title || event.text}
                </h3>
              )}

              {/* Description */}
              {event.desc && (
                <p className="text-sm text-[#8892B0] leading-relaxed">{event.desc}</p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

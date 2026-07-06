"use client";

import { Slide } from "@/lib/types";

interface Props {
  slide: Slide;
}

/**
 * Chart layout — data visualization slide.
 * Accepts a `chart` field in slide JSON: { type: "bar"|"line"|"pie", data: {...} }
 * Renders a styled placeholder chart grid until a real chart library is wired up.
 */
export function ChartSlide({ slide }: Props) {
  const chartData = (slide as any).chart || {};
  const chartType = chartData.type || "bar";
  const bars = chartData.data?.values || [65, 40, 80, 55, 90, 35];

  const maxVal = Math.max(...bars, 1);
  const colors = [
    "from-[#64FFDA] to-[#45E0BE]",
    "from-[#FFD700] to-[#FFA500]",
    "from-[#FF6B9D] to-[#FF4081]",
    "from-[#45E0BE] to-[#64FFDA]",
    "from-[#FFA500] to-[#FFD700]",
    "from-[#FF4081] to-[#FF6B9D]",
  ];

  return (
    <div className="w-full h-full flex flex-col px-16 py-12">
      {slide.title && (
        <h2 className="text-3xl font-bold text-[#E6F1FF] mb-8">{slide.title}</h2>
      )}

      <div className="flex-1 flex items-end gap-3 px-4 pb-2">
        {bars.map((val: number, i: number) => {
          const pct = (val / maxVal) * 100;
          return (
            <div key={i} className="flex-1 flex flex-col items-center gap-2 h-full justify-end">
              <span className="text-xs text-[#8892B0] font-mono">{val}</span>
              <div
                className={`w-full bg-gradient-to-t ${colors[i % colors.length]} rounded-t-lg transition-all duration-700`}
                style={{ height: `${Math.max(pct, 4)}%` }}
              />
              {chartData.data?.labels && (
                <span className="text-[10px] text-[#495670] mt-1">
                  {chartData.data.labels[i] || `#${i + 1}`}
                </span>
              )}
            </div>
          );
        })}
      </div>

      {slide.subtitle && (
        <p className="text-sm text-[#8892B0] text-center mt-4">{slide.subtitle}</p>
      )}

      {/* Bottom axis */}
      <div className="h-px bg-[#64FFDA]/10 mx-4 mt-4" />
    </div>
  );
}

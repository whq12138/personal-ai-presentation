"use client";

import { Slide } from "@/lib/types";

interface Props {
  slide: Slide;
}

export function TableSlide({ slide }: Props) {
  const table = slide.table;

  if (!table) return null;

  return (
    <div className="w-full h-full flex flex-col px-16 py-12">
      {/* Title */}
      {slide.title && (
        <h2 className="text-3xl font-bold text-[#E6F1FF] mb-10">
          {slide.title}
        </h2>
      )}

      {/* Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse">
          <thead>
            <tr>
              {table.headers.map((header, i) => (
                <th
                  key={i}
                  className="text-left text-sm font-semibold text-[#64FFDA] px-4 py-3 border-b border-[#64FFDA]/20 bg-[#64FFDA]/5 first:rounded-tl-lg last:rounded-tr-lg"
                >
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {table.rows.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className="hover:bg-white/[0.02] transition-colors"
              >
                {row.map((cell, colIdx) => (
                  <td
                    key={colIdx}
                    className="text-sm text-[#E6F1FF] px-4 py-3 border-b border-[#64FFDA]/5"
                  >
                    {cell}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

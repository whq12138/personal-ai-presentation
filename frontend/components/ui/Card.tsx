"use client";

import { HTMLAttributes, forwardRef } from "react";

interface CardProps extends HTMLAttributes<HTMLDivElement> {
  glow?: boolean;
  hoverable?: boolean;
}

export const Card = forwardRef<HTMLDivElement, CardProps>(
  ({ glow = false, hoverable = false, className = "", children, ...props }, ref) => {
    return (
      <div
        ref={ref}
        className={`
          bg-[#112240] border border-[#64FFDA]/10 rounded-2xl
          ${glow ? "shadow-[0_0_20px_rgba(100,255,218,0.05)]" : ""}
          ${hoverable ? "cursor-pointer hover:border-[#64FFDA]/30 hover:shadow-[0_0_20px_rgba(100,255,218,0.1)] transition-all duration-200" : ""}
          ${className}
        `.trim()}
        {...props}
      >
        {children}
      </div>
    );
  }
);

Card.displayName = "Card";

"use client";

import { HTMLAttributes } from "react";

type BadgeVariant = "accent" | "secondary" | "success" | "warning" | "default";

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
}

const variantStyles: Record<BadgeVariant, string> = {
  accent: "bg-[#64FFDA]/10 text-[#64FFDA] border-[#64FFDA]/20",
  secondary: "bg-white/5 text-[#8892B0] border-white/10",
  success: "bg-green-500/10 text-green-400 border-green-500/20",
  warning: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
  default: "bg-white/5 text-[#E6F1FF] border-white/10",
};

export function Badge({
  variant = "default",
  className = "",
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={`
        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium
        border ${variantStyles[variant]} ${className}
      `.trim()}
      {...props}
    >
      {children}
    </span>
  );
}

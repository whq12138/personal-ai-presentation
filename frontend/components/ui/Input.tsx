"use client";

import { InputHTMLAttributes, forwardRef } from "react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, leftIcon, className = "", ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm font-medium text-[#8892B0] mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-[#495670]">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            className={`
              w-full bg-[#0A192F] border border-[#64FFDA]/10 rounded-xl
              text-[#E6F1FF] placeholder-[#495670]
              ${leftIcon ? "pl-10" : "px-4"} py-3
              focus:outline-none focus:ring-2 focus:ring-[#64FFDA]/30 focus:border-[#64FFDA]/40
              transition-all duration-200
              ${error ? "border-red-500/50 focus:ring-red-500/30" : ""}
              ${className}
            `.trim()}
            {...props}
          />
        </div>
        {error && (
          <p className="mt-1 text-sm text-red-400">{error}</p>
        )}
      </div>
    );
  }
);

Input.displayName = "Input";

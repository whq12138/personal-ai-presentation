"use client";

import { useLanguage } from "@/lib/i18n/LanguageContext";

/**
 * Three bouncing dots animation — inspired by ai-native-ui.html pattern.
 * Indicates AI is processing/streaming a response.
 */
export function TypingIndicator() {
  const { t } = useLanguage();
  return (
    <div className="flex items-center gap-2 px-1">
      <div className="flex items-center gap-1.5">
        <span className="inline-block w-2 h-2 bg-[#64FFDA] rounded-full animate-bounce [animation-delay:0ms]" />
        <span className="inline-block w-2 h-2 bg-[#64FFDA] rounded-full animate-bounce [animation-delay:150ms]" />
        <span className="inline-block w-2 h-2 bg-[#64FFDA] rounded-full animate-bounce [animation-delay:300ms]" />
      </div>
      <span className="text-xs text-[#495670] ml-2">{t("chat.typing")}</span>
    </div>
  );
}

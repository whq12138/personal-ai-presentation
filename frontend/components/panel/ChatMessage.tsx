"use client";

import { Brain, User } from "lucide-react";
import { ChatMessage as ChatMessageType } from "@/lib/types";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface ChatMessageProps {
  message: ChatMessageType;
}

export function ChatMessageBubble({ message }: ChatMessageProps) {
  const { t } = useLanguage();
  const isUser = message.role === "user";
  const hasPresentation = !!message.presentation;

  return (
    <div className={`flex gap-3 px-4 py-3 ${isUser ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`
          w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0
          ${isUser
            ? "bg-[#FFD700]/20 text-[#FFD700]"
            : "bg-[#64FFDA]/10 text-[#64FFDA]"
          }
        `}
      >
        {isUser ? <User className="w-4 h-4" /> : <Brain className="w-4 h-4" />}
      </div>

      {/* Message Content */}
      <div className={`flex-1 min-w-0 ${isUser ? "text-right" : ""}`}>
        <div
          className={`
            inline-block max-w-[90%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed
            ${isUser
              ? "bg-[#64FFDA]/10 text-[#E6F1FF] border border-[#64FFDA]/20 rounded-tr-md"
              : "bg-[#112240] text-[#E6F1FF] border border-[#64FFDA]/10 rounded-tl-md"
            }
          `}
        >
          <p className="whitespace-pre-wrap break-words">{message.content}</p>
        </div>

        {/* Presentation badge */}
        {hasPresentation && message.presentation && (
          <div className={`mt-2 ${isUser ? "flex justify-end" : ""}`}>
            <span className="inline-flex items-center gap-1.5 px-3 py-1 bg-[#64FFDA]/10 border border-[#64FFDA]/20 rounded-full text-xs text-[#64FFDA]">
              <Brain className="w-3 h-3" />
              {t("msg.slidesGenerated", message.presentation.slides.length)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

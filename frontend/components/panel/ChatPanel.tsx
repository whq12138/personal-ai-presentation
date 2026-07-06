"use client";

import { useRef, useEffect } from "react";
import { MessageSquare, Play, History } from "lucide-react";
import { ChatMessageBubble } from "./ChatMessage";
import { MarkdownInput } from "./MarkdownInput";
import { TypingIndicator } from "@/components/ui/TypingIndicator";
import { Button } from "@/components/ui/Button";
import { Spinner } from "@/components/ui/Spinner";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { ChatMessage, GenerationStatus } from "@/lib/types";

interface ChatPanelProps {
  messages: ChatMessage[];
  generationStatus: GenerationStatus;
  onSubmit: (text: string) => void;
  onEdit?: (instruction: string) => void;
  onLoadDemo?: () => void;
  onToggleHistory?: () => void;
}

export function ChatPanel({
  messages,
  generationStatus,
  onSubmit,
  onEdit,
  onLoadDemo,
  onToggleHistory,
}: ChatPanelProps) {
  const { t } = useLanguage();
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, generationStatus]);

  const isLoading =
    generationStatus === "generating" || generationStatus === "editing";
  const isEditing = generationStatus === "editing";

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="px-4 py-3 border-b border-[#64FFDA]/10 flex items-center gap-3">
        <div className="w-2 h-2 rounded-full bg-[#64FFDA] animate-pulse shadow-[0_0_6px_rgba(100,255,218,0.5)]" />
        <h2 className="text-sm font-semibold text-[#E6F1FF]">
          {t("chat.title")}
        </h2>
        <span className="text-[10px] text-[#495670] ml-auto">
          {t("chat.shortcut")}
        </span>
        {onToggleHistory && (
          <button onClick={onToggleHistory} className="text-[#495670] hover:text-[#64FFDA] cursor-pointer" title="History">
            <History className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Messages */}
      <div
        ref={scrollRef}
        className="flex-1 overflow-y-auto py-2 space-y-1 scroll-smooth"
      >
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-center px-8">
            <div className="w-16 h-16 bg-[#112240] border border-[#64FFDA]/10 rounded-2xl flex items-center justify-center mb-4">
              <MessageSquare className="w-8 h-8 text-[#495670]" />
            </div>
            <h3 className="text-[#8892B0] font-medium mb-2">
              {t("chat.emptyTitle")}
            </h3>
            <p className="text-sm text-[#495670] leading-relaxed mb-5">
              {t("chat.emptyDesc")}
            </p>
            {onLoadDemo && (
              <Button
                variant="secondary"
                size="sm"
                onClick={onLoadDemo}
                leftIcon={<Play className="w-4 h-4" />}
              >
                {t("chat.loadDemo")}
              </Button>
            )}
          </div>
        ) : (
          messages.map((msg) => (
            <ChatMessageBubble key={msg.id} message={msg} />
          ))
        )}

        {/* Loading indicators with stage-specific labels */}
        {isLoading && (
          <div className="px-4 py-3">
            <div className="flex items-center gap-3">
              <TypingIndicator />
              <div className="flex-1" />
            </div>
            <div className="mt-2">
              <Spinner size="sm" />
              <p className="text-xs text-[#495670] text-center mt-2">
                {isEditing
                  ? t("status.layouting")
                  : generationStatus === "generating"
                  ? t("status.generating")
                  : t("status.layouting")}
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Input — changes between Generate and Edit mode */}
      <MarkdownInput
        onSubmit={onSubmit}
        onEdit={onEdit}
        isLoading={isLoading}
        isEditMode={messages.length > 0 && !!onEdit}
      />
    </div>
  );
}

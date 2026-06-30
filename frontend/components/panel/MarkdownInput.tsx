"use client";

import { useState, useRef, KeyboardEvent } from "react";
import { Wand2, Pencil } from "lucide-react";
import { Button } from "@/components/ui/Button";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface MarkdownInputProps {
  onSubmit: (text: string) => void;
  onEdit?: (instruction: string) => void;
  isLoading: boolean;
  isEditMode?: boolean;
}

export function MarkdownInput({
  onSubmit,
  onEdit,
  isLoading,
  isEditMode = false,
}: MarkdownInputProps) {
  const { t } = useLanguage();
  const [text, setText] = useState("");
  const [isEditing, setIsEditing] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = () => {
    if (!text.trim() || isLoading) return;
    if (isEditMode && isEditing && onEdit) {
      onEdit(text.trim());
    } else {
      onSubmit(text.trim());
    }
    setText("");
    setIsEditing(false);
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if ((e.metaKey || e.ctrlKey) && e.key === "Enter") {
      e.preventDefault();
      handleSubmit();
    }
  };

  const placeholder = isEditMode && isEditing
    ? t("input.editPlaceholder")
    : t("input.placeholder");

  return (
    <div className="p-4 border-t border-[#64FFDA]/10 bg-[#0A192F]/80 backdrop-blur-sm">
      {/* Edit mode toggle (only shown when there are slides) */}
      {isEditMode && onEdit && (
        <div className="flex items-center gap-2 mb-2">
          <button
            onClick={() => setIsEditing(false)}
            className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
              !isEditing
                ? "bg-[#64FFDA]/10 text-[#64FFDA] border border-[#64FFDA]/20"
                : "text-[#495670] hover:text-[#8892B0]"
            }`}
          >
            {t("input.generate")}
          </button>
          <button
            onClick={() => setIsEditing(true)}
            className={`text-[10px] px-2 py-0.5 rounded-full transition-colors ${
              isEditing
                ? "bg-[#FFD700]/10 text-[#FFD700] border border-[#FFD700]/20"
                : "text-[#495670] hover:text-[#8892B0]"
            }`}
          >
            {t("input.edit")}
          </button>
        </div>
      )}

      <div className="relative">
        <textarea
          ref={textareaRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          rows={isEditing ? 3 : 4}
          className={`
            w-full bg-[#050A1A] border rounded-xl
            text-[#E6F1FF] placeholder-[#495670] text-sm
            px-4 py-3 pr-12 resize-none
            focus:outline-none focus:ring-2 transition-all duration-200
            font-mono
            ${isEditing
              ? "border-[#FFD700]/20 focus:ring-[#FFD700]/30 focus:border-[#FFD700]/40"
              : "border-[#64FFDA]/10 focus:ring-[#64FFDA]/30 focus:border-[#64FFDA]/40"
            }
          `}
        />
        <div className="absolute bottom-3 right-3 flex items-center gap-2">
          <span className="text-[10px] text-[#495670] hidden sm:block">
            ⌘+↵
          </span>
          <Button
            size="sm"
            onClick={handleSubmit}
            isLoading={isLoading}
            disabled={!text.trim() || isLoading}
            variant={isEditing ? "secondary" : "primary"}
            leftIcon={
              isLoading ? undefined : isEditing ? (
                <Pencil className="w-4 h-4" />
              ) : (
                <Wand2 className="w-4 h-4" />
              )
            }
          >
            {isEditing ? t("input.edit") : t("input.generate")}
          </Button>
        </div>
      </div>
    </div>
  );
}

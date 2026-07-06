"use client";

import { useState, useEffect, useCallback } from "react";
import { History, Trash2, FileText, ChevronRight, Loader2 } from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";
import { Badge } from "@/components/ui/Badge";
import { useLanguage } from "@/lib/i18n/LanguageContext";

interface SavedItem {
  id: string;
  title: string;
  slide_count: number;
  created_at: string;
  updated_at: string;
}

interface Props {
  onLoad: (id: string) => void;
  onClose: () => void;
}

export function HistoryPanel({ onLoad, onClose }: Props) {
  const { getAccessToken, logout } = useAuth();
  const { t } = useLanguage();
  const [items, setItems] = useState<SavedItem[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchHistory = useCallback(async () => {
    const token = getAccessToken();
    if (!token) return;
    try {
      const res = await fetch("/api/presentation/history", {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) return;
      const data = await res.json();
      setItems(data.items || []);
    } catch { /* ignore */ }
    setLoading(false);
  }, [getAccessToken]);

  useEffect(() => { fetchHistory(); }, [fetchHistory]);

  return (
    <div className="absolute inset-0 z-40 flex flex-col bg-[#0A192F]">
      <div className="flex items-center justify-between px-4 py-3 border-b border-[#64FFDA]/10">
        <div className="flex items-center gap-2">
          <History className="w-4 h-4 text-[#64FFDA]" />
          <h3 className="text-sm font-semibold text-[#E6F1FF]">
            {t("lang.label") === "中" ? "文稿历史" : "History"}
          </h3>
        </div>
        <button onClick={onClose} className="text-xs text-[#495670] hover:text-[#E6F1FF] cursor-pointer">
          {t("lang.label") === "中" ? "关闭" : "Close"}
        </button>
      </div>

      <div className="flex-1 overflow-y-auto">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-5 h-5 text-[#64FFDA] animate-spin" />
          </div>
        ) : items.length === 0 ? (
          <p className="text-xs text-[#495670] text-center py-12">
            {t("lang.label") === "中" ? "暂无保存的文稿" : "No saved presentations"}
          </p>
        ) : (
          items.map((item) => (
            <button
              key={item.id}
              onClick={() => onLoad(item.id)}
              className="w-full flex items-center gap-3 px-4 py-3 border-b border-[#64FFDA]/5 hover:bg-[#64FFDA]/5 transition-colors text-left cursor-pointer"
            >
              <FileText className="w-4 h-4 text-[#495670] flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm text-[#E6F1FF] truncate">{item.title}</p>
                <div className="flex items-center gap-2 mt-0.5">
                  <Badge variant="default">{item.slide_count} slides</Badge>
                  <span className="text-[10px] text-[#495670]">
                    {new Date(item.created_at).toLocaleDateString()}
                  </span>
                </div>
              </div>
              <ChevronRight className="w-4 h-4 text-[#495670] flex-shrink-0" />
            </button>
          ))
        )}
      </div>
    </div>
  );
}

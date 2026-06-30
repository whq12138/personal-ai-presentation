"use client";

import { Sparkles, Presentation, LogOut, User, Crown, Zap } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { PremiumModal } from "@/components/layout/PremiumModal";
import { useLanguage } from "@/lib/i18n/LanguageContext";
import { useAuth } from "@/lib/auth/AuthContext";
import { useState, useRef, useEffect } from "react";

export function Navbar() {
  const { t, toggleLang, lang } = useLanguage();
  const { user, logout, isAuthenticated } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const [premiumOpen, setPremiumOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setMenuOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 h-14 bg-[#0A192F]/90 backdrop-blur-xl border-b border-[#64FFDA]/10">
      <div className="h-full max-w-full mx-auto px-4 flex items-center justify-between">
        {/* Logo */}
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-gradient-to-br from-[#64FFDA] to-[#45E0BE] rounded-lg flex items-center justify-center shadow-[0_0_15px_rgba(100,255,218,0.2)]">
            <Presentation className="w-4 h-4 text-[#0A192F]" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-[#E6F1FF] tracking-tight">
              {t("brand.name")}
            </span>
            <span className="text-lg font-bold text-[#64FFDA] tracking-tight">
              {t("brand.tagline")}
            </span>
          </div>
          <Badge variant="accent">{t("brand.badge")}</Badge>
        </div>

        {/* Right section */}
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 text-xs text-[#8892B0]">
            <Sparkles className="w-3.5 h-3.5 text-[#FFD700]" />
            <span>{t("brand.poweredBy")}</span>
          </div>

          {/* Language switcher */}
          <Button
            variant="ghost"
            size="sm"
            onClick={toggleLang}
            className="text-xs font-mono px-2"
          >
            {lang === "en" ? "中" : "EN"}
          </Button>

          {/* User menu (authenticated) */}
          {isAuthenticated && user && (
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setMenuOpen(!menuOpen)}
                className="flex items-center gap-2 px-2.5 py-1.5 rounded-lg bg-[#112240] border border-[#64FFDA]/10 hover:border-[#64FFDA]/30 transition-all cursor-pointer"
              >
                <div className="w-6 h-6 rounded-md bg-[#64FFDA]/10 flex items-center justify-center">
                  <User className="w-3.5 h-3.5 text-[#64FFDA]" />
                </div>
                <div className="text-left hidden sm:block">
                  <div className="text-xs font-medium text-[#E6F1FF] leading-tight max-w-[100px] truncate">
                    {user.email}
                  </div>
                  <div className="text-[10px] text-[#64FFDA] flex items-center gap-1">
                    {user.tier === "premium" ? (
                      <Crown className="w-3 h-3 text-[#FFD700]" />
                    ) : (
                      <Zap className="w-3 h-3" />
                    )}
                    {user.tier === "premium" ? "Premium" : "Free"}
                  </div>
                </div>
              </button>

              {/* Dropdown */}
              {menuOpen && (
                <div className="absolute right-0 top-full mt-2 w-56 bg-[#112240] border border-[#64FFDA]/20 rounded-xl shadow-xl overflow-hidden z-50">
                  {/* User info */}
                  <div className="px-4 py-3 border-b border-[#64FFDA]/10">
                    <p className="text-sm font-medium text-[#E6F1FF] truncate">
                      {user.email}
                    </p>
                    <div className="flex items-center gap-2 mt-1">
                      <Badge variant={user.tier === "premium" ? "warning" : "accent"}>
                        {user.tier === "premium" ? "Premium" : "Free"}
                      </Badge>
                      {user.tier === "free" && (
                        <span className="text-[10px] text-[#FFD700]/70">
                          {t("brand.badge") === "MVP" ? "3/hr · 10/day" : "3次/时 · 10次/天"}
                        </span>
                      )}
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="py-1">
                    {user.tier === "free" && (
                      <button
                        onClick={() => { setMenuOpen(false); setPremiumOpen(true); }}
                        className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-[#FFD700] hover:bg-[#FFD700]/5 transition-colors cursor-pointer"
                      >
                        <Crown className="w-4 h-4" />
                        Upgrade to Premium
                      </button>
                    )}
                    <button
                      onClick={() => {
                        setMenuOpen(false);
                        logout();
                      }}
                      className="w-full flex items-center gap-3 px-4 py-2.5 text-sm text-red-400 hover:bg-red-500/5 transition-colors cursor-pointer"
                    >
                      <LogOut className="w-4 h-4" />
                      Sign Out
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>

      {/* 收银台弹窗 */}
      <PremiumModal open={premiumOpen} onClose={() => setPremiumOpen(false)} />
    </nav>
  );
}

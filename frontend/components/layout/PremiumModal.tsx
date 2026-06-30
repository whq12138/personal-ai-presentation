"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  X, Crown, Zap, Sparkles, Infinity, CheckCircle2,
  Loader2, QrCode, CreditCard, ArrowRight, PartyPopper,
} from "lucide-react";
import { useAuth } from "@/lib/auth/AuthContext";

/* ── 套餐配置 ── */
const PLANS = [
  {
    id: "monthly", name: "月度会员", price: "¥29.90", period: "/月",
    desc: "适合短期项目", features: [
      "60 次/小时 AI 生成", "全部 9 种高级布局",
      "高清图片配图", "无水印 PPTX 导出", "优先客服支持",
    ],
    icon: Zap, highlight: false,
  },
  {
    id: "yearly", name: "年度会员", price: "¥199.00", period: "/年",
    desc: "最受欢迎 · 省 44%", features: [
      "所有月度权益", "200 次/天 AI 生成",
      "优先任务队列", "自定义品牌模板 (即将推出)", "专属 API 访问",
    ],
    icon: Crown, highlight: true, badge: "🔥 热门",
  },
  {
    id: "lifetime", name: "永久会员", price: "¥499.00", period: "",
    desc: "一次购买，终身使用", features: [
      "所有年度权益", "无限次 AI 生成",
      "永久更新", "VIP 专属通道", "创始会员徽章",
    ],
    icon: Infinity, highlight: false,
  },
];

/* ── Props ── */
interface Props {
  open: boolean;
  onClose: () => void;
}

/* ── 内置简易 canvas-confetti ── */
function fireConfetti() {
  const colors = ["#64FFDA", "#FFD700", "#FF6B9D", "#45E0BE", "#FF9F43"];
  for (let i = 0; i < 80; i++) {
    const particle = document.createElement("div");
    const size = Math.random() * 8 + 4;
    particle.style.cssText = `
      position:fixed; z-index:9999; pointer-events:none;
      width:${size}px; height:${size * 1.5}px;
      background:${colors[Math.floor(Math.random() * colors.length)]};
      left:${Math.random() * 100}vw; top:-10px;
      border-radius:2px; opacity:1;
      animation: confetti ${Math.random() * 2 + 2}s ease-out forwards;
      animation-delay:${Math.random() * 0.8}s;
    `;
    document.body.appendChild(particle);
    setTimeout(() => particle.remove(), 4000);
  }
  // Inject keyframes once
  if (!document.getElementById("confetti-style")) {
    const style = document.createElement("style");
    style.id = "confetti-style";
    style.textContent = `
      @keyframes confetti {
        0% { transform:translateY(0) rotate(0deg); opacity:1; }
        100% { transform:translateY(100vh) rotate(${360 + Math.random() * 720}deg); opacity:0; }
      }`;
    document.head.appendChild(style);
  }
}

export function PremiumModal({ open, onClose }: Props) {
  const { user, getAccessToken, refreshAccessToken } = useAuth();
  const [step, setStep] = useState<"plans" | "paying" | "success">("plans");
  const [selectedPlan, setSelectedPlan] = useState("yearly");
  const [channel, setChannel] = useState<"stripe" | "wechat">("wechat");
  const [orderNo, setOrderNo] = useState("");
  const [qrUrl, setQrUrl] = useState("");
  const [checkoutUrl, setCheckoutUrl] = useState("");
  const [polling, setPolling] = useState(false);
  const [simulating, setSimulating] = useState(false);
  const [error, setError] = useState("");
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Cleanup polling on unmount
  useEffect(() => () => {
    if (pollRef.current) clearInterval(pollRef.current);
  }, []);

  /* ── 创建订单 ── */
  const createOrder = useCallback(async () => {
    setError("");
    setStep("paying");
    try {
      const token = getAccessToken();
      const res = await fetch(
        `/api/payment/create-order`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({ plan: selectedPlan, channel }),
        },
      );
      if (!res.ok) throw new Error("创建订单失败");
      const data = await res.json();
      setOrderNo(data.order_no);
      setQrUrl(data.qr_url || "");
      setCheckoutUrl(data.checkout_url || "");
      startPollOrder(data.order_no);
    } catch (err: any) {
      setError(err.message);
      setStep("plans");
    }
  }, [selectedPlan, channel, getAccessToken]);

  /* ── 轮询订单状态 (2s) ── */
  const startPollOrder = (orderNo: string) => {
    setPolling(true);
    const poll = async () => {
      try {
        const token = getAccessToken();
        const res = await fetch(
          `/api/payment/order-status/${orderNo}`,
          { headers: { Authorization: `Bearer ${token}` } },
        );
        if (!res.ok) return;
        const data = await res.json();
        if (data.status === "paid") {
          clearInterval(pollRef.current!);
          setPolling(false);
          setStep("success");
          fireConfetti();
          // 刷新用户 tier 状态 (简单 reload)
          setTimeout(() => window.location.reload(), 2500);
        }
      } catch { /* ignore poll errors */ }
    };
    pollRef.current = setInterval(poll, 2000);
    poll(); // immediate first poll
  };

  /* ── 沙箱模拟支付 ── */
  const simulatePayment = async () => {
    setSimulating(true);
    setError("");
    try {
      const token = getAccessToken();
      const res = await fetch(
        `/api/payment/simulate-success`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
        },
      );
      if (!res.ok) throw new Error("模拟支付失败");
      clearInterval(pollRef.current!);
      setPolling(false);
      setStep("success");
      fireConfetti();
      setTimeout(() => window.location.reload(), 2500);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setSimulating(false);
    }
  };

  return (
    <AnimatePresence>
      {open && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-[100] flex items-center justify-center p-4"
        >
          {/* 暗色遮罩 */}
          <div className="absolute inset-0 bg-black/70 backdrop-blur-sm" onClick={onClose} />

          {/* Modal */}
          <motion.div
            initial={{ scale: 0.9, y: 20, opacity: 0 }}
            animate={{ scale: 1, y: 0, opacity: 1 }}
            exit={{ scale: 0.9, y: 20, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="relative z-10 w-full max-w-3xl max-h-[90vh] overflow-y-auto
                       bg-[#112240] border border-[#64FFDA]/20 rounded-2xl shadow-[0_0_80px_rgba(100,255,218,0.08)]
                       p-6 md:p-8"
          >
            {/* 关闭按钮 */}
            <button
              onClick={onClose}
              className="absolute top-4 right-4 text-[#495670] hover:text-[#E6F1FF] transition-colors cursor-pointer"
            >
              <X className="w-5 h-5" />
            </button>

            {/* ═══ 步骤 1: 选择套餐 ═══ */}
            {step === "plans" && (
              <>
                <div className="text-center mb-8">
                  <div className="inline-flex items-center gap-2 px-3 py-1 bg-[#FFD700]/10 border border-[#FFD700]/20 rounded-full mb-4">
                    <Crown className="w-4 h-4 text-[#FFD700]" />
                    <span className="text-sm text-[#FFD700] font-medium">升级 Premium</span>
                  </div>
                  <h2 className="text-2xl font-bold text-[#E6F1FF]">选择适合你的套餐</h2>
                  <p className="text-sm text-[#8892B0] mt-2">
                    当前: <span className="text-[#64FFDA]">Free</span> 计划 ·
                    解锁全部 9 种高级布局 + 60 次/小时生成
                  </p>
                </div>

                {/* 三列套餐 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                  {PLANS.map((plan) => {
                    const Icon = plan.icon;
                    return (
                      <div
                        key={plan.id}
                        onClick={() => setSelectedPlan(plan.id)}
                        className={`relative p-5 rounded-2xl border cursor-pointer transition-all duration-200
                          ${selectedPlan === plan.id
                            ? "border-[#64FFDA] bg-[#64FFDA]/5 shadow-[0_0_20px_rgba(100,255,218,0.1)]"
                            : "border-[#64FFDA]/10 bg-[#0A192F]/50 hover:border-[#64FFDA]/30"
                          }`}
                      >
                        {plan.badge && (
                          <span className="absolute -top-2 right-3 px-2 py-0.5 bg-[#FFD700] text-[#0A192F] text-[10px] font-bold rounded-full">
                            {plan.badge}
                          </span>
                        )}
                        <Icon className={`w-8 h-8 mb-3 ${
                          selectedPlan === plan.id ? "text-[#64FFDA]" : "text-[#495670]"
                        }`} />
                        <h3 className="text-lg font-bold text-[#E6F1FF] mb-1">{plan.name}</h3>
                        <div className="mb-2">
                          <span className="text-2xl font-black text-[#64FFDA]">{plan.price}</span>
                          <span className="text-xs text-[#8892B0]">{plan.period}</span>
                        </div>
                        <p className="text-xs text-[#8892B0] mb-3">{plan.desc}</p>
                        <ul className="space-y-1.5">
                          {plan.features.map((f, i) => (
                            <li key={i} className="flex items-start gap-2 text-xs text-[#8892B0]">
                              <CheckCircle2 className="w-3 h-3 text-[#64FFDA] flex-shrink-0 mt-0.5" />
                              {f}
                            </li>
                          ))}
                        </ul>
                      </div>
                    );
                  })}
                </div>

                {/* 支付方式 + 确认按钮 */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <span className="text-xs text-[#8892B0]">支付方式:</span>
                    {[
                      { id: "wechat" as const, label: "微信", icon: QrCode },
                      { id: "stripe" as const, label: "Stripe", icon: CreditCard },
                    ].map((ch) => (
                      <button
                        key={ch.id}
                        onClick={() => setChannel(ch.id)}
                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs border transition-all cursor-pointer ${
                          channel === ch.id
                            ? "border-[#64FFDA] bg-[#64FFDA]/10 text-[#64FFDA]"
                            : "border-[#64FFDA]/10 text-[#8892B0] hover:border-[#64FFDA]/30"
                        }`}
                      >
                        <ch.icon className="w-3.5 h-3.5" /> {ch.label}
                      </button>
                    ))}
                  </div>
                  <button
                    onClick={createOrder}
                    className="flex items-center gap-2 px-6 py-2.5 bg-[#64FFDA] text-[#0A192F] font-bold rounded-xl
                               hover:bg-[#45E0BE] transition-colors cursor-pointer"
                  >
                    立即升级 <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
                {error && <p className="text-red-400 text-xs mt-3 text-center">{error}</p>}
              </>
            )}

            {/* ═══ 步骤 2: 支付中 ═══ */}
            {step === "paying" && (
              <div className="text-center py-6">
                <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-[#64FFDA]/10 flex items-center justify-center">
                  {channel === "wechat" ? (
                    <QrCode className="w-8 h-8 text-[#64FFDA]" />
                  ) : (
                    <CreditCard className="w-8 h-8 text-[#64FFDA]" />
                  )}
                </div>
                <h3 className="text-lg font-bold text-[#E6F1FF] mb-2">扫码支付</h3>
                <p className="text-sm text-[#8892B0] mb-6">
                  {channel === "wechat" ? "请使用微信扫描二维码完成支付" : "即将跳转到 Stripe 支付页面"}
                </p>

                {/* 二维码区域 */}
                {qrUrl && (
                  <div className="w-48 h-48 mx-auto mb-4 bg-white rounded-2xl flex items-center justify-center border-2 border-[#64FFDA]/20">
                    <span className="text-[10px] text-gray-400">
                      二维码加载中...<br />请调用支付网关
                    </span>
                  </div>
                )}

                {checkoutUrl && (
                  <a
                    href={checkoutUrl}
                    target="_blank"
                    className="inline-flex items-center gap-2 px-6 py-2.5 bg-[#64FFDA] text-[#0A192F] font-bold rounded-xl cursor-pointer"
                  >
                    <CreditCard className="w-4 h-4" /> 前往 Stripe 支付
                  </a>
                )}

                {/* 轮询指示器 */}
                <div className="mt-6 flex items-center justify-center gap-2 text-sm text-[#8892B0]">
                  <Loader2 className="w-4 h-4 animate-spin text-[#64FFDA]" />
                  {polling ? "等待支付确认中..." : "订单已创建"}
                </div>

                {/* ─── 沙箱模拟支付按钮 ─── */}
                <div className="mt-4 p-3 border border-dashed border-[#FFD700]/30 rounded-xl bg-[#FFD700]/5">
                  <p className="text-xs text-[#FFD700]/70 text-center mb-2">
                    🧪 开发者沙箱模式 — 无需真实支付
                  </p>
                  <button
                    onClick={simulatePayment}
                    disabled={simulating}
                    className="w-full py-2.5 bg-[#FFD700] text-[#0A192F] font-bold rounded-xl
                               hover:bg-yellow-400 transition-colors cursor-pointer
                               disabled:opacity-50 text-sm"
                  >
                    {simulating ? (
                      <span className="flex items-center justify-center gap-2">
                        <Loader2 className="w-4 h-4 animate-spin" /> 处理中...
                      </span>
                    ) : (
                      "【测试】一键模拟支付成功"
                    )}
                  </button>
                </div>

                <button
                  onClick={() => { clearInterval(pollRef.current!); setStep("plans"); }}
                  className="mt-3 text-xs text-[#495670] hover:text-[#8892B0] transition-colors cursor-pointer"
                >
                  取消并返回
                </button>
              </div>
            )}

            {/* ═══ 步骤 3: 支付成功 ═══ */}
            {step === "success" && (
              <div className="text-center py-10">
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 15 }}
                  className="w-20 h-20 mx-auto mb-4 rounded-full bg-[#64FFDA]/20 flex items-center justify-center"
                >
                  <PartyPopper className="w-10 h-10 text-[#FFD700]" />
                </motion.div>
                <motion.h2
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.2 }}
                  className="text-2xl font-bold text-[#E6F1FF] mb-2"
                >
                  🎉 支付成功！
                </motion.h2>
                <motion.p
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.4 }}
                  className="text-sm text-[#8892B0] mb-4"
                >
                  你已升级为 Premium 会员，享受全部高级功能
                </motion.p>
                <motion.div
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: 0.6 }}
                  className="flex items-center justify-center gap-2 text-xs text-[#64FFDA]"
                >
                  <Sparkles className="w-4 h-4" />
                  正在刷新权限...
                </motion.div>
              </div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

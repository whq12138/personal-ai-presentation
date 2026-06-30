"""
Prompt 注入防护盾 (Input Sanitizer Guard) — Phase 3 Step 3

双层防御机制:
  1. 高风险模式 (REJECT): 直接拦截 + 返回 400，不允许进入 LLM 管线
  2. 中风险模式 (FILTER): 替换可疑片段为 [filtered]，记录日志后放行

支持中英文双语攻击模式识别。
"""

import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class RiskLevel(Enum):
    CLEAN = "clean"       # 安全，无需处理
    FILTER = "filter"     # 中风险：过滤后放行
    REJECT = "reject"     # 高风险：直接拦截


# ================================================================
# 高风险拦截模式 (命中后直接 HTTP 400 拒绝)
# 这些是明确的 jailbreak/override 攻击，不应进入任何 LLM 上下文
# ================================================================

REJECT_PATTERNS: list[tuple[str, str]] = [
    # —— 英文直接劫持 ——
    (r"ignore\s+(all\s+)?(previous|above|prior|your|the\s+above)\s+(instructions?|prompts?|rules?|constraints?)",
     "Ignore-previous-instructions injection"),
    (r"(forget|erase|delete)\s+(everything|all|your)\s+(you\s+)?(know|learned|were\s+told|memory)",
     "Forget-everything injection"),
    (r"(you\s+are\s+now|from\s+now\s+on\s+you\s+are)\s+(a|an)\s+(hacker|unfiltered|unrestricted|evil|malicious)",
     "Role-hijack injection"),
    (r"pretend\s+(you\s+are|to\s+be)\s+(a|an)\s+(different|other)\s+(ai|model|system)",
     "Pretend injection"),
    (r"DAN\s+(mode|prompt|jailbreak)",
     "DAN jailbreak"),
    (r"developer\s+mode\s+(enabled|activated|on)",
     "Developer-mode jailbreak"),
    (r"(print|output|display|reveal|show|tell\s+me)\s+(your|the)\s+(system\s+prompt|original\s+instructions?|base\s+prompt)",
     "System-prompt exfiltration"),
    (r"(what|what's)\s+(is\s+)?(your|the)\s+(system\s+prompt|secret\s+instructions?)",
     "Prompt probing"),

    # —— 中文直接劫持 ——
    (r"忽略.{0,6}(指令|提示|规则|要求|约束|限制)",
     "中文-忽略指令注入"),
    (r"(忘记|忘掉|清除|删除).{0,6}(记忆|知识|学到的|被告知的)",
     "中文-清除记忆注入"),
    (r"(现在|从现在开始).{0,6}(扮演|你是|是).{0,6}(黑客|不受限制|无约束|邪恶)",
     "中文-角色劫持"),
    (r"(打印|输出|显示|告诉|展示).{0,6}(系统提示|原始指令|底层指令|prompt)",
     "中文-Prompt 窃取"),
    (r"(绕过|跳过|无视).{0,4}(限制|约束|安全|过滤|规则|审查)",
     "中文-绕过限制"),
    (r"不要.{0,4}(遵守|遵循|服从|听从).{0,4}(指令|规则|限制)",
     "中文-拒绝服从"),
    (r"你.{0,4}(必须|一定要|只能).{0,4}(回答|输出|响应|回复)",
     "中文-强制输出操控"),
    (r"假装.{0,10}(AI|人工智能|不受限制|不受控制)",
     "中文-假装注入"),

    # —— 通用高危 ——
    (r"(leak|expose|dump)\s+(the\s+)?(system\s+)?(prompt|instructions?|config|secrets?)",
     "Credential leak attempt"),
    (r"bypass\s+(all\s+)?(restrictions?|safety|content\s+filter|guardrails?)",
     "Bypass attempt"),
]


# ================================================================
# 中风险过滤模式 (替换为 [filtered]，不拦截请求)
# ================================================================

FILTER_PATTERNS: list[tuple[str, str]] = [
    (r"new\s+(system\s+)?prompt",
     "New-prompt insertion"),
    (r"system\s+message\s*:",
     "System-message injection"),
    (r"<script[\s>]",
     "XSS script tag"),
    (r"javascript\s*:",
     "JS protocol injection"),
    (r"onerror\s*=",
     "onerror handler injection"),
    (r"onload\s*=",
     "onload handler injection"),
    (r"(format|输出格式|回复格式)\s+(your|你)(的)?\s+(response|output|回答|输出)",
     "Output-format manipulation"),
]


# ================================================================
# 核心安全接口
# ================================================================

def assess_risk(text: str) -> RiskLevel:
    """
    评估文本的风险等级。

    返回:
      REJECT — 命中高风险拦截模式
      FILTER — 命中中风险过滤模式
      CLEAN  — 未命中任何模式
    """
    if not text or not text.strip():
        return RiskLevel.CLEAN

    # 先检查高风险 (优先级更高)
    for pattern, label in REJECT_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"🚫 高风险注入拦截: {label} | 文本前80字: {text[:80]}")
            return RiskLevel.REJECT

    # 再检查中风险
    for pattern, label in FILTER_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            logger.warning(f"⚠️ 中风险模式过滤: {label}")
            return RiskLevel.FILTER

    return RiskLevel.CLEAN


def filter_text(text: str) -> tuple[str, bool]:
    """
    洗涤文本 — 将中风险敏感词替换为 [filtered]。

    返回: (safe_text, was_filtered)
    """
    if not text or not text.strip():
        return text, False

    result = text
    filtered = False

    for pattern, label in FILTER_PATTERNS:
        if re.search(pattern, result, re.IGNORECASE):
            result = re.sub(pattern, "[filtered]", result, flags=re.IGNORECASE)
            filtered = True
            logger.info(f"   过滤: {label}")

    return result, filtered


def sanitize_prompt_input(text: str) -> tuple[str, RiskLevel]:
    """
    【主接口】完整的输入流安全洗涤。

    三步处理:
      1. assess_risk  → REJECT → 调用方抛 HTTP 400
      2. filter_text  → 替换中风险片段
      3. 返回清洁文本 + 风险评估结果

    返回: (safe_text, risk_level)
    """
    risk = assess_risk(text)
    if risk == RiskLevel.REJECT:
        return text, RiskLevel.REJECT

    if risk == RiskLevel.FILTER:
        safe_text, _ = filter_text(text)
        return safe_text, RiskLevel.FILTER

    return text, RiskLevel.CLEAN


# ——— 向后兼容的旧接口 ———
def sanitize_user_input(text: str) -> tuple[str, bool]:
    """
    旧版兼容接口 — 始终返回 (text, was_modified)。
    注意: REJECT 级别在此接口中只过滤不拦截，调用方需用 sanitize_prompt_input 实现拦截逻辑。
    """
    safe, risk = sanitize_prompt_input(text)
    return safe, risk != RiskLevel.CLEAN


def validate_input_length(text: str, max_length: int = 25000) -> bool:
    return len(text) <= max_length


def validate_no_html_tags(text: str) -> bool:
    return not bool(re.search(
        r"<\s*(script|iframe|object|embed|form|input|img)", text, re.IGNORECASE
    ))

#!/usr/bin/env python3
"""
DeepSeek / LLM 连通性检查工具 (Sanity Check)

用法:
    cd backend
    python check_llm.py

读取 .env 中的 LLM_API_KEY, LLM_API_BASE, LLM_MODEL_NAME，
发起一次极简 API 请求并校验返回格式。

退出码: 0=成功, 1=失败
"""

import asyncio
import os
import sys


def load_env():
    """从 backend/.env 加载环境变量 (不依赖 python-dotenv)。"""
    env_path = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_path):
        # Fallback: try current directory
        env_path = ".env"
        if not os.path.exists(env_path):
            print("⚠️  未找到 .env 文件，使用系统环境变量")
            print("   (从 backend/ 目录运行可自动加载)")
            print()
            return

    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, val = line.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


async def check_llm():
    """异步发起 LLM 请求并验证返回。"""
    load_env()

    api_key = os.getenv("LLM_API_KEY", "")
    api_base = os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1")
    model = os.getenv("LLM_MODEL_NAME", "deepseek-chat")

    # ── 环境变量检查 ──
    if not api_key or api_key.startswith("sk-your-") or "placeholder" in api_key.lower():
        print("❌ LLM_API_KEY 未配置或仍是占位符！")
        print(f"   当前值: {api_key[:20]}{'...' if len(api_key) > 20 else ''}")
        print()
        print("🔧 请编辑 backend/.env，填入真实 Key:")
        print("   LLM_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        print()
        print("   DeepSeek Key 获取: https://platform.deepseek.com/api_keys")
        print("   硅基流动 Key 获取: https://siliconflow.cn/account/ak")
        return 1

    provider = api_base.split("//")[1].split("/")[0] if "//" in api_base else "unknown"
    print(f"🔍 检查 LLM 连通性...")
    print(f"   端点:  {api_base}")
    print(f"   模型:  {model}")
    print(f"   供应商: {provider}")

    # 检测代理配置
    http_proxy = os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy")
    https_proxy = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
    if http_proxy or https_proxy:
        print(f"   HTTP_PROXY:  {http_proxy or '(not set)'}")
        print(f"   HTTPS_PROXY: {https_proxy or '(not set)'}")
    print()

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=api_key, base_url=api_base, timeout=30.0)

        # ── 极简请求: 让 LLM 返回一个固定 JSON ──
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a JSON-only testing API. "
                        "Reply with exactly: {\"status\":\"ok\",\"model\":\"" + model + "\"}"
                        "No markdown, no explanation — just the raw JSON object."
                    ),
                },
                {"role": "user", "content": "ping"},
            ],
            max_tokens=128,
            temperature=0,
        )

        raw = response.choices[0].message.content or ""
        print(f"📥 原始返回: {raw[:300]}")

        # ── 校验 JSON ──
        import json
        try:
            # Strip possible markdown fences
            if raw.strip().startswith("```"):
                raw = raw.strip().replace("```json", "").replace("```", "").strip()
            data = json.loads(raw)
        except json.JSONDecodeError:
            print()
            print("⚠️  LLM 返回了非 JSON 内容，但 API 连通正常。")
            print("   这说明 Key 有效、网络可达，只是 prompt 未被完美执行。")
            print("   DeepSeek 返回: " + raw[:200])
            return 0

        if data.get("status") == "ok":
            print()
            print("✅ LLM 连通性检查通过！")
            print(f"   Key 有效，模型 {model} 响应正常。")
            print(f"   调用端点: {api_base}")
            print()
            print("🚀 可以开始使用 Personal AI Presentation 了！")
            print("   运行: cd ../frontend && pnpm dev")
            return 0
        else:
            print()
            print(f"⚠️  LLM 返回了非预期内容: {data}")
            print("   但网络连通正常，可以尝试使用。")
            return 0

    except ImportError:
        print("❌ 缺少 openai 库！")
        print("   请运行: pip install openai")
        return 1

    except Exception as e:
        err_str = str(e)
        print()
        print("❌ LLM 连通性检查失败！")
        print(f"   错误类型: {type(e).__name__}")
        print(f"   错误信息: {err_str[:300]}")
        print()

        # ── 针对性排查指引 ──
        if "401" in err_str or "unauthorized" in err_str.lower():
            print("🔧 排查: API Key 无效或已过期")
            print("   1. 检查 backend/.env 中 LLM_API_KEY 是否正确")
            print("   2. 登录控制台确认 Key 状态: https://platform.deepseek.com/api_keys")
        elif "403" in err_str or "forbidden" in err_str.lower():
            print("🔧 排查: 权限不足")
            print("   1. Key 可能没有聊天模型权限")
            print("   2. 检查账户余额是否充足")
            print(f"   3. 确认模型 {model} 在你的账户中可用")
        elif "timeout" in err_str.lower() or "timed out" in err_str.lower():
            print("🔧 排查: 网络超时")
            print(f"   1. 测试: curl -I {api_base}/models")
            print("   2. 如果你在中国大陆, 确保已配置代理:")
            print("      硅基流动 (免代理): https://api.siliconflow.cn/v1")
            print("      设置: LLM_API_BASE=https://api.siliconflow.cn/v1")
        elif "Connection" in err_str or "connect" in err_str.lower():
            print("🔧 排查: 网络不通")
            print(f"   1. ping {provider}")
            print("   2. 检查是否需要 VPN/代理访问外网")
            print("   3. 硅基流动/智谱等国内供应商通常无需代理")
        else:
            print("🔧 请检查网络连接和 API 配置。")
            print("   可尝试的替代方案:")
            print("   - 硅基流动: LLM_API_BASE=https://api.siliconflow.cn/v1")
            print("   - 智谱 AI:  LLM_API_BASE=https://open.bigmodel.cn/api/paas/v4")
            print("   - 本地 Ollama: LLM_API_BASE=http://localhost:11434/v1")

        return 1


if __name__ == "__main__":
    sys.exit(asyncio.run(check_llm()))

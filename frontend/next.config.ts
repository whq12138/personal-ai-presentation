import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // 将所有 /api/* 请求代理到 FastAPI 后端 (端口 8000)
  // 前端 fetch("/api/generate") → 后端 http://localhost:8000/generate
  // 前端 fetch("/api/export")  → 后端 http://localhost:8000/export
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${BACKEND_URL}/:path*`,
      },
    ];
  },
};

export default nextConfig;

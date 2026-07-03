import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  // Docker standalone output (required for production Dockerfile)
  output: "standalone",

  // 将所有 /api/* 请求代理到 FastAPI 后端
  // 本地开发: http://localhost:8000
  // Docker:     http://backend:8000 (容器间通信)
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

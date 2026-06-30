"use client";

import { useState, useRef, useCallback } from "react";
import { useAuth } from "@/lib/auth/AuthContext";

export type TaskStatus = "queued" | "processing" | "completed" | "failed";

export interface TaskProgress {
  taskId: string | null;
  status: TaskStatus;
  progress: number;
  message: string;
  error: string | null;
}

const POLL_INTERVAL_MS = 1500;

export function useTaskPolling() {
  const { getAccessToken, refreshAccessToken, logout } = useAuth();
  const [taskProgress, setTaskProgress] = useState<TaskProgress>({
    taskId: null,
    status: "queued",
    progress: 0,
    message: "",
    error: null,
  });
  const pollingRef = useRef<ReturnType<typeof setInterval> | null>(null);

  /**
   * 统一鉴权 fetch — 通过 Next.js rewrites 代理到后端。
   * path 格式: "/generate", "/export", "/auth/login" 等
   * 被 next.config.ts rewrites 映射: /api/* → http://localhost:8000/*
   * 发送时加 /api 前缀。
   */
  const authFetch = useCallback(
    async (path: string, options: RequestInit = {}): Promise<Response> => {
      const token = getAccessToken();
      const headers: Record<string, string> = {};

      // 不上 Content-Type 让浏览器自动设 + boundary (multipart 兼容)
      if (!(options.body instanceof FormData)) {
        headers["Content-Type"] = "application/json";
      }
      if (token) headers["Authorization"] = `Bearer ${token}`;

      const fetchOptions: RequestInit = {
        ...options,
        headers: { ...headers, ...((options.headers as Record<string, string>) || {}) },
      };

      let res = await fetch(`/api${path}`, fetchOptions);

      if (res.status === 401) {
        const newToken = await refreshAccessToken();
        if (newToken) {
          headers["Authorization"] = `Bearer ${newToken}`;
          fetchOptions.headers = { ...headers, ...((options.headers as Record<string, string>) || {}) };
          res = await fetch(`/api${path}`, fetchOptions);
        } else {
          logout();
          throw new Error("Session expired");
        }
      }
      return res;
    },
    [getAccessToken, refreshAccessToken, logout],
  );

  const startPolling = useCallback(
    (taskId: string, onComplete: (result: any) => void, onError?: (err: string) => void) => {
      setTaskProgress({
        taskId,
        status: "queued",
        progress: 0,
        message: "Queued...",
        error: null,
      });

      pollingRef.current = setInterval(async () => {
        try {
          const res = await authFetch(`/generate/task/${taskId}`);
          if (!res.ok) throw new Error("Poll failed");

          const data = await res.json();
          setTaskProgress({
            taskId,
            status: data.status as TaskStatus,
            progress: data.progress || 0,
            message: data.progress_message || "",
            error: data.error || null,
          });

          if (data.status === "completed") {
            clearInterval(pollingRef.current!);
            pollingRef.current = null;

            const resultRes = await authFetch(`/generate/task/${taskId}/result`);
            const result = await resultRes.json();
            onComplete(result);
          }

          if (data.status === "failed") {
            clearInterval(pollingRef.current!);
            pollingRef.current = null;
            onError?.(data.error || "Task failed");
          }
        } catch (err: any) {
          clearInterval(pollingRef.current!);
          pollingRef.current = null;
          setTaskProgress((prev) => ({ ...prev, status: "failed", error: err.message }));
          onError?.(err.message);
        }
      }, POLL_INTERVAL_MS);
    },
    [authFetch],
  );

  const cancelPolling = useCallback(() => {
    if (pollingRef.current) {
      clearInterval(pollingRef.current);
      pollingRef.current = null;
    }
    setTaskProgress({
      taskId: null,
      status: "queued",
      progress: 0,
      message: "",
      error: null,
    });
  }, []);

  return { taskProgress, startPolling, cancelPolling, authFetch };
}

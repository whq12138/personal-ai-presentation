# ============================================================
# Personal AI Presentation — Frontend Production Dockerfile
# Next.js 14 multi-stage build for minimal image size
# ============================================================

# ═══ Stage 1: Dependencies ═══
FROM node:23-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package.json pnpm-lock.yaml* ./
RUN corepack enable pnpm && pnpm install --frozen-lockfile --prod


# ═══ Stage 2: Build ═══
FROM node:23-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# 禁用 Next.js telemetry
ENV NEXT_TELEMETRY_DISABLED=1

RUN corepack enable pnpm && pnpm build


# ═══ Stage 3: Runner ═══
FROM node:23-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# 非 root
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# 复制必要输出
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["node", "server.js"]

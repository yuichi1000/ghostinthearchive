# Build stage
# ビルドコンテキスト: monorepo ルート（docker build -f web-admin/Dockerfile .）
FROM node:20-alpine AS builder

WORKDIR /app

# ワークスペースの package.json をコピー（依存解決用）
COPY package.json package-lock.json ./
COPY packages/shared/package.json ./packages/shared/
COPY web-admin/package.json ./web-admin/
COPY web-public/package.json ./web-public/

# 依存インストール（workspaces で @ghost/shared をローカル解決）
RUN npm ci

# ソースコードをコピーしてビルド
COPY packages/shared/ ./packages/shared/
COPY web-admin/ ./web-admin/

WORKDIR /app/web-admin
RUN mkdir -p public
RUN npm run build

# Production stage
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=8080

# Create non-root user
RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# standalone 出力をコピー（monorepo 構造が再現される）
COPY --from=builder /app/web-admin/public ./web-admin/public
COPY --from=builder --chown=nextjs:nodejs /app/web-admin/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/web-admin/.next/static ./web-admin/.next/static

USER nextjs

EXPOSE 8080

CMD ["node", "web-admin/server.js"]

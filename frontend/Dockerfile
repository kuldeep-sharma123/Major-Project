# ============================================================
# Stage 1: deps — install node_modules with cache-friendly layer
# ============================================================
FROM node:18-alpine AS deps

# Check https://github.com/nodejs/docker-node/tree/b4117f9333da4138b03a546ec926ef50a31506c3#nodealpine
# for why libc6-compat is needed
RUN apk add --no-cache libc6-compat

WORKDIR /app

# Copy package manifests only — install before copying source
# so npm install layer is cached unless deps change
COPY package.json package-lock.json* ./

RUN npm ci --only=production

# ============================================================
# Stage 2: builder — compile Next.js app
# ============================================================
FROM node:18-alpine AS builder

WORKDIR /app

# Copy all node_modules from deps stage
COPY --from=deps /app/node_modules ./node_modules

# Copy full source code
COPY . .

# Build-time env vars injected at compile time
# NEXT_PUBLIC_ vars are baked into the bundle; set at build time via --build-arg
ARG NEXT_PUBLIC_API_URL=http://localhost/api
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

# Disable Next.js telemetry in CI / Docker builds
ENV NEXT_TELEMETRY_DISABLED=1

# Build the standalone output bundle (needed for the slim runner stage)
RUN npm run build

# ============================================================
# Stage 3: runner — minimal production image
# ============================================================
FROM node:18-alpine AS runner

LABEL maintainer="AI Testing Agent Team" \
      version="1.0.0" \
      description="AI Autonomous Testing Agent – Next.js Frontend"

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

# Create non-root user
RUN addgroup --system --gid 1001 nodejs && \
    adduser  --system --uid 1001 nextjs

# Copy public assets
COPY --from=builder /app/public ./public

# Copy prebuilt standalone output — this includes all required Node modules
# (requires `output: 'standalone'` in next.config.js)
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Health check against Next.js health route or root
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD wget -qO- http://localhost:3000/ || exit 1

# server.js is produced by `output: standalone` and is the minimal entrypoint
CMD ["node", "server.js"]

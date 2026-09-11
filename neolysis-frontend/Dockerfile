# ============================================
# Stage 1: Build Rust/WASM MD Engine
# ============================================
FROM rust:1.82-slim AS wasm-builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

RUN rustup target add wasm32-unknown-unknown

WORKDIR /engine
COPY neolysis-md-engine/ .

RUN cargo install wasm-pack
RUN wasm-pack build --target web --release

# ============================================
# Stage 2: Build Next.js frontend
# ============================================
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files first for better caching
COPY neolysis-frontend/package.json neolysis-frontend/package-lock.json* ./

# Copy the WASM engine package from stage 1
COPY --from=wasm-builder /engine/pkg ../neolysis-md-engine/pkg

# Install dependencies
RUN npm ci || npm install

# Copy frontend source code
COPY neolysis-frontend/ .

# Set env for build
ENV NEXT_TELEMETRY_DISABLED=1
ENV NODE_ENV=production

# Build the application
RUN npm run build

# ============================================
# Stage 3: Production image
# ============================================
FROM node:20-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

# Copy public assets
COPY --from=builder /app/public ./public

# Copy .next standalone output
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

# Copy WASM file for direct serving
COPY --from=wasm-builder /engine/pkg/neolysis_md_engine_bg.wasm ./public/wasm/

USER nextjs

EXPOSE 3001
ENV PORT=3001
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]

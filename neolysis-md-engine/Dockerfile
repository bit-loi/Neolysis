# ============================================
# Neolysis MD Engine — Rust/WASM Build
# ============================================
# Multi-stage build: compile Rust to WASM, export pkg/ directory
# Usage: docker build -t neolysis-md-engine .
# The output pkg/ directory can be consumed by the frontend.

FROM rust:1.82-slim AS builder

RUN apt-get update && apt-get install -y --no-install-recommends \
    pkg-config \
    libssl-dev \
    && rm -rf /var/lib/apt/lists/*

# Add WASM target
RUN rustup target add wasm32-unknown-unknown

# Install wasm-pack
RUN cargo install wasm-pack

WORKDIR /engine

# Copy manifests first for better caching
COPY Cargo.toml Cargo.lock ./

# Create dummy src to cache dependency builds
RUN mkdir src && echo 'fn main() {}' > src/main.rs
RUN mkdir tests && echo '' > tests/web.rs

# Build dependencies (cached layer)
RUN wasm-pack build --target web --release || true

# Remove dummy src
RUN rm -rf src tests

# Copy real source code
COPY src/ src/

# Build the actual WASM package
RUN wasm-pack build --target web --release

# ============================================
# Stage 2: Export the built package
# ============================================
FROM alpine:3.19 AS output

COPY --from=builder /engine/pkg/ /pkg/

# Default command: just copy the output (used by docker cp or volume mount)
CMD ["cp", "-r", "/pkg/.", "/output/"]

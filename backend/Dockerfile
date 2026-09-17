# ==============================================================================
# Multi-Stage Production Dockerfile for Express.js Backend
# Base image: node:20.17.0-alpine (explicit version tag pinned)
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Dependencies Builder
# ------------------------------------------------------------------------------
FROM node:20.17.0-alpine AS builder

WORKDIR /app

# Copy package definition files
COPY package*.json ./

# Install production dependencies only (clean install from package-lock.json)
RUN npm ci --omit=dev && npm cache clean --force

# ------------------------------------------------------------------------------
# Stage 2: Minimal Production Runtime
# ------------------------------------------------------------------------------
FROM node:20.17.0-alpine AS runtime

WORKDIR /app

# Security hardening: Create non-root system group and user
RUN addgroup -g 1001 -S appgroup && \
    adduser -u 1001 -S appuser -G appgroup

# Document environment variables with defaults (actual secrets sourced at runtime)
ENV NODE_ENV=production \
    PORT=5000 \
    MONGO_URI="" \
    JWT_SECRET=""

# Copy production node_modules from builder stage with correct ownership
COPY --from=builder --chown=appuser:appgroup /app/node_modules ./node_modules

# Copy application source code with non-root ownership
COPY --chown=appuser:appgroup . .

# Switch to non-root user
USER appuser

# Expose backend port
EXPOSE 5000

# Health check instruction calling /health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -qO- http://localhost:5000/health || exit 1

# Start production server
CMD ["node", "index.js"]

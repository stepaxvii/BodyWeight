FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Production image
FROM node:20-alpine

WORKDIR /app

# Copy built files
COPY --from=builder /app/build ./build
COPY --from=builder /app/package*.json ./

# Install only production dependencies for serving
RUN npm ci --omit=dev

# Install a simple static server
RUN npm install -g sirv-cli

EXPOSE 3000

# Serve the static files
CMD ["sirv", "build", "--host", "0.0.0.0", "--port", "3000", "--single"]

# Builds the SvelteKit mini-app inside Docker so the host needs no Node.
# base=/bodyweight is baked in via svelte.config.js. The built SPA is copied to
# a mounted /out directory at run time:
#   docker build -t bw-frontend-build frontend/mini-app
#   docker run --rm -v "$PWD/backend/static:/out" bw-frontend-build
FROM node:20-alpine
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci || npm install
COPY . .
RUN npm run build
CMD ["sh", "-c", "rm -rf /out/* 2>/dev/null; cp -r build/. /out/ && echo 'SPA -> /out'"]

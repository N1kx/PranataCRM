# Stage 1: build
FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

ARG NUXT_PUBLIC_API_BASE=http://localhost:8230/api/v1
ARG NUXT_PUBLIC_APP_ENV=production

ENV NUXT_PUBLIC_API_BASE=$NUXT_PUBLIC_API_BASE
ENV NUXT_PUBLIC_APP_ENV=$NUXT_PUBLIC_APP_ENV

RUN npm run build

# Stage 2: run
FROM node:22-alpine AS runner

WORKDIR /app

ENV NODE_ENV=production

COPY --from=builder /app/.output ./.output

EXPOSE 3000

CMD ["node", ".output/server/index.mjs"]

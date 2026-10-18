# Build context is the repo root (docker-compose.yml) so ops/nginx/web.conf is reachable.
FROM node:20-alpine AS build
WORKDIR /w
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY apps/web/ ./
RUN npm run build

FROM nginx:1.27-alpine
COPY ops/nginx/web.conf /etc/nginx/conf.d/default.conf
COPY --from=build /w/dist /usr/share/nginx/html

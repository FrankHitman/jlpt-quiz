FROM node:24-alpine AS build

ARG VITE_API_BASE=http://localhost:8000/api

WORKDIR /app
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci --no-audit --no-fund

COPY frontend/ ./
RUN VITE_USE_MOCK=false VITE_API_BASE=${VITE_API_BASE} npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80

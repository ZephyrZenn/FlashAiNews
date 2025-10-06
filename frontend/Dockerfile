# syntax=docker/dockerfile:1.7

FROM node:20-slim AS frontend-base
WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install --frozen-lockfile || npm install

COPY . .
RUN npm run build

FROM nginx:1.27-alpine AS frontend-runtime
RUN apk add --no-cache gettext
ENV BACKEND_URL=http://backend:8000
COPY --from=frontend-base /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY docker-entrypoint.d/ /docker-entrypoint.d/
RUN chmod +x /docker-entrypoint.d/*.sh
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]

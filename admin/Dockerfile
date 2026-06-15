FROM node:22-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

FROM nginx:1.27-alpine

ENV API_URL=https://flashcards-stagging-d9c092f5d04d.herokuapp.com \
    APP_ENV=STAGING \
    PORT=8080

COPY --from=builder /app/dist /usr/share/nginx/html
COPY deploy/default.conf.template /etc/nginx/templates/default.conf.template
COPY deploy/config.template.js /etc/nginx/templates/config.template.js
COPY deploy/40-runtime-config.sh /docker-entrypoint.d/40-runtime-config.sh

RUN chmod +x /docker-entrypoint.d/40-runtime-config.sh

EXPOSE 8080

# Frontend (React/Vite) production image.
#
# Multi-stage build:
#   1. Build the static application bundle using Node.js.
#   2. Serve the generated assets using Nginx.
#
# This approach avoids shipping the Node.js runtime in production,
# resulting in a smaller, more secure final image.
#
# To build directly from the frontend directory:
#   docker build -t entrepreneur-dashboard \
#     --build-arg VITE_API_BASE_URL=https://api.example.com .
#
# In normal usage, the image is built through the root-level
# docker-compose.yml configuration.

FROM node:20-slim AS build

WORKDIR /app

COPY package.json package-lock.json* ./

# Disable strict SSL validation as a workaround for environments that
# perform TLS inspection through a corporate proxy.
#
# This addresses the same certificate validation issue handled in the
# backend Dockerfile. While acceptable for local development and testing,
# the preferred solution is to install and trust the organization's root
# certificate authority rather than bypassing SSL verification.
RUN npm config set strict-ssl false && npm ci

COPY . .

# Vite embeds all VITE_* variables into the application bundle during
# the build process, not when the container starts.
#
# Because of this, the API base URL must be supplied as a build argument.
# If omitted, the frontend falls back to the default value configured in
# client.js for local development.

ARG VITE_API_BASE_URL=http://localhost:8000
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL

RUN npm run build

FROM nginx:1.27-alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD wget -q --spider http://localhost:80 || exit 1

CMD ["nginx", "-g", "daemon off;"]
ARG WEKAN_BASE=ghcr.io/wekan/wekan@sha256:818e36c01d695596e94718fc00884a38bf5562f7c63a36192a70a17d7a4b0c5a
FROM node:24.20.0-bookworm-slim AS dependencies
WORKDIR /opt/pearnly
COPY package.json package-lock.json ./
RUN npm ci --ignore-scripts --no-audit --no-fund
FROM ${WEKAN_BASE}
USER root
COPY --from=dependencies /opt/pearnly /opt/pearnly
COPY install.mjs /opt/pearnly/
COPY meteor-bridge.js /build/programs/server/packages/pearnly-bridge.js
RUN node /opt/pearnly/install.mjs /build/programs/server
COPY cookies.mjs gateway.mjs client.js /opt/pearnly/
USER wekan

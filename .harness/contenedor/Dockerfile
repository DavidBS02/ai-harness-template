# Imagen del ejecutor (OpenCode) aislado: solo ve el repo montado. La construye scripts/ejec-contenedor.
FROM node:22-bookworm
ARG OPENCODE_VERSION=latest
RUN apt-get update \
 && apt-get install -y --no-install-recommends git gh python3 ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && npm i -g "opencode-ai@${OPENCODE_VERSION}" \
 && git config --system --add safe.directory '*'
ENV HARNESS_ROL=ejecutor
CMD ["opencode"]

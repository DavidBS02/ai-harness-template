# Imagen del ejecutor (OpenCode) aislado. La construye scripts/ejec-contenedor con las versiones de .harness/versiones.json.
# Sin valores por defecto a propósito: una build sin versión fijada falla (reproducibilidad).
ARG IMAGEN_BASE
FROM ${IMAGEN_BASE}
ARG OPENCODE_VERSION
RUN test -n "${OPENCODE_VERSION}" || (echo "OPENCODE_VERSION requerido (.harness/versiones.json)" && exit 1) \
 && apt-get update \
 && apt-get install -y --no-install-recommends git gh python3 ca-certificates \
 && rm -rf /var/lib/apt/lists/* \
 && npm i -g "opencode-ai@${OPENCODE_VERSION}" \
 && git config --system --add safe.directory '*'
ENV HARNESS_ROL=ejecutor
CMD ["opencode"]

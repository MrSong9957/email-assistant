FROM s7620605/dev-base:latest

ARG HTTP_PROXY
ARG HTTPS_PROXY

USER root
RUN if [ -n "$HTTP_PROXY" ]; then echo "proxy=${HTTP_PROXY}" >> /home/app/.npmrc; fi && \
    if [ -n "$HTTPS_PROXY" ]; then echo "https-proxy=${HTTPS_PROXY}" >> /home/app/.npmrc; fi && \
    chown app:app /home/app/.npmrc

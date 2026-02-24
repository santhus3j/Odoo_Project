FROM odoo:18

USER root
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    fonts-urw-base35 \
    fonts-liberation \
    fonts-dejavu \
 && rm -rf /var/lib/apt/lists/*

USER odoo

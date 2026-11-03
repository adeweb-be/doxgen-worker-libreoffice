FROM debian:trixie-slim
ENV TZ=Europe/Brussels
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# LibreOffice comes from trixie-backports to get the newest release branch.
RUN echo "deb http://deb.debian.org/debian trixie-backports main contrib" > /etc/apt/sources.list.d/backports.list \
    && apt-get update -qqy \
    && apt-get install -qqy --no-install-recommends curl python3 python3-venv fontconfig \
    && apt-get install -qqy --no-install-recommends -t trixie-backports \
        python3-uno \
        libreoffice-writer \
        libreoffice-calc \
    && apt-get install -qqy --no-install-recommends \
        fonts-crosextra-carlito \
        fonts-crosextra-caladea \
        fonts-dejavu \
        fonts-liberation \
        fonts-liberation2 \
        fonts-linuxlibertine \
        fonts-roboto \
        fonts-sil-gentium-basic \
    && fc-cache -f \
    && rm -rf /var/lib/apt/lists/*

# The venv sees system packages so that "import uno" works in-process.
COPY ./requirements.txt ./
RUN python3 -m venv --system-site-packages /opt/venv \
    && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt
ENV PATH="/opt/venv/bin:$PATH"

# Compose runs the container with the host UID, which has no home directory.
ENV HOME=/tmp

VOLUME /storage
WORKDIR /srv

COPY . .

ADD entrypoint.sh /
RUN ["chmod", "+x", "/entrypoint.sh"]

ENV GENERATION_TIMEOUT=120
EXPOSE 5000
HEALTHCHECK --interval=5s --timeout=10s --retries=3 CMD curl -sS --fail 127.0.0.1:5000/healthcheck || exit 1
ENTRYPOINT ["/entrypoint.sh"]

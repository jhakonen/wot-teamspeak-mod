FROM ubuntu:bionic
RUN apt-get update \
    && apt-get install -y \
        ca-certificates \
        curl \
        ffmpeg \
        gnupg \
        libarchive-tools \
        libopus-dev \
    && apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys 3FA7E0328081BFF6A14DA29AA6A19B38D3D831EF \
    && echo "deb https://download.mono-project.com/repo/ubuntu stable-bionic main" | tee /etc/apt/sources.list.d/mono-official-stable.list \
    && apt-get update \
    && apt-get install -y mono-devel \
    && rm -rf /var/lib/apt/lists/*
# Download the bot
RUN mkdir /opt/bot/ \
    && curl https://splamy.de/api/nightly/ts3ab/develop/download | bsdtar -xvf- -C /opt/bot
# Configure it
RUN mkdir /app
COPY rights.toml /app/rights.toml
COPY ts3audiobot.toml /app/ts3audiobot.toml
COPY bots /app/bots
WORKDIR /app/
VOLUME /app/
CMD ["mono", "/opt/bot/TS3AudioBot.exe", "--non-interactive"]

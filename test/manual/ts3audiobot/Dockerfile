FROM ubuntu:bionic
RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y \
        ca-certificates \
        curl \
        ffmpeg \
        gnupg \
        libarchive-tools \
        libopus-dev \
        wget \
    && wget \
        https://packages.microsoft.com/config/ubuntu/18.04/packages-microsoft-prod.deb \
        -O packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && apt-get update \
    && apt-get install -y dotnet-runtime-2.2 \
    && rm -rf /var/lib/apt/lists/*
# Download the bot
RUN mkdir /opt/bot/ \
    && curl https://splamy.de/api/nightly/ts3ab/master_dotnet_core/download | bsdtar -xvf- -C /opt/bot
# Configure it
RUN mkdir /app
COPY rights.toml /app/rights.toml
COPY ts3audiobot.toml /app/ts3audiobot.toml
COPY bots /app/bots
WORKDIR /app/
VOLUME /app/
CMD ["dotnet", "/opt/bot/TS3AudioBot.dll", "--non-interactive"]

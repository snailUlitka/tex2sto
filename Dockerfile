ARG TEXLIVE_IMAGE=texlive/texlive@sha256:b4a9b20b4bac833fc4682a97313aeacc9a21ca00872e003546712039c81926cc
FROM ghcr.io/astral-sh/uv:0.12.8 AS uv
FROM ${TEXLIVE_IMAGE}

ARG TARGETARCH
ARG PANDOC_VERSION=3.11

USER root
RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
      ca-certificates curl fontconfig fonts-liberation python3 \
    && rm -rf /var/lib/apt/lists/*

RUN case "${TARGETARCH}" in \
      amd64) \
        pandoc_arch=amd64; \
        pandoc_sha=37edb3bbcf722f921a009941bf5874e2e0c09263226c9b4a2d980788cb062ab6 \
        ;; \
      arm64) \
        pandoc_arch=arm64; \
        pandoc_sha=56ed5566ec41d22ec9ee0704e6ac0b98ba102e92384efd5306173a22d314c79a \
        ;; \
      *) echo "unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac \
    && curl --fail --location --silent --show-error \
      "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-linux-${pandoc_arch}.tar.gz" \
      --output /tmp/pandoc.tar.gz \
    && echo "${pandoc_sha}  /tmp/pandoc.tar.gz" | sha256sum --check --status \
    && tar --extract --gzip --file /tmp/pandoc.tar.gz --directory /tmp \
    && install "/tmp/pandoc-${PANDOC_VERSION}/bin/pandoc" /usr/local/bin/pandoc \
    && rm -rf /tmp/pandoc.tar.gz "/tmp/pandoc-${PANDOC_VERSION}"

COPY --from=uv /uv /uvx /usr/local/bin/

WORKDIR /app
COPY .python-version pyproject.toml uv.lock README.md LICENSE ./
RUN uv python install 3.12.11 \
    && uv sync --frozen --no-dev --no-install-project \
    && fc-match --format='%{family}\n' 'Liberation Serif' | grep --fixed-strings "Liberation Serif" \
    && pandoc --version | head -n 1 | grep --fixed-strings "pandoc 3.11" \
    && tlmgr --version | grep --fixed-strings "version 2026"
COPY src/ ./src/
RUN uv sync --frozen --no-dev

WORKDIR /work
ENTRYPOINT ["/app/.venv/bin/tex2sto"]

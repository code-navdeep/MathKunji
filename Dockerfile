# MathKunji - Mathematical Solver
# Docker image for running the Gradio app

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for matplotlib
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better layer caching).
#
# requirements.lock is generated from requirements.txt with hashes, and
# --require-hashes makes pip verify every downloaded file against the SHA-256
# recorded there. A version pin alone says "gradio 4.44.1" and trusts PyPI to
# serve the same artifact under that name; the hash says which exact bytes, and
# the install aborts rather than proceeding if they differ.
#
# The lock is resolved on Python 3.11, so the audioop-lts entry -- which
# requirements.txt carries behind a `python_version >= "3.13"` marker -- is
# absent by design. This image is 3.11 and never needs it. That backport only
# matters outside Docker on 3.13+, where PEP 594 removed the stdlib audioop
# module Gradio reaches through pydub.
COPY requirements.lock .

# Install Python dependencies
RUN pip install --require-hashes -r requirements.lock

# Gradio's own frontend template hardcodes two preconnects to Google's font
# hosts and an iframe-resizer script from cdnjs. Neither is needed here -- the
# app bundles its typefaces and is never embedded in an iframe -- and all three
# would contact a third party on every page load, breaking the guarantee that
# this app makes no network requests. Must run as root, before USER below,
# because it edits site-packages.
#
# Gradio is pinned, so the template cannot change underneath a build. The
# script's loud failure matters on the day someone raises that pin: it stops
# the build rather than quietly shipping the requests again.
COPY scripts/strip_external_requests.py /tmp/
RUN python /tmp/strip_external_requests.py && rm /tmp/strip_external_requests.py

# Copy application code
COPY app.py .
COPY core/ core/
COPY utils/ utils/

# The bundled typefaces. app.py reads these at import time and inlines them
# into the stylesheet, so the app never requests a font over the network --
# without this COPY the container dies at startup with FileNotFoundError.
COPY assets/ assets/

# Run as an unprivileged user rather than root. This app parses untrusted
# mathematical input and has already had one RCE; if another parser bug ever
# lands, root inside the namespace is a materially worse starting position than
# a user that owns nothing.
#
# --create-home is load-bearing: matplotlib writes a font cache under $HOME on
# first use, and would fail on a home directory it cannot write to.
RUN useradd --create-home --uid 10001 mathkunji \
    && chown -R mathkunji:mathkunji /app
USER mathkunji

# Expose Gradio default port
EXPOSE 7860

# Set environment variables for Gradio
ENV GRADIO_SERVER_NAME="0.0.0.0"
ENV GRADIO_SERVER_PORT="7860"

# Gradio's analytics are on by default and reach out to api.gradio.app, plus
# api.ipify.org and checkip.amazonaws.com -- the last two exist purely to
# discover the host's public IP. MathKunji is a local-only tool; it has no business
# making outbound calls to anyone.
ENV GRADIO_ANALYTICS_ENABLED="False"

# Don't buffer stdout/stderr. The container runs unattended under
# `restart: unless-stopped`, and utils/timeout.py now runs computations in
# worker processes that report failures as text. With Python's default block
# buffering that output can sit unflushed indefinitely and never reach
# `docker logs`, which is exactly when you need it.
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "app.py"]

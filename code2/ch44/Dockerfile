# Book 1, Chapter 44: package the API service (serve_proxy.py) as a container image.
# Not built on the author's laptop (no Docker there). Build and run with:
#   docker build -t ai-gateway:1.0 .
#   docker run -p 8790:8790 -e ENGINE_URL=http://host.docker.internal:11434/api/chat ai-gateway:1.0
FROM python:3.12-slim

# a non-root user: if the service is ever compromised, it can't own the container
RUN useradd --create-home app
WORKDIR /home/app
COPY serve_proxy.py .
USER app

EXPOSE 8790
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8790/healthz')"
CMD ["python", "serve_proxy.py", "--serve"]

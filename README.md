# OpenHeart Protocol Docker Image

[OpenHeart protocol](https://github.com/dddddddddzzzz/OpenHeart) minimal Docker Image.

## Image Source

### pre-build

- `ghcr.io/yozlog/openheart:latest`
- Override with `OPENHEART_IMAGE` if your tag is different

### local build

```bash
docker build -t openheart-protocol .
```

## Run

```bash
docker run --rm -p 8080:8080 -v "$(pwd)/data:/data" openheart-protocol
```

## Docker Compose

```yaml
services:
  openheart:
    image: ${OPENHEART_IMAGE:-ghcr.io/yozlog/openheart:latest}
    # build:
    #   context: .
    #   dockerfile: Dockerfile
    ports:
      - "8080:8080"
    volumes:
      - data:/data
    restart: unless-stopped

volumes:
  data:
```

Run:

```bash
docker compose up -d
```

## Endpoints

- `GET /` returns a tiny test page.
- `GET /anything` returns reaction counts as JSON.
- `POST /anything` records a reaction.

## Notes

- Data persists in `/data/openheart.db`.
- The server listens on `0.0.0.0:8080` by default.
- Set `OPENHEART_ALLOWED_DOMAINS=example.com,foo.com` to allow browser requests only from those domains and their subdomains.
- Data is keyed by `host + path`, so different domains using the same path keep separate counts.
- Front-end usage reference: [open-heart-element](https://github.com/dddddddddzzzz/open-heart-element).

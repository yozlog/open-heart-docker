# OpenHeart Protocol Docker 이미지

[OpenHeart protocol](https://github.com/dddddddddzzzz/OpenHeart) 간단 Docker Image.

## 이미지 소스

### pre-build

- `ghcr.io/yozlog/openheart:latest`
- 태그가 다르면 `OPENHEART_IMAGE` 로 변경하세요

### 로컬 build

```bash
docker build -t openheart-protocol .
```

## 실행

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
    environment:
      OPENHEART_ALLOWED_ORIGINS: ${OPENHEART_ALLOWED_ORIGINS:-https://your.website.com,https://your.website2.com}
    ports:
      - "8080:8080"
    volumes:
      - data:/data
    restart: unless-stopped

volumes:
  data:
```

실행:

```bash
docker compose up -d
```

개발 중 로컬 Hugo 미리보기를 허용하려면:

```bash
OPENHEART_ALLOWED_ORIGINS=http://localhost:1313 docker compose up -d
```

## 엔드포인트

- `GET /` 는 간단한 테스트 페이지를 반환합니다.
- `GET /anything` 은 반응 수를 JSON으로 반환합니다.
- `POST /anything` 은 반응을 기록합니다.

## 참고

- 데이터는 `/data/openheart.db` 에 저장됩니다.
- 서버는 기본적으로 `0.0.0.0:8080` 에서 실행됩니다.
- `OPENHEART_ALLOWED_DOMAINS=example.com,foo.com` 로 설정하면 해당 도메인과 하위 도메인에서 온 브라우저 요청만 허용합니다.
- `OPENHEART_ALLOWED_ORIGINS=https://site-a.com,https://site-b.com` 로 설정하면 정확히 일치하는 origin의 브라우저 CORS 요청을 허용합니다.
- 데이터는 `host + path` 기준으로 분리되어, 같은 경로를 써도 도메인이 다르면 각각 따로 집계됩니다.
- 프런트엔드 사용 예시는 [open-heart-element](https://github.com/dddddddddzzzz/open-heart-element)를 참고하세요.

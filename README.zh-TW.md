# OpenHeart Protocol Docker 映像

[OpenHeart protocol](https://github.com/dddddddddzzzz/OpenHeart) 簡易 Docker Image。

## 映像來源

### pre-build

- `ghcr.io/yozlog/openheart:latest`
- 如果你的 tag 不同，用 `OPENHEART_IMAGE` 覆蓋

### 本地 build

```bash
docker build -t openheart-protocol .
```

## 執行

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

啟動：

```bash
docker compose up -d
```

開發時若要允許本機 Hugo 預覽：

```bash
OPENHEART_ALLOWED_ORIGINS=http://localhost:1313 docker compose up -d
```

## 端點

- `GET /` 會回傳一個簡單的測試頁。
- `GET /anything` 會回傳反應計數的 JSON。
- `POST /anything` 會記錄一次反應。

## 備註

- 資料會持久化到 `/data/openheart.db`。
- 伺服器預設監聽 `0.0.0.0:8080`。
- 設定 `OPENHEART_ALLOWED_DOMAINS=example.com,foo.com` 後，只允許來自這些網域與其子網域的瀏覽器請求。
- 設定 `OPENHEART_ALLOWED_ORIGINS=https://site-a.com,https://site-b.com` 後，會允許完全符合的 origin 發出的瀏覽器 CORS 請求。
- 資料會以 `host + path` 分開，因此不同網域使用同一路徑時會各自計數。
- 前端寫法可參考 [open-heart-element](https://github.com/dddddddddzzzz/open-heart-element)。

# Plugin Service

Plugin Service được thiết kế để cho các website khác tích hợp giao diện chat của hệ thống bằng cách gọi các API của Plugin-service.

## Mục tiêu
- Cung cấp widget chat embeddable cho các website đối tác.
- Cho phép đối tác đăng ký và nhận API key.
- Định tuyến mọi câu hỏi tới endpoint `/api/chat` của Plugin-service.
- Cung cấp cấu hình plugin qua `/plugin/register` và `/plugin/config`.

## Endpoint chính

### `GET /health`
- Mục đích: kiểm tra plugin service đang chạy.
- Response 200:
```json
{
  "status": "ok",
  "timestamp": "2026-04-20T12:34:56.789Z"
}
```

### `GET /plugin/info`
- Mục đích: trả metadata của plugin service.
- Response 200:
```json
{
  "name": "AI Chat Plugin Service",
  "version": "1.0.0",
  "baseUrl": "http://localhost:8000",
  "docs": "http://localhost:8000/plugin",
  "description": "Service cung cap giao dien chat embeddable va API chat cho cac website doi tac."
}
```

### `POST /plugin/register`
- Mục đích: cho phép website đối tác đăng ký plugin và nhận API key.
- Body:
```json
{
  "origin": "http://localhost:3000",
  "siteName": "Acme Website",
  "theme": { "primary": "#0084ff", "accent": "#ffffff" }
}
```
- Response 2001:
```json
{
  "status": 2001,
  "success": true,
  "message": "Plugin registered successfully",
  "data": {
    "origin": "http://localhost:3000",
    "config": {
      "siteName": "Acme Website",
      "apiKey": "plugin_...",
      "theme": {
        "primary": "#0084ff",
        "accent": "#ffffff"
      },
      "registeredAt": "2026-04-20T12:34:56.789Z"
    },
    "widgetUrl": "http://localhost:8000/plugin/widget.js",
    "embedSnippet": "<script src=\"http://localhost:8000/plugin/widget.js\"></script>..."
  }
}
```

### `GET /plugin/config?origin=...`
- Mục đích: lấy cấu hình plugin cho origin đã đăng ký.
- Response 2001:
```json
{
  "status": 2001,
  "success": true,
  "message": "Plugin configuration retrieved",
  "data": {
    "origin": "http://localhost:3000",
    "config": {
      "siteName": "Acme Website",
      "apiKey": "plugin_...",
      "theme": { "primary": "#0084ff", "accent": "#ffffff" },
      "registeredAt": "..."
    },
    "widgetUrl": "http://localhost:8000/plugin/widget.js"
  }
}
```

### `POST /api/chat`
- Mục đích: endpoint chính nhận câu hỏi và trả lời chat.
- Headers:
  - `X-API-Key: <apiKey>`
- Body:
```json
{
  "question": "Xin chào, tôi muốn hỏi về hợp đồng?"
}
```
- Response 200:
```json
{
  "question": "Xin chào, tôi muốn hỏi về hợp đồng?",
  "answer": "[Bot]: Bạn vừa hỏi \"Xin chào, tôi muốn hỏi về hợp đồng?\". Đây là phản hồi từ Plugin-service tại http://localhost:8000.",
  "apiKey": "plugin_...",
  "requests": 1
}
```

### `POST /api/validate-key`
- Mục đích: kiểm tra API key hợp lệ.
- Headers:
  - `X-API-Key: <apiKey>`
- Response 2001:
```json
{
  "status": 2001,
  "success": true,
  "message": "API key is valid",
  "data": {
    "valid": true,
    "apiKey": "plugin_..."
  }
}
```

## Cách tích hợp với website đối tác
1. Đăng ký plugin từ website đối tác qua `POST /plugin/register`.
2. Nhận `apiKey` và `widgetUrl`.
3. Nhúng vào website:
```html
<script src="http://localhost:8000/plugin/widget.js"></script>
<script>
  AIChat.init({
    apiKey: 'plugin_...',
    baseUrl: 'http://localhost:8000',
    widgetTitle: 'Acme Chat'
  });
</script>
```
4. Widget sẽ tạo nút chat và mở giao diện chat từ Plugin-service.

## File có sẵn
- `server.js`: backend xử lý đăng ký plugin, xác thực API key và routing chat.
- `public/plugin.js`: script embeddable cho website đối tác.
- `public/chat.html`: giao diện chat được render trong iframe.

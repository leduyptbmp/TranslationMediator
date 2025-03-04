
# Telegram Translation Bot

## Cài đặt

1. Clone repository về máy của bạn:
```
git clone <repository-url>
```

2. Cài đặt các thư viện phụ thuộc:
```
pip install -r requirements.txt
```

3. Cấu hình file `.env` với token bot Telegram của bạn:
```
TELEGRAM_BOT_TOKEN=your-token-here
GOOGLE_TRANSLATE_API_KEY=your-api-key-here
```

4. Chạy bot:
```
python bot.py
```

## Cấu hình môi trường

Bot yêu cầu Python 3.11 trở lên và các thư viện được liệt kê trong `requirements.txt`.

## Triển khai

Khi triển khai lên môi trường khác, đảm bảo:
1. Tất cả các biến môi trường đã được cấu hình đúng trong file `.env`
2. Thư mục `logs` tồn tại hoặc được tạo tự động
3. Cổng 8080 được mở nếu bạn sử dụng keep_alive server

## Cấu trúc project
- `bot.py`: File chính để chạy bot
- `config.py`: Cấu hình bot
- `handlers.py`: Xử lý các lệnh từ Telegram
- `translator.py`: Module dịch thuật
- `storage.py`: Lưu trữ dữ liệu người dùng
- `utils.py`: Tiện ích và hàm hỗ trợ
- `keep_alive.py`: Giữ bot hoạt động liên tục


#!/bin/bash

# Tạo thư mục logs nếu chưa tồn tại
mkdir -p logs

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt

# Chạy bot
python bot.py

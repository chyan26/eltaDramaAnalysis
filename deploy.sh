#!/bin/bash
# 愛爾達收視分析系統部署腳本

echo "🚀 開始部署愛爾達收視分析系統..."

# 更新系統
sudo apt update && sudo apt upgrade -y

# 安裝Python和依賴
sudo apt install -y python3 python3-pip python3-venv nginx

# 創建虛擬環境
python3 -m venv elta_env
source elta_env/bin/activate

# 安裝Python套件
pip install -r requirements.txt

# 安裝process manager
sudo apt install -y supervisor

echo "✅ 基礎環境安裝完成"

# 創建Supervisor配置
sudo tee /etc/supervisor/conf.d/elta-streamlit.conf > /dev/null <<EOF
[program:elta-streamlit]
command=/home/$(whoami)/eltaDramaAnalysis/elta_env/bin/streamlit run recommend.py --server.port=8501 --server.address=0.0.0.0 --server.headless=true
directory=/home/$(whoami)/eltaDramaAnalysis
user=$(whoami)
autostart=true
autorestart=true
stderr_logfile=/var/log/elta-streamlit.err.log
stdout_logfile=/var/log/elta-streamlit.out.log
EOF

sudo tee /etc/supervisor/conf.d/elta-pipeline.conf > /dev/null <<EOF
[program:elta-pipeline]
command=/home/$(whoami)/eltaDramaAnalysis/elta_env/bin/python automated_pipeline.py
directory=/home/$(whoami)/eltaDramaAnalysis
user=$(whoami)
autostart=true
autorestart=true
stderr_logfile=/var/log/elta-pipeline.err.log
stdout_logfile=/var/log/elta-pipeline.out.log
EOF

# 重新加載Supervisor
sudo supervisorctl reread
sudo supervisorctl update

echo "✅ 應用服務配置完成"

# 配置Nginx反向代理
sudo tee /etc/nginx/sites-available/elta-analysis > /dev/null <<EOF
server {
    listen 80;
    server_name your-domain.com;  # 替換為您的域名

    # Streamlit應用
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 86400;
    }

    # 自動化儀表板
    location /dashboard {
        proxy_pass http://localhost:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# 啟用網站
sudo ln -sf /etc/nginx/sites-available/elta-analysis /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl restart nginx

# 啟動服務
sudo supervisorctl start elta-streamlit
sudo supervisorctl start elta-pipeline

echo "🎉 部署完成！"
echo "Streamlit應用: http://your-domain.com"
echo "儀表板: http://your-domain.com/dashboard"
echo ""
echo "管理命令:"
echo "sudo supervisorctl status"
echo "sudo supervisorctl restart elta-streamlit"
echo "sudo supervisorctl restart elta-pipeline"

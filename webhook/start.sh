#!/bin/bash
# 一键启动 webhook 服务 + 隧道 + 自动更新 GitHub webhook

cd "$(dirname "$0")/.."

echo "🚀 启动 GitHub Webhook 自动化系统..."
echo ""

# 1. 启动 Flask 服务
echo "📡 启动 Flask webhook 服务..."
pkill -f "webhook/server.py" 2>/dev/null
python3 webhook/server.py > /tmp/webhook.log 2>&1 &
sleep 3

if curl -s http://localhost:5000/health > /dev/null; then
    echo "✅ Flask 服务运行正常"
else
    echo "❌ Flask 服务启动失败"
    exit 1
fi

# 2. 启动 Cloudflare Tunnel
echo "📡 启动 Cloudflare Tunnel..."
pkill -f cloudflared 2>/dev/null
cloudflared tunnel --url http://localhost:5000 > /tmp/cloudflared.log 2>&1 &
sleep 5

# 3. 更新 GitHub Webhook
echo "📡 更新 GitHub webhook..."
./webhook/update_github_webhook.sh

echo ""
echo "✅ 系统启动完成！"
echo "   日志文件:"
echo "   - Flask: /tmp/webhook.log"
echo "   - Tunnel: /tmp/cloudflared.log"

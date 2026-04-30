#!/bin/bash
# 停止所有服务

echo "🛑 停止 GitHub Webhook 自动化系统..."
pkill -f "webhook/server.py" && echo "✅ Flask 服务已停止" || echo "⚠️  Flask 服务未运行"
pkill -f cloudflared && echo "✅ Cloudflare Tunnel 已停止" || echo "⚠️  Cloudflare Tunnel 未运行"
pkill -f "localhost.run" && echo "✅ localhost.run 已停止" || echo "⚠️  localhost.run 未运行"
echo "完成"

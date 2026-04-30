#!/bin/bash
# 多用户 webhook 启动脚本

set -e

# 默认值
TRIGGER_LABEL="${TRIGGER_LABEL:-claude}"
PORT="${PORT:-5000}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🚀 多用户 Webhook 启动工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "配置信息："
echo "  触发标签: $TRIGGER_LABEL"
echo "  监听端口: $PORT"
echo "  项目目录: $PROJECT_DIR"
echo "  仓库: ${REPO_OWNER:-dengzhh}/${REPO_NAME:-osenv}"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 停止旧服务
echo "🛑 停止旧服务..."
pkill -f "webhook/server.py" 2>/dev/null || true
pkill -f "cloudflared" 2>/dev/null || true
sleep 2
echo "✅ 旧服务已停止"
echo ""

# 2. 启动 Flask 服务
echo "📡 启动 Flask webhook 服务 (端口 $PORT)..."
cd "${PROJECT_DIR:-$(dirname "$0")}"
PORT=$PORT TRIGGER_LABEL=$TRIGGER_LABEL python3 webhook/server.py > /tmp/webhook.log 2>&1 &
sleep 3

if curl -s "http://localhost:$PORT/health" > /dev/null 2>&1; then
    echo "✅ Flask 服务运行正常"
else
    echo "❌ Flask 服务启动失败"
    cat /tmp/webhook.log
    exit 1
fi

# 3. 启动 Cloudflare Tunnel
echo "📡 启动 Cloudflare Tunnel..."
cloudflared tunnel --url "http://localhost:$PORT" > /tmp/cloudflared.log 2>&1 &
sleep 5

TUNNEL_URL=$(cat /tmp/cloudflared.log 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1)

if [ -n "$TUNNEL_URL" ]; then
    echo "✅ Tunnel 运行正常"
    echo "   URL: $TUNNEL_URL"
else
    echo "❌ Tunnel 启动失败"
    exit 1
fi

# 4. 更新 GitHub webhook
echo ""
echo "📡 更新 GitHub webhook..."
export TRIGGER_LABEL
export WEBHOOK_PORT=$PORT

# 创建临时更新脚本
cat > /tmp/update_webhook.sh << 'UPDATE_SCRIPT'
#!/bin/bash
TUNNEL_URL="$1"
OWNER=${REPO_OWNER:-dengzhh}
REPO=${REPO_NAME:-osenv}
LABEL=${TRIGGER_LABEL:-claude}
WEBHOOK_URL="$TUNNEL_URL/webhook"

echo "为 label '$LABEL' 配置 webhook..."

# 获取现有 webhooks
HOOKS=$(gh api /repos/$OWNER/$REPO/hooks 2>/dev/null)

# 查找是否有匹配的 webhook
EXISTING_ID=$(echo "$HOOKS" | python3 -c "
import json, sys
try:
    hooks = json.load(sys.stdin)
    label = '$LABEL'
    for h in hooks:
        url = h.get('config', {}).get('url', '')
        if 'trycloudflare' in url:
            print(h['id'])
            break
except:
    pass
" 2>/dev/null)

if [ -n "$EXISTING_ID" ]; then
    echo "更新现有 webhook (ID: $EXISTING_ID)..."
    gh api -X PATCH /repos/$OWNER/$REPO/hooks/$EXISTING_ID \
      -f config[url]="$WEBHOOK_URL" \
      -f config[content_type]="json" > /dev/null 2>&1
    echo "✅ Webhook 已更新"
else
    echo "创建新 webhook..."
    gh api /repos/$OWNER/$REPO/hooks \
      -f name=web \
      -f config[url]="$WEBHOOK_URL" \
      -f config[content_type]="json" \
      -f config[secret]="$WEBHOOK_SECRET" \
      -f events[0]=issues \
      -f events[1]=issue_comment \
      -f active=true > /dev/null 2>&1
    echo "✅ Webhook 已创建"
fi
UPDATE_SCRIPT

chmod +x /tmp/update_webhook.sh
/tmp/update_webhook.sh "$TUNNEL_URL"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 启动完成！"
echo ""
echo "📊 配置信息："
echo "  触发标签: $TRIGGER_LABEL"
echo "  Webhook URL: $TUNNEL_URL/webhook"
echo "  本地服务: http://localhost:$PORT"
echo ""
echo "🎮 测试方法："
echo "  gh issue create --repo $OWNER/$REPO --title '测试 $TRIGGER_LABEL' --body '测试' --label '$TRIGGER_LABEL'"
echo ""
echo "📝 日志："
echo "  Flask: /tmp/webhook.log"
echo "  Tunnel: /tmp/cloudflared.log"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

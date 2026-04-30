#!/bin/bash
# 自动更新 GitHub webhook URL 的脚本

# 检查参数
if [ -z "$GITHUB_PERSONAL_ACCESS_TOKEN" ]; then
    echo "❌ 错误: 请设置 GITHUB_PERSONAL_ACCESS_TOKEN 环境变量"
    echo "   在 ~/.bashrc 中添加: export GITHUB_PERSONAL_ACCESS_TOKEN=\"ghp_xxxx\""
    exit 1
fi

OWNER=${REPO_OWNER:-dengzhh}
REPO=${REPO_NAME:-osenv}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔄 GitHub Webhook URL 自动更新工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. 获取 cloudflared URL
echo "📡 步骤 1: 获取 Cloudflare Tunnel URL..."
sleep 3  # 等待 tunnel 启动

TUNNEL_URL=$(cat /tmp/cloudflared.log 2>/dev/null | grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' | head -1)

if [ -z "$TUNNEL_URL" ]; then
    echo "❌ 错误: 无法获取 tunnel URL"
    echo "   请确保 cloudflared 正在运行"
    exit 1
fi

echo "✅ 获取到 URL: $TUNNEL_URL"
echo ""

# 2. 获取现有 webhook
echo "📡 步骤 2: 获取现有 GitHub webhook..."
WEBHOOK_URL="$TUNNEL_URL/webhook"

HOOKS=$(curl -s -x http://localhost:19180 \
  -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/$OWNER/$REPO/hooks 2>&1)

if echo "$HOOKS" | grep -q "Bad credentials"; then
    echo "❌ 错误: GitHub Token 无效"
    echo "   请检查 GITHUB_PERSONAL_ACCESS_TOKEN 环境变量"
    exit 1
fi

# 检查是否已有 webhook
EXISTING_HOOK=$(echo "$HOOKS" | python3 -c "
import json, sys
try:
    hooks = json.load(sys.stdin)
    for h in hooks:
        if 'claude' in h.get('config', {}).get('url', '').lower():
            print(f'{h[\"id\"]}')
            break
except:
    pass
" 2>/dev/null)

echo ""

if [ -n "$EXISTING_HOOK" ]; then
    # 更新现有 webhook
    echo "📡 步骤 3: 更新现有 webhook (ID: $EXISTING_HOOK)..."
    
    RESPONSE=$(curl -s -x http://localhost:19180 -X PATCH \
      -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      https://api.github.com/repos/$OWNER/$REPO/hooks/$EXISTING_HOOK \
      -d "{\"config\":{\"url\":\"$WEBHOOK_URL\",\"content_type\":\"json\"}}" 2>&1)
    
    if echo "$RESPONSE" | grep -q "active.*true"; then
        echo "✅ Webhook 更新成功"
    else
        echo "❌ Webhook 更新失败"
        echo "   响应: $RESPONSE"
        exit 1
    fi
else
    # 创建新 webhook
    echo "📡 步骤 3: 创建新的 webhook..."
    
    RESPONSE=$(curl -s -x http://localhost:19180 -X POST \
      -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN" \
      -H "Accept: application/vnd.github+json" \
      https://api.github.com/repos/$OWNER/$REPO/hooks \
      -d "{\"name\":\"web\",\"config\":{\"url\":\"$WEBHOOK_URL\",\"content_type\":\"json\",\"secret\":\"$WEBHOOK_SECRET\"},\"events\":[\"issues\",\"issue_comment\"],\"active\":true}" 2>&1)
    
    if echo "$RESPONSE" | grep -q "active.*true"; then
        echo "✅ Webhook 创建成功"
        HOOK_ID=$(echo "$RESPONSE" | python3 -c "import json,sys; print(json.load(sys.stdin)[\"id\"])" 2>/dev/null)
        echo "   Webhook ID: $HOOK_ID"
    else
        echo "❌ Webhook 创建失败"
        echo "   响应: $RESPONSE"
        exit 1
    fi
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ 配置完成！"
echo "   Webhook URL: $WEBHOOK_URL"
echo "   仓库: $OWNER/$REPO"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

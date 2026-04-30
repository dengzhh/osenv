# 多用户 Webhook 协作方案

## 架构设计

多个开发者可以同时维护同一个仓库，各自运行本地 webhook 服务，通过不同的 label 触发。

```
GitHub Issue (label: claude-alice)
  ├─> Webhook A → Alice 本地 Claude Code (端口 5000)
GitHub Issue (label: claude-bob)
  └─> Webhook B → Bob 本地 Claude Code (端口 5001)
```

## 配置示例

### 开发者 Alice

```bash
# ~/.bashrc 添加
export REPO_OWNER="shared-repo-owner"
export REPO_NAME="shared-repo"
export TRIGGER_LABEL="claude-alice"
export WEBHOOK_PORT="5000"
export PROJECT_DIR="/home/alice/projects/shared-repo"
```

启动服务：
```bash
cd ~/projects/shared-repo
TRIGGER_LABEL="claude-alice" PORT=5000 python3 webhook/server.py
cloudflared tunnel --url http://localhost:5000
# 获取 URL 并配置 GitHub webhook
```

### 开发者 Bob

```bash
# ~/.bashrc 添加
export REPO_OWNER="shared-repo-owner"
export REPO_NAME="shared-repo"
export TRIGGER_LABEL="claude-bob"
export WEBHOOK_PORT="5001"
export PROJECT_DIR="/home/bob/projects/shared-repo"
```

启动服务：
```bash
cd ~/projects/shared-repo
TRIGGER_LABEL="claude-bob" PORT=5001 python3 webhook/server.py
cloudflared tunnel --url http://localhost:5001
# 获取 URL 并配置 GitHub webhook
```

## GitHub 仓库配置

### 创建不同的 Label

在 GitHub 仓库中创建多个触发标签：

```bash
# Alice 的 label
gh label create claude-alice --color "FFA500" --description "触发 Alice 的 Claude Code"

# Bob 的 label
gh label create claude-bob --color "00BFFF" --description "触发 Bob 的 Claude Code"

# Charlie 的 label
gh label create claude-charlie --color "32CD32" --description "触发 Charlie 的 Claude Code"
```

### 配置多个 Webhook

每个开发者在同一个仓库上创建自己的 webhook：

```bash
# Alice 的 webhook
gh api /repos/OWNER/REPO/hooks \
  -f name=web \
  -f config[url]="https://alice-tunnel.trycloudflare.com/webhook" \
  -f config[content_type]="json" \
  -f config[secret]="alice-secret" \
  -f events[0]=issues \
  -f events[1]=issue_comment \
  -f active=true

# Bob 的 webhook
gh api /repos/OWNER/REPO/hooks \
  -f name=web \
  -f config[url]="https://bob-tunnel.trycloudflare.com/webhook" \
  -f config[content_type]="json" \
  -f config[secret]="bob-secret" \
  -f events[0]=issues \
  -f events[1]=issue_comment \
  -f active=true
```

## 工作流程

### 场景 1: Alice 处理 Issue

1. 创建 GitHub issue
2. 添加 label: `claude-alice`
3. Alice 的 webhook 接收到事件
4. Alice 的本地服务检查 label 匹配
5. 触发 Alice 的 Claude Code 处理
6. 创建 PR，评论回复

### 场景 2: Bob 处理 Issue

1. 创建 GitHub issue
2. 添加 label: `claude-bob`
3. Bob 的 webhook 接收到事件
4. Bob 的本地服务检查 label 匹配
5. 触发 Bob 的 Claude Code 处理
6. 创建 PR，评论回复

### 场景 3: 协作处理

一个 issue 可以有多个 label：
- `claude-alice` - Alice 处理后端
- `claude-bob` - Bob 处理前端
- `bug`, `enhancement` - 其他标签

## 优势

1. **独立工作**：每个开发者维护自己的本地环境
2. **灵活触发**：通过不同 label 指定处理者
3. **无冲突**：各自使用不同端口和 tunnel
4. **可扩展**：轻松添加更多开发者

## 注意事项

1. **Label 命名规范**：
   - 建议格式：`claude-<username>`
   - 或使用项目前缀：`frontend-claude`, `backend-claude`

2. **端口分配**：
   - Alice: 5000
   - Bob: 5001
   - Charlie: 5002
   - 避免端口冲突

3. **Secret 管理**：
   - 每个开发者使用不同的 `WEBHOOK_SECRET`
   - 不要共享 secret

4. **Git 分支**：
   - 每个开发者创建自己的分支：`claude-alice/xxx`, `claude-bob/xxx`
   - 避免分支名冲突

5. **PR 标题**：
   - 建议格式：`[claude-alice] Issue #123: xxx`
   - 便于识别是谁的 Claude 创建的

## 快速启动脚本

为每个开发者创建专属启动脚本：

```bash
# webhook/start-alice.sh
#!/bin/bash
export TRIGGER_LABEL="claude-alice"
export PORT=5000
./webhook/start.sh

# webhook/start-bob.sh
#!/bin/bash
export TRIGGER_LABEL="claude-bob"
export PORT=5001
./webhook/start.sh
```

使用：
```bash
./webhook/start-alice.sh  # Alice 启动
./webhook/start-bob.sh    # Bob 启动
```

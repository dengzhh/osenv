# GitHub Webhook + 本地 Claude Code 自动响应方案

让 GitHub Issue 自动触发本地 Claude Code CLI 处理并创建 PR 的完整方案。

## 为什么需要这个方案？

- **使用非官方 API**: 当你使用的不是 Anthropic 官方 API（如智谱、Azure 等代理），官方 `claude-code-action` GitHub Action 无法使用
- **本地模型调用**: Claude Code CLI 在你本地运行，可以访问本地资源、文件系统和自定义配置
- **完全控制**: 对整个流程有完全控制权，可以根据需求定制 prompt、触发条件、处理逻辑

## 工作原理

```
┌─────────────────┐
│  GitHub Issue   │ (label: claude 或 @claude)
└────────┬────────┘
         │ Webhook POST
         ▼
┌─────────────────────────────────┐
│  Cloudflare Tunnel (公网URL)     │
│  https://xxx.trycloudflare.com  │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Flask Webhook Server           │
│  (localhost:5000)               │
│  - 验证 GitHub 签名              │
│  - 解析事件类型                  │
│  - 过滤触发条件                  │
│  - 异步调用 Claude CLI           │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  Claude Code CLI                │
│  - 分析 Issue 内容               │
│  - 修改/创建代码                 │
│  - 创建分支、提交、推送            │
│  - 创建 Pull Request            │
└────────┬────────────────────────┘
         │
         ▼
┌─────────────────────────────────┐
│  回复到 GitHub                  │
│  - Issue 评论                   │
│  - Pull Request                 │
└─────────────────────────────────┘
```

### 核心组件

| 组件 | 作用 |
|------|------|
| **Flask Server** (`server.py`) | Webhook 接收服务，验证签名、解析事件、调用 Claude CLI |
| **Config** (`config.py`) | 集中配置文件（仓库信息、环境变量、触发条件） |
| **Cloudflare Tunnel** | 将本地服务暴露到公网，让 GitHub webhook 能访问 |
| **GitHub Webhook** | 在仓库配置的 webhook URL，将事件 POST 到本地服务 |

### 触发条件

1. **Issue 打标签**: 创建 issue 时打上 `claude` 标签，或后续给 issue 添加 `claude` 标签
2. **Issue 评论**: 在已有 `claude` 标签的 issue 中评论 `@claude`

## 安装步骤

### 1. 安装依赖

```bash
# Python 依赖
pip3 install flask gunicorn --break-system-packages

# Cloudflare Tunnel (cloudflared)
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o ~/.local/bin/cloudflared
chmod +x ~/.local/bin/cloudflared

# 验证安装
python3 --version  # >= 3.10
flask --version
cloudflared --version
```

### 2. 复制文件到你的项目

```bash
# 在你的项目根目录创建 webhook 目录
mkdir -p webhook

# 复制以下文件到 webhook/ 目录
# - server.py
# - config.py
# - requirements.txt
```

### 3. 配置环境变量

在 `~/.bashrc` 或 `~/.zshrc` 中添加：

```bash
# GitHub Personal Access Token (需要 repo 权限)
export GITHUB_PERSONAL_ACCESS_TOKEN="ghp_xxxxxxxxxxxxxxxxxxxx"
export GH_TOKEN="$GITHUB_PERSONAL_ACCESS_TOKEN"

# Webhook 签名密钥（随机生成的密钥）
export WEBHOOK_SECRET="your-random-secret-here"

# （可选）代理设置
# export http_proxy=http://localhost:19180
# export https_proxy=http://localhost:19180
```

应用配置：
```bash
source ~/.bashrc
```

### 4. 修改 config.py

根据你的项目修改 `webhook/config.py`：

```python
# 修改为你的仓库信息
REPO_OWNER = "your-username"      # 你的 GitHub 用户名
REPO_NAME = "your-repo"          # 仓库名称

# （可选）自定义触发标签
TRIGGER_LABEL = "claude"          # 触发标签名称
TRIGGER_MENTION = "@claude"       # 触发提及关键词

# （可选）端口设置
PORT = 5000                       # Flask 服务端口
```

### 5. 创建 GitHub 标签

在 GitHub 仓库中创建触发标签：

```bash
# 方法1: 通过 GitHub API

在 GitHub 仓库中创建触发标签：

```bash
# 方法1: 通过 GitHub API
curl -X POST \
  -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/YOUR_OWNER/YOUR_REPO/labels \
  -d '{"name":"claude","color":"FFA500","description":"Trigger Claude Code"}'

# 方法2: 在 GitHub 网页上手动创建
# Settings → Labels → New label
```

## 跨项目使用

当前机制可以服务于多个 GitHub 仓库，有两种使用方式：

### 方式一：动态切换仓库（推荐）

保持一个 webhook 服务实例，通过环境变量动态切换目标仓库：

```bash
# 临时设置另一个项目的仓库信息
export REPO_OWNER="other-user"
export REPO_NAME="other-repo"

# 启动 Flask 服务（自动使用新配置）
python3 webhook/server.py
```

**优点**：
- 只需一个服务实例，节省资源
- 切换仓库只需更新环境变量，无需重启服务
- 可以快速在不同项目之间切换

**适用场景**：
- 你有多个个人仓库需要自动响应
- 测试不同项目的配置
- 临时为某个项目提供支持

### 方式二：多实例运行

为每个项目运行独立的 webhook 服务实例：

```bash
# 项目 A
REPO_OWNER="user-a"
REPO_NAME="repo-a"
PORT=5000
python3 webhook/server.py &

# 项目 B
REPO_OWNER="user-b"
REPO_NAME="repo-b"
PORT=5001
python3 webhook/server.py &

# 为项目 B 配置不同的 GitHub webhook URL
cloudflared tunnel --url http://localhost:5001
```

**优点**：
- 各项目独立运行，互不干扰
- 可以为不同项目配置不同的处理逻辑

**缺点**：
- 需要更多端口
- 需要多个 cloudflared 隧道实例
- 资源占用更高

**适用场景**：
- 多人团队协作，每人管理自己的项目
- 需要同时为多个项目提供自动响应

### 推荐的跨项目配置

如果你经常需要在多个项目间切换，推荐配置项目级别的配置文件：

```bash
# 在 ~/.bashrc 中添加快捷切换函数
switch_repo() {
    local repo=$1
    case $repo in
        osenv)
            export REPO_OWNER="dengzhh"
            export REPO_NAME="osenv"
            ;;
        other-repo)
            export REPO_OWNER="other-user"
            export REPO_NAME="other-repo"
            ;;
    esac
    echo "Switched to: $REPO_OWNER/$REPO_NAME"
}

# 使用
switch_repo osenv
python3 webhook/server.py
```

## 使用方法

### 快速启动（推荐）

**一键启动所有服务并自动配置 GitHub webhook**：

```bash
cd /path/to/your/project
./webhook/start.sh
```

这个脚本会自动：
1. ✅ 启动 Flask webhook 服务 (localhost:5000)
2. ✅ 启动 Cloudflare Tunnel（获取公网 URL）
3. ✅ 自动创建/更新 GitHub webhook 配置

**停止所有服务**：
```bash
./webhook/stop.sh
```

### 手动启动（分步）

如果需要手动控制每个步骤：

```bash
# 终端1: 启动 Flask webhook 服务
cd /path/to/your/project
python3 webhook/server.py
```

```bash
# 终端2: 启动 Cloudflare Tunnel
cloudflared tunnel --url http://localhost:5000 > /tmp/cloudflared.log 2>&1 &
```

```bash
# 终端3: 更新 GitHub webhook URL
./webhook/update_github_webhook.sh
```

### 配置 GitHub Webhook（自动化）

使用提供的自动化脚本，无需手动配置：

```bash
./webhook/update_github_webhook.sh
```

脚本会自动：
- 获取当前的 Cloudflare Tunnel URL
- 检查 GitHub 仓库是否已有 webhook
- 创建新 webhook 或更新已有 webhook 的 URL
- 验证配置成功

**手动配置**（如果需要）：

1. 在 GitHub 仓库页面：**Settings** → **Webhooks** → **Add webhook**
2. 填写配置：
   - **Payload URL**: `https://xxx.trycloudflare.com/webhook`（将 `xxx` 替换为实际 URL）
   - **Content type**: `application/json`
   - **Secret**: 你的 `WEBHOOK_SECRET` 值
   - **Events**: 勾选 `issues` 和 `issue_comment`
3. 点击 **Add webhook**

### 测试触发

在 GitHub 上创建一个 issue 并打上 `claude` 标签：

```bash
# 通过 API 创建测试 issue
curl -X POST \
  -H "Authorization: Bearer $GITHUB_PERSONAL_ACCESS_TOKEN" \
  -H "Accept: application/vnd.github+json" \
  https://api.github.com/repos/YOUR_OWNER/YOUR_REPO/issues \
  -d '{"title":"Test","body":"Create a hello.py file","labels":["claude"]}'
```

或直接在 GitHub 网页上操作。

### 验证结果

1. 检查 Flask 日志：应该看到 `Processing issue #X: ...`
2. 检查 GitHub Issue：应该有 "🤖 Claude Code 正在处理..." 评论
3. 等待几分钟后：检查是否有新的 Pull Request 创建
4. 检查日志：确认没有错误

## 故障排查

### Claude 超时

**症状**: Issue 评论显示 "⏰ Claude Code 处理超时"

**原因**: 默认 600 秒超时，对于复杂任务可能不够

**解决**: 在 `server.py` 中增加 `timeout` 值：
```python
timeout=1200,  # 20 分钟
```

### 重复触发

**症状**: 同一个 issue 启动了多个 Claude 进程

**原因**: GitHub webhook 可能发送重复事件

**解决**: 已在 `server.py` 中实现去重逻辑，确认 `_processing_issues` 代码存在

### Webhook 签名验证失败

**症状**: 日志显示 `Invalid signature`

**原因**: `WEBHOOK_SECRET` 不匹配

**解决**:
1. 确认 `~/.bashrc` 中的 `WEBHOOK_SECRET` 值
2. 确认 GitHub webhook 配置中的 Secret 值一致
3. 重启 Flask 服务

### Cloudflare Tunnel URL 变化

**症状**: 重启 cloudflared 后 URL 变了，GitHub webhook 失效

**原因**: 免费版 cloudflared 每次启动生成随机 URL

**解决（自动化）**:
```bash
# 一键更新 webhook URL
./webhook/update_github_webhook.sh
```

或重新启动整个系统：
```bash
./webhook/stop.sh
./webhook/start.sh
```

`start.sh` 脚本会自动获取最新 tunnel URL 并更新 GitHub webhook。

### Claude CLI 未找到

**症状**: 日志显示 `claude: command not found`

**原因**: Claude Code CLI 不在 PATH 中

**解决**: 在 `config.py` 中设置完整路径：
```python
CLAUDE_CLI = "/path/to/claude"  # 或 which claude 查看路径
```

## 高级配置

### 自定义 Prompt

修改 `server.py` 中的 `build_prompt()` 函数，定制 Claude 的行为：

```python
def build_prompt(title, body, author, issue_number):
    return f"""你是一个专业的开发者，请处理以下 Issue：

## Issue #{issue_number}: {title}

{body}

要求：
1. 先分析需求，不要急着写代码
2. 创建详细的测试用例
3. 实现代码并确保测试通过
4. 提交时使用规范的 commit message

请用中文回复，详细说明你的分析和实现过程。
"""
```

### 修改触发条件

在 `server.py` 的 `handle_webhook()` 函数中修改：

```python
# 只处理特定标签
if config.TRIGGER_LABEL in labels and "bug" in labels:
    should_process = True

# 只处理高优先级 issue
if issue.get("priority") == "high":
    should_process = True
```

### 添加代理支持

如果你在国内访问 GitHub 需要代理，已在 `config.py` 和 `server.py` 中集成代理设置：

```bash
export http_proxy=http://localhost:19180
export https_proxy=http://localhost:19180
```

## 生产环境建议

1. **使用进程管理器**: 用 `systemd`、`supervisord` 或 `pm2` 管理 Flask 进程
2. **命名隧道**: 注册 Cloudflare 账号创建固定 URL 的隧道
3. **日志轮转**: 配置日志轮转避免日志文件过大
4. **监控告警**: 添加健康检查和告警机制
5. **限流**: 添加限流逻辑避免短时间内处理过多 issue

## 安全注意事项

- ✅ 所有敏感信息（token、secret）存储在环境变量中，不硬编码
- ✅ Webhook 签名验证防止伪造请求
- ✅ GitHub token 使用最小权限原则（repo 权限即可）
- ⚠️ 不要将 config.py 提交到公开仓库（添加到 .gitignore）
- ⚠️ 定期轮换 WEBHOOK_SECRET 和 GITHUB_TOKEN

## 相关资源

- [GitHub Webhooks 文档](https://docs.github.com/en/developers/webhooks-and-events/webhooks/about-webhooks)
- [Cloudflare Tunnel 文档](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/)
- [Claude Code 文档](https://code.claude.com)

## 许可证

本方案可自由使用、修改和分发，请保留原作者信息。

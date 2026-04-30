import os

# GitHub webhook secret (用于验证签名)
WEBHOOK_SECRET = os.environ.get("WEBHOOK_SECRET", "change-me-in-production")

# GitHub token (从环境变量读取，不在代码中硬编码)
GITHUB_TOKEN = os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN", "")

# 仓库信息 — 支持通过环境变量动态切换
REPO_OWNER = os.environ.get("REPO_OWNER", "dengzhh")
REPO_NAME = os.environ.get("REPO_NAME", "osenv")

# 服务端口
PORT = int(os.environ.get("WEBHOOK_PORT", os.environ.get("PORT", "5000")))

# Claude Code 可执行文件路径
CLAUDE_CLI = os.environ.get("CLAUDE_CLI", "claude")

# 项目目录 (Claude Code 在此目录下工作)
# 如果设置环境变量 PROJECT_DIR，使用它；否则自动计算
PROJECT_DIR = os.environ.get(
    "PROJECT_DIR",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
)

# 触发标签（支持多个，用逗号分隔）
_TRIGGER_LABELS = os.environ.get("TRIGGER_LABELS", os.environ.get("TRIGGER_LABEL", "claude"))
TRIGGER_LABELS = [label.strip() for label in _TRIGGER_LABELS.split(",") if label.strip()]

# 触发提及
TRIGGER_MENTION = os.environ.get("TRIGGER_MENTION", "@claude")

# 代理设置
HTTP_PROXY = os.environ.get("http_proxy", os.environ.get("HTTP_PROXY", ""))

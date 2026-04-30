import hashlib
import hmac
import json
import logging
import os
import re
import subprocess
import sys
import threading
import urllib.request
from datetime import datetime

from flask import Flask, request, jsonify

import config

app = Flask(__name__)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("webhook")

# 防止同一 issue 被重复处理
_processing_issues = set()
_processing_lock = threading.Lock()


def verify_signature(payload_body: bytes, signature_header: str) -> bool:
    if not signature_header:
        return False
    expected = "sha256=" + hmac.new(
        config.WEBHOOK_SECRET.encode(), payload_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature_header)


def github_api(method, url, data=None):
    headers = {
        "Authorization": f"Bearer {config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    if body:
        req.add_header("Content-Type", "application/json")

    opener = None
    if config.HTTP_PROXY:
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({"https": config.HTTP_PROXY})
        )
    resp = (opener or urllib.request.build_opener()).open(req, timeout=30)
    if resp.status == 204:
        return {}
    return json.loads(resp.read())


def post_comment(issue_number, body):
    url = f"https://api.github.com/repos/{config.REPO_OWNER}/{config.REPO_NAME}/issues/{issue_number}/comments"
    github_api("POST", url, {"body": body})
    log.info(f"Posted comment on #{issue_number}")


def build_prompt(title, body, author, issue_number):
    return f"""请解决以下 GitHub Issue，创建代码修改并提交 PR。

## Issue #{issue_number}: {title}
作者: {author}

{body or '(无详细描述)'}

## 要求
1. 分析 issue 内容，理解需求
2. 在当前仓库中实现修改
3. 创建新分支 claude/issue-{issue_number}
4. 提交修改并推送
5. 创建 Pull Request 关联此 issue

请用中文回复。
"""


def run_claude(issue_number, title, body, author):
    with _processing_lock:
        if issue_number in _processing_issues:
            log.info(f"Issue #{issue_number} already being processed, skipping")
            return
        _processing_issues.add(issue_number)

    try:
        post_comment(
            issue_number,
            f"🤖 Claude Code 正在处理这个 issue，请稍候...",
        )

        prompt = build_prompt(title, body, author, issue_number)

        env = os.environ.copy()
        env["ANTHROPIC_BASE_URL"] = "https://open.bigmodel.cn/api/anthropic"

        result = subprocess.run(
            [
                config.CLAUDE_CLI,
                "-p",
                prompt,
                "--allowedTools",
                "Edit,Write,Read,Bash",
                "--output-format",
                "json",
                "--max-turns",
                "20",
            ],
            cwd=config.PROJECT_DIR,
            capture_output=True,
            text=True,
            env=env,
            timeout=600,
        )

        output = result.stdout.strip()
        error = result.stderr.strip()

        if result.returncode != 0:
            log.error(f"Claude CLI error: {error}")
            post_comment(
                issue_number,
                f"❌ Claude Code 处理失败:\n```\n{error[:500]}\n```",
            )
            return

        summary = ""
        if output:
            try:
                data = json.loads(output)
                for msg in data:
                    if msg.get("type") == "assistant":
                        text = msg.get("message", {}).get("content", "")
                        if isinstance(text, list):
                            for block in text:
                                if isinstance(block, dict) and block.get("type") == "text":
                                    summary = block["text"]
                                    break
                        elif isinstance(text, str):
                            summary = text
                        if summary:
                            break
            except json.JSONDecodeError:
                summary = output[:500]

        if summary:
            post_comment(
                issue_number,
                f"✅ Claude Code 已处理完成:\n\n{summary[:2000]}",
            )
        else:
            post_comment(issue_number, "✅ Claude Code 已处理完成。")

    except subprocess.TimeoutExpired:
        log.error(f"Claude timeout for issue #{issue_number}")
        post_comment(issue_number, "⏰ Claude Code 处理超时，请手动处理。")
    except Exception as e:
        log.error(f"Error processing issue #{issue_number}: {e}")
        post_comment(issue_number, f"❌ 处理出错: {str(e)[:200]}")
    finally:
        with _processing_lock:
            _processing_issues.discard(issue_number)


@app.route("/webhook", methods=["POST"])
def handle_webhook():
    signature = request.headers.get("X-Hub-Signature-256", "")
    if not verify_signature(request.data, signature):
        log.warning("Invalid signature")
        return jsonify({"error": "Invalid signature"}), 403

    event = request.headers.get("X-GitHub-Event", "")
    payload = request.get_json()

    if not payload:
        return jsonify({"error": "Invalid payload"}), 400

    log.info(f"Received event: {event}")

    if event == "ping":
        return jsonify({"msg": "pong"})

    if event == "issues":
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        labels = [l["name"] for l in issue.get("labels", [])]

        should_process = False
        if action == "opened":
            if any(label in labels for label in config.TRIGGER_LABELS):
                should_process = True
        elif action == "labeled":
            label_name = payload.get("label", {}).get("name", "")
            if label_name in config.TRIGGER_LABELS:
                should_process = True
        elif action == "edited":
            if any(label in labels for label in config.TRIGGER_LABELS):
                if config.TRIGGER_MENTION in (issue.get("body") or ""):
                    should_process = True

        if should_process:
            log.info(f"Processing issue #{issue['number']}: {issue['title']}")
            thread = threading.Thread(
                target=run_claude,
                args=(
                    issue["number"],
                    issue["title"],
                    issue.get("body", ""),
                    issue["user"]["login"],
                ),
            )
            thread.start()
            return jsonify({"status": "processing", "issue": issue["number"]})

    elif event == "issue_comment":
        comment = payload.get("comment", {})
        issue = payload.get("issue", {})
        comment_body = comment.get("body", "")

        if config.TRIGGER_MENTION in comment_body:
            labels = [l["name"] for l in issue.get("labels", [])]
            if any(label in labels for label in config.TRIGGER_LABELS):
                log.info(
                    f"Processing comment on #{issue['number']} by {comment['user']['login']}"
                )
                full_body = f"评论: {comment_body}\n\n原始 Issue: {issue.get('body', '')}"
                thread = threading.Thread(
                    target=run_claude,
                    args=(
                        issue["number"],
                        issue["title"],
                        full_body,
                        comment["user"]["login"],
                    ),
                )
                thread.start()
                return jsonify({"status": "processing", "issue": issue["number"]})

    return jsonify({"status": "ignored"})


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "repo": f"{config.REPO_OWNER}/{config.REPO_NAME}"})


if __name__ == "__main__":
    log.info(f"Starting webhook server on port {config.PORT}")
    log.info(f"Project dir: {config.PROJECT_DIR}")
    app.run(host="0.0.0.0", port=config.PORT, debug=False)

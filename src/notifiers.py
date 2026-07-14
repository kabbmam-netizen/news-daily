"""Webhook notification senders (WeChat Work and DingTalk)."""
from __future__ import annotations

import sys

import requests


def send_wechat_work(webhook_url: str, content: str) -> bool:
    """Send a markdown message to a WeChat Work group robot.

    Webhook format: https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=XXX
    """
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content},
    }
    return _post(webhook_url, payload, "WeChat Work")


def send_dingtalk(webhook_url: str, title: str, text: str) -> bool:
    """Send a markdown message to a DingTalk group robot.

    Webhook format: https://oapi.dingtalk.com/robot/send?access_token=XXX
    """
    payload = {
        "msgtype": "markdown",
        "markdown": {"title": title, "text": text},
    }
    return _post(webhook_url, payload, "DingTalk")


def _post(url: str, payload: dict, name: str) -> bool:
    try:
        resp = requests.post(url, json=payload, timeout=15)
    except Exception as e:
        print(f"[warn] {name} request failed: {e}", file=sys.stderr)
        return False

    if not resp.ok:
        print(f"[warn] {name} HTTP {resp.status_code}: {resp.text[:200]}",
              file=sys.stderr)
        return False

    # Both WeChat and DingTalk return errcode=0 on success.
    data = resp.json()
    if data.get("errcode", 0) == 0:
        print(f"[info] {name} notification sent", file=sys.stderr)
        return True
    print(f"[warn] {name} API error: {data}", file=sys.stderr)
    return False


def notify(webhook_url: str, content: str, title: str) -> bool:
    """Auto-detect webhook type from URL domain and send the message."""
    if not webhook_url:
        return False
    if "qyapi.weixin.qq.com" in webhook_url:
        return send_wechat_work(webhook_url, content)
    if "oapi.dingtalk.com" in webhook_url:
        return send_dingtalk(webhook_url, title, content)
    masked = webhook_url[:60] + ("..." if len(webhook_url) > 60 else "")
    print(f"[warn] unknown webhook domain, cannot determine type: {masked}",
          file=sys.stderr)
    return False

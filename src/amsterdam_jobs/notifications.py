
import json
import os
from datetime import datetime
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo


def send_notification():
    # Read credentials and workflow information
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]

    workflow = os.environ.get("ALERT_LABEL", "Unknown workflow")
    status = os.environ.get("ALERT_STATUS", "unknown").lower()

    # Create a link to the GitHub Actions run
    repository = os.environ["GITHUB_REPOSITORY"]
    run_id = os.environ["GITHUB_RUN_ID"]
    run_url = f"https://github.com/{repository}/actions/runs/{run_id}"

    # Format the notification
    icon = {
        "success": "✅",
        "failure": "❌",
        "cancelled": "⚠️",
        "skipped": "⚠️",
    }.get(status, "❔")

    now = datetime.now(ZoneInfo("Europe/Amsterdam"))

    message = (
        f"{icon} Amsterdam Job Market Analytics\n\n"
        f"Workflow: {workflow}\n"
        f"Status: {status.upper()}\n"
        f"Time: {now:%d.%m.%Y %H:%M} Amsterdam\n\n"
        f"GitHub Actions:\n{run_url}"
    )

    # Send the message through Telegram Bot API
    payload = urlencode({
        "chat_id": chat_id,
        "text": message,
        "disable_web_page_preview": "true",
    }).encode("utf-8")

    request = Request(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        method="POST",
    )

    try:
        with urlopen(request, timeout=20) as response:
            result = json.load(response)

        if not result.get("ok"):
            raise RuntimeError("Telegram rejected the notification")

    except HTTPError as error:
        raise SystemExit(
            f"Telegram notification failed: HTTP {error.code}"
        ) from None
    except (URLError, OSError, ValueError, RuntimeError):
        raise SystemExit(
            "Telegram notification failed: check connection and credentials"
        ) from None

    print("Telegram notification sent successfully")


if __name__ == "__main__":
    send_notification()

import requests
import re
from datetime import datetime

USERNAME = "shindonghwi"

def get_recent_events():
    url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=50"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    return response.json()

def format_date(iso_date):
    dt = datetime.fromisoformat(iso_date.replace("Z", "+00:00"))
    return dt.strftime("%Y-%m-%d")

def format_event(event):
    event_type = event["type"]
    repo = event["repo"]["name"]
    repo_url = f"https://github.com/{repo}"
    payload = event.get("payload", {})
    date = format_date(event["created_at"])

    if repo == f"{USERNAME}/{USERNAME}":
        return None

    if event_type == "PullRequestEvent":
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        pr_num = pr.get("number", "")
        pr_url = f"https://github.com/{repo}/pull/{pr_num}"
        if action == "opened":
            return (date, "Opened PR", f"[#{pr_num}]({pr_url})", f"[{repo}]({repo_url})")
        elif action == "closed" and pr.get("merged"):
            return (date, "Merged PR", f"[#{pr_num}]({pr_url})", f"[{repo}]({repo_url})")
    elif event_type == "IssuesEvent":
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_num = issue.get("number", "")
        issue_url = issue.get("html_url", "")
        if action == "opened":
            return (date, "Opened Issue", f"[#{issue_num}]({issue_url})", f"[{repo}]({repo_url})")
    elif event_type == "IssueCommentEvent":
        issue = payload.get("issue", {})
        issue_num = issue.get("number", "")
        comment_url = payload.get("comment", {}).get("html_url", "")
        return (date, "Commented", f"[#{issue_num}]({comment_url})", f"[{repo}]({repo_url})")
    elif event_type == "PullRequestReviewEvent":
        pr = payload.get("pull_request", {})
        pr_num = pr.get("number", "")
        pr_url = f"https://github.com/{repo}/pull/{pr_num}"
        return (date, "Reviewed PR", f"[#{pr_num}]({pr_url})", f"[{repo}]({repo_url})")

    return None

def generate_activity():
    events = get_recent_events()
    rows = []
    seen = set()

    for event in events:
        result = format_event(event)
        if result:
            key = (result[1], result[2], result[3])
            if key not in seen:
                seen.add(key)
                rows.append(result)
        if len(rows) >= 10:
            break

    return rows

def update_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    activities = generate_activity()
    if not activities:
        print("No activities found")
        return

    table = "| Date | Action | Link | Project |\n|------|--------|------|---------|"
    for date, action, link, project in activities:
        table += f"\n| {date} | {action} | {link} | {project} |"

    new_section = f"<!--START_SECTION:activity-->\n{table}\n<!--END_SECTION:activity-->"

    content = re.sub(
        r"<!--START_SECTION:activity-->.*<!--END_SECTION:activity-->",
        new_section,
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md updated!")

if __name__ == "__main__":
    update_readme()

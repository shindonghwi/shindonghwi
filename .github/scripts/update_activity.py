import requests
import re

USERNAME = "shindonghwi"

def get_recent_events():
    url = f"https://api.github.com/users/{USERNAME}/events/public?per_page=30"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    return response.json()

def format_event(event):
    event_type = event["type"]
    repo = event["repo"]["name"]
    repo_url = f"https://github.com/{repo}"
    payload = event.get("payload", {})

    # 본인 프로필 레포는 스킵
    if repo == f"{USERNAME}/{USERNAME}":
        return None

    if event_type == "PullRequestEvent":
        action = payload.get("action", "")
        pr = payload.get("pull_request", {})
        pr_num = pr.get("number", "")
        pr_url = f"https://github.com/{repo}/pull/{pr_num}"
        if action == "opened":
            return f"💪 Opened PR [#{pr_num}]({pr_url}) in [{repo}]({repo_url})"
        elif action == "closed" and pr.get("merged"):
            return f"🎉 Merged PR [#{pr_num}]({pr_url}) in [{repo}]({repo_url})"
    elif event_type == "PushEvent":
        commits = payload.get("commits", [])
        if commits:
            return f"⬆️ Pushed to [{repo}]({repo_url})"
    elif event_type == "IssuesEvent":
        action = payload.get("action", "")
        issue = payload.get("issue", {})
        issue_num = issue.get("number", "")
        issue_url = issue.get("html_url", "")
        if action == "opened":
            return f"❗ Opened issue [#{issue_num}]({issue_url}) in [{repo}]({repo_url})"
    elif event_type == "IssueCommentEvent":
        issue = payload.get("issue", {})
        issue_num = issue.get("number", "")
        comment_url = payload.get("comment", {}).get("html_url", "")
        return f"💬 Commented on [#{issue_num}]({comment_url}) in [{repo}]({repo_url})"
    elif event_type == "PullRequestReviewEvent":
        pr = payload.get("pull_request", {})
        pr_num = pr.get("number", "")
        pr_url = f"https://github.com/{repo}/pull/{pr_num}"
        return f"👀 Reviewed PR [#{pr_num}]({pr_url}) in [{repo}]({repo_url})"

    return None

def generate_activity():
    events = get_recent_events()
    lines = []
    seen = set()

    for event in events:
        line = format_event(event)
        if line and line not in seen:
            seen.add(line)
            lines.append(line)
        if len(lines) >= 5:
            break

    return lines

def update_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    activities = generate_activity()
    if not activities:
        print("No activities found")
        return

    activity_text = "\n".join([f"{i+1}. {line}" for i, line in enumerate(activities)])
    print("Generated activity:")
    print(activity_text)

    new_section = f"<!--START_SECTION:activity-->\n{activity_text}\n<!--END_SECTION:activity-->"

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

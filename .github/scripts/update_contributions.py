import requests
import re
import json
import os
from datetime import datetime

USERNAME = "shindonghwi"
DATA_FILE = ".github/data/contributions.json"

EXCLUDED_OWNERS = [
    USERNAME,
    "teampmm",
]

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"prs": [], "monthly_stats": {}}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_pr_details(repo, number):
    url = f"https://api.github.com/repos/{repo}/pulls/{number}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    return response.json()

def get_all_prs():
    url = f"https://api.github.com/search/issues?q=author:{USERNAME}+is:pr&sort=created&order=desc&per_page=100"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    return response.json().get("items", [])

def extract_month(date_str):
    if not date_str:
        return None
    return date_str[:7]  # "2024-12-16T..." -> "2024-12"

def process_prs(data):
    items = get_all_prs()
    existing_keys = {f"{pr['repo']}#{pr['number']}" for pr in data["prs"]}

    for item in items:
        repo_url = item["repository_url"]
        repo = repo_url.replace("https://api.github.com/repos/", "")
        owner = repo.split("/")[0]

        if owner in EXCLUDED_OWNERS:
            continue

        key = f"{repo}#{item['number']}"
        pr_details = get_pr_details(repo, item["number"])

        if not pr_details:
            continue

        # Determine status
        if pr_details.get("merged"):
            status = "Merged"
            month = extract_month(pr_details.get("merged_at"))
        elif pr_details.get("state") == "closed":
            status = "Closed"
            month = extract_month(pr_details.get("closed_at"))
        elif pr_details.get("draft"):
            status = "Draft"
            month = extract_month(pr_details.get("created_at"))
        else:
            status = "Open"
            month = extract_month(pr_details.get("created_at"))

        pr_data = {
            "repo": repo,
            "number": item["number"],
            "title": item["title"],
            "url": item["html_url"],
            "status": status,
            "month": month,
            "created_at": pr_details.get("created_at"),
            "merged_at": pr_details.get("merged_at"),
            "closed_at": pr_details.get("closed_at"),
        }

        # Update or add
        if key in existing_keys:
            for i, pr in enumerate(data["prs"]):
                if f"{pr['repo']}#{pr['number']}" == key:
                    data["prs"][i] = pr_data
                    break
        else:
            data["prs"].append(pr_data)

    return data

def calculate_monthly_stats(data):
    stats = {}
    for pr in data["prs"]:
        month = pr.get("month")
        if not month:
            continue

        if month not in stats:
            stats[month] = {"merged": 0, "open": 0, "closed": 0, "draft": 0}

        status = pr["status"].lower()
        if status in stats[month]:
            stats[month][status] += 1

    data["monthly_stats"] = stats
    return data

def generate_readme(data):
    now = datetime.now()
    current_month = now.strftime("%Y-%m")

    # Current month PRs
    current_prs = [pr for pr in data["prs"] if pr.get("month") == current_month]
    # Open PRs (regardless of month)
    open_prs = [pr for pr in data["prs"] if pr["status"] == "Open"]
    # Recent merged (not current month)
    past_merged = [pr for pr in data["prs"] if pr["status"] == "Merged" and pr.get("month") != current_month]
    past_merged = sorted(past_merged, key=lambda x: x.get("merged_at", ""), reverse=True)[:10]

    lines = []

    # Current month section
    if current_prs or open_prs:
        lines.append(f"#### {now.strftime('%B %Y')}")
        lines.append("")

        # Sort by date (most recent first)
        def get_sort_date(pr):
            if pr["status"] == "Merged" and pr.get("merged_at"):
                return pr["merged_at"]
            elif pr["status"] == "Closed" and pr.get("closed_at"):
                return pr["closed_at"]
            return pr.get("created_at", "")

        all_prs = sorted(current_prs + open_prs, key=get_sort_date, reverse=True)

        seen = set()
        for pr in all_prs:
            key = f"{pr['repo']}#{pr['number']}"
            if key in seen:
                continue
            seen.add(key)
            # Get date based on status
            if pr["status"] == "Merged" and pr.get("merged_at"):
                date_str = pr["merged_at"][:10]  # "2024-12-17"
            elif pr["status"] == "Closed" and pr.get("closed_at"):
                date_str = pr["closed_at"][:10]
            else:
                date_str = pr.get("created_at", "")[:10]
            date_display = date_str[5:] if date_str else ""  # "12-17"
            lines.append(f"- `{pr['status']}` `{date_display}` [{pr['repo']}#{pr['number']}]({pr['url']}) — {pr['title']}")
        lines.append("")

    # Monthly stats table
    sorted_months = sorted(data["monthly_stats"].keys(), reverse=True)
    recent_months = sorted_months[:6]  # Last 6 months

    if recent_months:
        lines.append("#### Monthly Stats")
        lines.append("")
        lines.append("| Month | Merged | Open | Closed | Total |")
        lines.append("|:---:|:---:|:---:|:---:|:---:|")
        for month in recent_months:
            stats = data["monthly_stats"][month]
            m = stats.get("merged", 0)
            o = stats.get("open", 0)
            c = stats.get("closed", 0)
            t = m + o + c
            # Bold current month
            if month == current_month:
                lines.append(f"| **{month}** | {m} | {o} | {c} | {t} |")
            else:
                lines.append(f"| {month} | {m} | {o} | {c} | {t} |")
        lines.append("")

    # Past merged highlights
    if past_merged:
        lines.append("<details>")
        lines.append("<summary>Past Merged PRs</summary>")
        lines.append("")
        for pr in past_merged:
            lines.append(f"- `{pr['month']}` [{pr['repo']}#{pr['number']}]({pr['url']}) — {pr['title']}")
        lines.append("")
        lines.append("</details>")

    return "\n".join(lines)

def update_readme(data):
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    contrib_content = generate_readme(data)
    contrib_section = f"<!--START_SECTION:contributions-->\n{contrib_content}\n<!--END_SECTION:contributions-->"

    content = re.sub(
        r"<!--START_SECTION:contributions-->.*<!--END_SECTION:contributions-->",
        contrib_section,
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md updated!")

def main():
    data = load_data()
    data = process_prs(data)
    data = calculate_monthly_stats(data)
    save_data(data)
    update_readme(data)
    print(f"Processed {len(data['prs'])} PRs")
    print(f"Monthly stats: {data['monthly_stats']}")

if __name__ == "__main__":
    main()

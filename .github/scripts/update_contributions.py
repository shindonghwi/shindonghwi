import requests
import re

USERNAME = "shindonghwi"

EXCLUDED_OWNERS = [
    USERNAME,
    "teampmm",
]

def get_pr_status(repo, number):
    """Get actual PR status by fetching PR details"""
    url = f"https://api.github.com/repos/{repo}/pulls/{number}"
    response = requests.get(url)
    if response.status_code != 200:
        return "Open"

    pr = response.json()
    if pr.get("merged"):
        return "Merged"
    elif pr.get("state") == "closed":
        return "Closed"
    elif pr.get("draft"):
        return "Draft"
    return "Open"

def get_all_prs():
    url = f"https://api.github.com/search/issues?q=author:{USERNAME}+is:pr&sort=updated&order=desc&per_page=100"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    data = response.json()
    prs = []

    for item in data.get("items", []):
        repo_url = item["repository_url"]
        repo = repo_url.replace("https://api.github.com/repos/", "")
        owner = repo.split("/")[0]

        if owner in EXCLUDED_OWNERS:
            continue

        status = get_pr_status(repo, item["number"])

        prs.append({
            "repo": repo,
            "number": item["number"],
            "title": item["title"],
            "url": item["html_url"],
            "status": status,
        })

    return prs

def update_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    prs = get_all_prs()
    if prs:
        lines = []
        for pr in prs:
            lines.append(f"- `{pr['status']}` [{pr['repo']}#{pr['number']}]({pr['url']}) — {pr['title']}")
        contrib_section = "<!--START_SECTION:contributions-->\n" + "\n".join(lines) + "\n<!--END_SECTION:contributions-->"
    else:
        contrib_section = "<!--START_SECTION:contributions-->\n<!--END_SECTION:contributions-->"

    content = re.sub(
        r"<!--START_SECTION:contributions-->.*<!--END_SECTION:contributions-->",
        contrib_section,
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md updated!")

if __name__ == "__main__":
    update_readme()

import requests
import re

USERNAME = "shindonghwi"

# 제외할 organization/owner 목록
EXCLUDED_OWNERS = [
    USERNAME,
    "teampmm",
]

def get_all_prs():
    url = f"https://api.github.com/search/issues?q=author:{USERNAME}+is:pr+is:merged&sort=updated&order=desc&per_page=100"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    data = response.json()
    prs = []

    for item in data.get("items", []):
        repo_url = item["repository_url"]
        repo = repo_url.replace("https://api.github.com/repos/", "")
        owner = repo.split("/")[0]

        # 제외 목록에 있으면 스킵
        if owner in EXCLUDED_OWNERS:
            continue

        prs.append({
            "repo": repo,
            "number": item["number"],
            "title": item["title"],
            "url": item["html_url"],
        })

    return prs

def update_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    prs = get_all_prs()

    if not prs:
        section = "<!--START_SECTION:contributions-->\n<!--END_SECTION:contributions-->"
    else:
        lines = []
        for pr in prs:
            lines.append(f"- [{pr['repo']}#{pr['number']}]({pr['url']}) — {pr['title']}")

        section = "<!--START_SECTION:contributions-->\n" + "\n".join(lines) + "\n<!--END_SECTION:contributions-->"

    content = re.sub(
        r"<!--START_SECTION:contributions-->.*<!--END_SECTION:contributions-->",
        section,
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md updated!")

if __name__ == "__main__":
    update_readme()

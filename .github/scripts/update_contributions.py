import requests
import re
from datetime import datetime

USERNAME = "shindonghwi"
NPM_SCOPE = "sognora"

EXCLUDED_OWNERS = [
    USERNAME,
    "teampmm",
]

def get_npm_packages():
    url = f"https://registry.npmjs.org/-/v1/search?text=@{NPM_SCOPE}&size=100"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    data = response.json()
    packages = []

    for obj in data.get("objects", []):
        pkg = obj.get("package", {})
        name = pkg.get("name", "")
        version = pkg.get("version", "")
        date_str = pkg.get("date", "")

        if date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date = dt.strftime("%Y-%m-%d")
        else:
            date = ""

        packages.append({
            "name": name,
            "description": pkg.get("description", ""),
            "url": f"https://www.npmjs.com/package/{name}",
            "version": version,
            "date": date,
        })

    return packages

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

        if item.get("pull_request", {}).get("merged_at"):
            status = "Merged"
        elif item.get("state") == "closed":
            status = "Closed"
        elif item.get("draft"):
            status = "Draft"
        else:
            status = "Open"

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

    # Libraries
    packages = get_npm_packages()
    if packages:
        lines = []
        for pkg in packages:
            lines.append(f"- [{pkg['name']}]({pkg['url']}) `{pkg['version']}` ({pkg['date']}) — {pkg['description']}")
        libs_section = "<!--START_SECTION:libraries-->\n" + "\n".join(lines) + "\n<!--END_SECTION:libraries-->"
    else:
        libs_section = "<!--START_SECTION:libraries-->\n<!--END_SECTION:libraries-->"

    content = re.sub(
        r"<!--START_SECTION:libraries-->.*<!--END_SECTION:libraries-->",
        libs_section,
        content,
        flags=re.DOTALL
    )

    # Contributions
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

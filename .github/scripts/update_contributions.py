import requests
import re

GITHUB_USERNAME = "shindonghwi"

# 기여하고 싶은 레포지토리 목록 (owner/repo 형식)
TARGET_REPOS = [
    "flutter/flutter",
    "flutter/engine",
    "riverpod/riverpod",
]

def get_merged_prs(repo):
    """특정 레포지토리에서 머지된 PR 목록 가져오기"""
    url = f"https://api.github.com/search/issues?q=author:{GITHUB_USERNAME}+repo:{repo}+is:pr+is:merged&sort=updated&order=desc"
    response = requests.get(url)
    if response.status_code != 200:
        return []

    data = response.json()
    prs = []
    for item in data.get("items", []):
        prs.append({
            "number": item["number"],
            "title": item["title"],
            "url": item["html_url"],
        })
    return prs

def generate_contributions_section():
    """기여 섹션 마크다운 생성"""
    all_contributions = {}

    for repo in TARGET_REPOS:
        prs = get_merged_prs(repo)
        if prs:
            all_contributions[repo] = prs

    if not all_contributions:
        return ""

    lines = ["", "---", "", "### 🔧 Open Source", ""]

    for repo, prs in all_contributions.items():
        pr_links = ", ".join([f"[#{pr['number']}]({pr['url']})" for pr in prs])
        lines.append(f"- [{repo}](https://github.com/{repo}) - {pr_links}")

    return "\n".join(lines)

def update_readme():
    """README.md 업데이트"""
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    # 기존 Open Source 섹션 제거
    content = re.sub(r'\n---\n+### 🔧 Open Source\n.*', '', content, flags=re.DOTALL)
    content = content.rstrip()

    # 새 기여 섹션 추가
    contributions = generate_contributions_section()
    new_content = content + contributions + "\n"

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(new_content)

    print("README.md updated!")

if __name__ == "__main__":
    update_readme()

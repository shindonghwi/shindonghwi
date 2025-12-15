import requests
import re
from datetime import datetime

NPM_SCOPE = "sognora"

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
        keywords = pkg.get("keywords", [])

        if date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            date = dt.strftime("%Y-%m-%d")
        else:
            date = ""

        packages.append({
            "name": name,
            "url": f"https://www.npmjs.com/package/{name}",
            "version": version,
            "date": date,
            "keywords": keywords,
        })

    return packages

def update_readme():
    with open("README.md", "r", encoding="utf-8") as f:
        content = f.read()

    packages = get_npm_packages()
    if packages:
        lines = []
        for pkg in packages:
            keywords_str = " ".join([f"`{k}`" for k in pkg['keywords'][:5]]) if pkg['keywords'] else ""
            line = f"- [{pkg['name']}]({pkg['url']}) · `v{pkg['version']}` · {pkg['date']}"
            if keywords_str:
                line += f"<br>{keywords_str}"
            lines.append(line)
        libs_section = "<!--START_SECTION:libraries-->\n" + "\n".join(lines) + "\n<!--END_SECTION:libraries-->"
    else:
        libs_section = "<!--START_SECTION:libraries-->\n<!--END_SECTION:libraries-->"

    content = re.sub(
        r"<!--START_SECTION:libraries-->.*<!--END_SECTION:libraries-->",
        libs_section,
        content,
        flags=re.DOTALL
    )

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(content)

    print("README.md updated!")

if __name__ == "__main__":
    update_readme()

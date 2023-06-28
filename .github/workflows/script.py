import requests

def get_latest_release(repo):
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    response = requests.get(url)
    
    if response.status_code == 200:
        release_info = response.json()
        tag_name = release_info["tag_name"]
        release_notes = release_info["body"]
        return tag_name, release_notes
    
    return None, None

def update_readme(repo_name, latest_release, release_notes):
    readme_file = "README.md"  # 替换为你的 README.md 文件路径
    
    with open(readme_file, "r") as file:
        readme_content = file.read()
    
    # 更新版本号和更新内容
    new_content = readme_content.replace("{{latest_release}}", latest_release)
    new_content = new_content.replace("{{release_notes}}", release_notes)
    
    with open(readme_file, "w") as file:
        file.write(new_content)

# 用法示例
repo_name = "Ehviewer-Overhauled/Ehviewer"  # 请替换为你要检测的仓库的所有者和名称
latest_release, release_notes = get_latest_release(repo_name)
if latest_release:
    print(f"The latest release of {repo_name} is: {latest_release}")
    print(f"Release notes:\n{release_notes}")
    update_readme(repo_name, latest_release, release_notes)
else:
    print("Failed to retrieve the latest release.")

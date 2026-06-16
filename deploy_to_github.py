# -*- coding: utf-8 -*-
"""
GitHub 自动化部署脚本
自动创建仓库、推送代码到 GitHub
"""

import os
import base64
import requests
from pathlib import Path

# ========== 配置（请修改以下信息）==========
GITHUB_TOKEN = "YOUR_GITHUB_TOKEN"  # 在 https://github.com/settings/tokens 生成
GITHUB_USERNAME = "hanby123"        # 你的 GitHub 用户名
REPO_NAME = "jingju"                # 仓库名
REPO_DESCRIPTION = "京剧数据可视化竞赛 - 项目上传网站 | ChinaVis 2026"
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
HEADERS = {
    "Authorization": f"token {GITHUB_TOKEN}",
    "Accept": "application/vnd.github.v3+json"
}


def create_repo():
    """创建 GitHub 仓库"""
    url = "https://api.github.com/user/repos"
    data = {
        "name": REPO_NAME,
        "description": REPO_DESCRIPTION,
        "private": False,
        "auto_init": False
    }
    resp = requests.post(url, json=data, headers=HEADERS)
    if resp.status_code == 201:
        print(f"✓ 仓库创建成功: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}")
        return True
    elif resp.status_code == 422:
        print(f"⚠ 仓库已存在，将直接推送代码")
        return True
    else:
        print(f"✗ 创建仓库失败: {resp.status_code} {resp.text}")
        return False


def get_file_tree():
    """获取所有需要上传的文件"""
    files = []
    for root, dirs, filenames in os.walk(BASE_DIR):
        # 跳过 __pycache__、venv、uploads、.git
        dirs[:] = [d for d in dirs if d not in ('__pycache__', 'venv', 'uploads', '.git', 'static/img')]
        for fname in filenames:
            if fname in ('.DS_Store', 'Thumbs.db'):
                continue
            full_path = Path(root) / fname
            rel_path = full_path.relative_to(BASE_DIR)
            files.append((str(rel_path), full_path))
    return files


def upload_file(filepath, content):
    """上传单个文件到 GitHub"""
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{REPO_NAME}/contents/{filepath}"
    data = {
        "message": f"Upload {filepath}",
        "content": base64.b64encode(content).decode('utf-8')
    }
    resp = requests.put(url, json=data, headers=HEADERS)
    if resp.status_code in (201, 200):
        print(f"  ✓ {filepath}")
        return True
    elif resp.status_code == 422:
        # 文件已存在，需要先获取 SHA 再更新
        get_resp = requests.get(url, headers=HEADERS)
        if get_resp.status_code == 200:
            sha = get_resp.json()['sha']
            data['sha'] = sha
            resp2 = requests.put(url, json=data, headers=HEADERS)
            if resp2.status in (201, 200):
                print(f"  ✓ {filepath} (已更新)")
                return True
        print(f"  ✗ {filepath} 更新失败")
        return False
    else:
        print(f"  ✗ {filepath} 上传失败: {resp.status_code}")
        return False


def main():
    if GITHUB_TOKEN == "YOUR_GITHUB_TOKEN":
        print("=" * 50)
        print("请先修改脚本中的配置：")
        print("  1. GITHUB_TOKEN = '你的GitHub访问令牌'")
        print("  2. GITHUB_USERNAME = '你的用户名'")
        print("  3. REPO_NAME = '仓库名'")
        print("=" * 50)
        print()
        print("如何生成 GitHub Token：")
        print("  1. 登录 https://github.com")
        print("  2. 点击右上角头像 → Settings")
        print("  3. 左侧菜单 → Developer settings")
        print("  4. Personal access tokens → Tokens (classic)")
        print("  5. 点击 Generate new token (classic)")
        print("  6. 勾选 repo (完全控制私有仓库)")
        print("  7. 生成并复制 token")
        print()
        print("运行脚本命令：")
        print("  python deploy_to_github.py")
        return

    print(f"正在推送到 GitHub: {GITHUB_USERNAME}/{REPO_NAME} ...")

    if not create_repo():
        return

    files = get_file_tree()
    print(f"找到 {len(files)} 个文件，开始上传...")
    print()

    success = 0
    for filepath, full_path in files:
        try:
            content = full_path.read_bytes()
            if upload_file(filepath, content):
                success += 1
        except Exception as e:
            print(f"  ✗ {filepath} 读取失败: {e}")

    print()
    print(f"=" * 50)
    print(f"✓ 成功上传 {success}/{len(files)} 个文件")
    print(f"  仓库地址: https://github.com/{GITHUB_USERNAME}/{REPO_NAME}")
    print(f"=" * 50)


if __name__ == '__main__':
    main()

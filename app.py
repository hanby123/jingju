# -*- coding: utf-8 -*-
"""
京剧数据可视化竞赛 - 项目上传与管理网站
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime

from flask import (
    Flask, render_template, request, redirect,
    url_for, flash, send_from_directory, jsonify
)

app = Flask(__name__)
app.secret_key = 'jingju-viz-2026-secret-key'

# ---------- 路径配置 ----------
BASE_DIR = Path(__file__).resolve().parent

# Render 免费版只有 /tmp 可写
if os.environ.get('RENDER'):
    UPLOAD_FOLDER = Path('/tmp/uploads')
else:
    UPLOAD_FOLDER = BASE_DIR / 'uploads'

ALLOWED_EXTENSIONS = {
    'py', 'xlsx', 'xls', 'csv', 'json', 'html', 'css', 'js',
    'png', 'jpg', 'jpeg', 'gif', 'svg', 'pdf', 'txt', 'md',
    'ttf', 'conf', 'xml', 'iml', 'gitignore'
}
MAX_CONTENT_LENGTH = 100 * 1024 * 1024  # 100MB

app.config['UPLOAD_FOLDER'] = str(UPLOAD_FOLDER)
app.config['MAX_CONTENT_LENGTH'] = MAX_CONTENT_LENGTH

# 确保上传目录存在
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_project_stats():
    """获取项目统计信息"""
    src_dir = BASE_DIR.parent

    # 项目总大小
    total_size = 0
    file_count = 0
    py_files = 0
    image_files = 0
    data_files = 0
    for root, dirs, files in os.walk(src_dir):
        # 跳过 venv 和 .idea
        rel = Path(root).relative_to(src_dir)
        if any(part.startswith('.') or part == 'venv' or part == '__pycache__' or part == 'node_modules'
               for part in rel.parts):
            continue
        for f in files:
            fp = Path(root) / f
            if not fp.is_symlink():
                total_size += fp.stat().st_size
                file_count += 1
                ext = f.rsplit('.', 1)[-1].lower() if '.' in f else ''
                if ext == 'py':
                    py_files += 1
                elif ext in ('png', 'jpg', 'jpeg', 'gif', 'svg'):
                    image_files += 1
                elif ext in ('xlsx', 'xls', 'csv', 'json'):
                    data_files += 1

    return {
        'total_size': total_size,
        'file_count': file_count,
        'py_files': py_files,
        'image_files': image_files,
        'data_files': data_files,
        'upload_count': len(list(UPLOAD_FOLDER.iterdir())) if UPLOAD_FOLDER.exists() else 0
    }


def get_size_str(size_bytes):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def get_project_tree():
    """获取项目文件树"""
    src_dir = BASE_DIR.parent
    tree = []

    def walk_dir(dir_path, relative_to):
        items = []
        try:
            entries = sorted(os.listdir(dir_path))
        except PermissionError:
            return items

        for entry in entries:
            full = Path(dir_path) / entry
            rel = str(full.relative_to(relative_to)).replace('\\', '/')

            # 跳过隐藏目录和 venv
            if entry.startswith('.') or entry == 'venv' or entry == '__pycache__' or entry == 'node_modules':
                continue

            if full.is_dir():
                children = walk_dir(full, relative_to)
                items.append({
                    'name': entry,
                    'path': rel,
                    'type': 'folder',
                    'children': children
                })
            else:
                ext = entry.rsplit('.', 1)[-1].lower() if '.' in entry else ''
                size = full.stat().st_size
                items.append({
                    'name': entry,
                    'path': rel,
                    'type': 'file',
                    'ext': ext,
                    'size': get_size_str(size)
                })

        return items

    root_items = walk_dir(src_dir, src_dir)
    return root_items


# ====================== 路由 ======================


@app.route('/')
def index():
    """首页 - 项目展示"""
    stats = get_project_stats()
    return render_template('index.html', stats=stats, get_size_str=get_size_str)


@app.route('/browse')
def browse():
    """浏览项目文件"""
    tree = get_project_tree()
    return render_template('browse.html', tree=tree)


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    """上传页面"""
    if request.method == 'POST':
        # 检查是否有文件
        if 'files' not in request.files:
            flash('没有选择文件', 'error')
            return redirect(request.url)

        files = request.files.getlist('files')
        uploaded_count = 0
        skipped_count = 0

        for file in files:
            if file and file.filename:
                if allowed_file(file.filename):
                    # 安全检查文件名
                    safe_name = file.filename.replace('..', '').replace('/', '_').replace('\\', '_')
                    save_path = UPLOAD_FOLDER / safe_name

                    # 如果文件已存在，添加时间戳
                    if save_path.exists():
                        name_part, ext_part = safe_name.rsplit('.', 1) if '.' in safe_name else (safe_name, '')
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        safe_name = f"{name_part}_{timestamp}.{ext_part}"
                        save_path = UPLOAD_FOLDER / safe_name

                    file.save(str(save_path))
                    uploaded_count += 1
                else:
                    skipped_count += 1

        if uploaded_count > 0:
            flash(f'成功上传 {uploaded_count} 个文件！', 'success')
        if skipped_count > 0:
            flash(f'{skipped_count} 个文件因类型不支持被跳过', 'warning')

        return redirect(url_for('files'))

    return render_template('upload.html')


@app.route('/files')
def files():
    """已上传文件列表"""
    uploaded_files = []
    if UPLOAD_FOLDER.exists():
        for f in sorted(UPLOAD_FOLDER.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True):
            if f.is_file():
                ext = f.suffix[1:].lower()
                uploaded_files.append({
                    'name': f.name,
                    'ext': ext,
                    'size': get_size_str(f.stat().st_size),
                    'time': datetime.fromtimestamp(f.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                })

    return render_template('files.html', files=uploaded_files)


@app.route('/download/<filename>')
def download(filename):
    """下载上传的文件"""
    return send_from_directory(str(UPLOAD_FOLDER), filename, as_attachment=True)


@app.route('/delete/<filename>', methods=['POST'])
def delete(filename):
    """删除上传的文件"""
    file_path = UPLOAD_FOLDER / filename
    if file_path.exists() and file_path.is_file():
        file_path.unlink()
        flash(f'已删除文件: {filename}', 'success')
    return redirect(url_for('files'))


@app.route('/api/stats')
def api_stats():
    """API: 获取项目统计数据"""
    return jsonify(get_project_stats())


# ====================== 启动 ======================

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    print(f"  {'='*50}")
    print(f"  京剧数据可视化竞赛 - 项目网站")
    print(f"  {'='*50}")
    print(f"  访问地址: http://127.0.0.1:{port}")
    print(f"  上传目录: {UPLOAD_FOLDER}")
    print(f"  {'='*50}")
    app.run(debug=not os.environ.get('RENDER'), host='0.0.0.0', port=port)

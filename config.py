"""
配置文件
"""
import os

# Git仓库搜索路径（可以设置环境变量 GIT_REPO_SEARCH_PATH 来覆盖）
GIT_REPO_SEARCH_PATH = os.environ.get('GIT_REPO_SEARCH_PATH', os.path.expanduser("~"))

# 日报保存路径
REPORT_SAVE_DIR = os.path.join(os.path.dirname(__file__), 'reports')

# 需要排除的目录（提高搜索效率）
EXCLUDE_DIRS = ['.git', 'node_modules', '.venv', 'venv', '__pycache__', '.idea', '.vscode', '.cursor']

# 日报文件格式
REPORT_FILE_FORMAT = "日报_{date}.txt"  # {date} 会被替换为日期

# DeepSeek API（优先使用环境变量 DEEPSEEK_API_KEY，避免 key 进仓库）
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-91ee266d045e47c28ae1cfeb461ea9d7')
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_MODEL = 'deepseek-chat'

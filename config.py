"""
配置文件
"""
import os

# Git仓库搜索路径（可设置环境变量 GIT_REPO_SEARCH_PATH 覆盖）
# 单路径默认值（环境变量未设置时的 fallback）
GIT_REPO_SEARCH_PATH = os.environ.get('GIT_REPO_SEARCH_PATH', os.path.expanduser("~"))

# 默认 Git 仓库搜索路径列表（无环境变量时使用，main 会过滤存在的目录）
GIT_SEARCH_PATHS = [
    os.path.expanduser("~/Desktop/vankun/code"),
    # os.path.expanduser("~/Documents/开发代码"),
]

# 日报保存路径（项目根目录下的 reports）
REPORT_SAVE_DIR = os.path.join(os.path.dirname(__file__), 'reports')

# Git 搜索时需排除的目录（提高效率，git_service 使用）
EXCLUDE_DIRS = ['.git', 'node_modules', '.venv', 'venv', '__pycache__', '.idea', '.vscode', '.cursor']

# 日报/简报文件格式（{date} 替换为 YYYYMMDD）
REPORT_FILE_FORMAT = "日报_{date}.txt"
BRIEF_FILE_FORMAT = "简报_{date}.txt"

# DeepSeek API（优先使用环境变量 DEEPSEEK_API_KEY，避免 key 进仓库）
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY', 'sk-91ee266d045e47c28ae1cfeb461ea9d7')
DEEPSEEK_BASE_URL = 'https://api.deepseek.com'
DEEPSEEK_MODEL = 'deepseek-chat'

# CRM 登录配置
CRM_URL = "https://crm.vankun.cn/crm/"
CRM_USERNAME = "eddy.yang"
CRM_PASSWORD = "xxx"

# DeepSeek 简报生成修饰词配置
# 工作描述风格：用于修饰生成的工作内容描述
BRIEF_STYLE_MODIFIERS = {
    # 工作描述风格
    "work_style": "专业、详细、具体",  # 可选：专业、简洁、详细、具体、概括等
    
    # 语气修饰
    "tone": "积极、客观、正式",  # 可选：积极、客观、正式、简洁等
    
    # 用词偏好
    "word_preference": "使用技术术语，但保持通俗易懂",  # 可选：技术术语、通俗易懂、专业术语等
    
    # 时间描述方式
    "time_description": "精确到具体时间段",  # 可选：精确、概括、合理分配等
    
    # 工作内容描述要求
    "work_description": "详细描述工作内容，包括具体的技术点、实现方式、遇到的问题和解决方案",
    
    # 学习内容描述要求
    "learning_description": "基于实际工作内容，描述相关的技术学习和实践进度，体现持续学习的态度",
}

# DeepSeek 系统提示词修饰
BRIEF_SYSTEM_MODIFIER = (
    "请使用{work_style}的风格，{tone}的语气，{word_preference}。"
    "{work_description}。"
    "{learning_description}。"
).format(**BRIEF_STYLE_MODIFIERS)

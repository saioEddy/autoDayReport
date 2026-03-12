# 自动化日报提交程序

自动发现本地Git仓库，生成每日提交清单的日报程序，支持AI智能润色和CRM自动发布。

**✅ 跨平台支持**: 支持 macOS、Linux 和 Windows 系统

## 功能特性

1. **自动发现Git仓库**: 递归搜索指定目录下的所有Git仓库
2. **获取今日提交**: 自动获取所有仓库中今日的所有提交记录（含完整提交描述体）
3. **生成提交清单**: 按作者和仓库分组，生成格式化的提交清单
4. **保存日报**: 自动保存日报到文件
5. **AI智能简报**: 使用DeepSeek AI自动润色生成工作简报（区分本人提交/协助他人）
6. **CRM自动发布**: 支持自动登录CRM系统并发布日报（可选）
7. **配置集中管理**: 所有配置项集中在 `config.py`，便于维护
8. **远程GitLab模式**: 通过 GitLab API 拉取今日有提交活动的项目，无需本地 clone
9. **昨日备用简报**: 全天无任何提交时，自动获取昨日记录并创造性改写为今日简报，避免内容雷同
10. **自定义内容模式**: 支持直接输入工作描述字符串，跳过 Git 记录直接生成简报
11. **免确认自动发布**: 支持 `auto` 参数跳过人工确认，直接发布到 CRM

## 项目结构

```
自动化日报提交/
├── service/                  # 服务层（业务逻辑）
│   ├── git_service.py       # Git仓库服务
│   ├── report_service.py    # 日报生成服务
│   ├── deepseek_service.py  # DeepSeek AI服务
│   └── crm_service.py       # CRM自动发布服务
├── main.py                  # 主程序入口
├── config.py                # 配置文件（集中管理所有配置）
├── requirements.txt         # 依赖文件
└── reports/                 # 日报保存目录（自动创建）
    ├── 日报_YYYYMMDD.txt    # 原始提交清单日报
    └── 简报_YYYYMMDD.txt    # AI润色后的工作简报
```

## 系统要求

- Python 3.6+
- Git 已安装并配置在系统PATH中
- DeepSeek API Key（用于AI简报生成，可在 `config.py` 中配置或使用环境变量）
- Playwright（用于CRM自动发布，首次运行会自动安装）

## 安装依赖

在运行程序前，需要先安装Python依赖包：

```bash
pip install -r requirements.txt
```

**主要依赖：**
- `openai>=1.0.0` - 用于调用DeepSeek API（兼容OpenAI格式）
- `requests>=2.28.0` - HTTP请求库
- `playwright>=1.40.0` - 浏览器自动化（用于CRM发布）

**安装Playwright浏览器驱动：**

安装Python包后，还需要安装Playwright的浏览器驱动：

```bash
playwright install chromium
```

## 使用方法

### 1. 运行程序

**标准模式（交互式确认是否发布 CRM）：**
```bash
# macOS/Linux
python3 main.py

# Windows
python main.py
```

**免确认自动发布模式（跳过 y/n 询问，直接发布）：**
```bash
python3 main.py auto
```

**自定义内容模式（输入工作描述，跳过 Git 记录直接生成简报）：**
```bash
# 写法一：等号连接
python3 main.py --content=今天完成了登录模块的开发和联调测试

# 写法二：空格分隔
python3 main.py --content "今天完成了登录模块的开发和联调测试"

# 组合 auto 参数：生成简报后直接发布到 CRM
python3 main.py auto --content=今天完成了登录模块的开发和联调测试
```

### 2. 数据来源模式

在 `config.py` 中通过 `COMMIT_SOURCE` 切换数据来源：

```python
# 远程模式：通过 GitLab API 获取，无需本地 clone（推荐）
COMMIT_SOURCE = 'remote'

# 本地模式：递归扫描本地已 clone 的仓库
COMMIT_SOURCE = 'local'
```

**远程模式（remote）：**
- 通过 GitLab REST API v4 拉取今日有提交活动的项目
- 无需将所有仓库 clone 到本地，效率更高
- 需要配置 `GITLAB_URL` 和 `GITLAB_TOKEN`
- Token 生成地址：`http://<gitlab地址>/-/profile/personal_access_tokens`

**本地模式（local）：**
- 递归扫描 `GIT_SEARCH_PATHS` 中配置的本地目录
- 适合仓库已全部 clone 到本地的场景

### 3. 配置说明

所有配置项都集中在 `config.py` 文件中，主要包括：

#### Git仓库搜索路径配置（本地模式）

程序会按以下优先级搜索Git仓库：
1. 环境变量 `GIT_REPO_SEARCH_PATH` 指定的路径（单路径）
2. `config.py` 中的 `GIT_SEARCH_PATHS` 列表（多路径，推荐）
3. 用户主目录 `~` (最后备选)

**推荐方式：在 `config.py` 中配置**
```python
GIT_SEARCH_PATHS = [
    os.path.expanduser("~/Desktop/vankun/code"),
    os.path.expanduser("~/Documents/开发代码"),
]
```

**环境变量方式（macOS/Linux）:**
```bash
export GIT_REPO_SEARCH_PATH=/path/to/your/projects
python3 main.py
```

**环境变量方式（Windows）:**
```cmd
# 临时设置（当前会话）
set GIT_REPO_SEARCH_PATH=C:\Users\YourName\Documents\Projects
python main.py

# 永久设置（系统环境变量）
# 在"系统属性" -> "环境变量"中添加 GIT_REPO_SEARCH_PATH
```

#### DeepSeek API配置

用于AI简报生成，推荐使用环境变量避免密钥泄露：

```bash
# macOS/Linux
export DEEPSEEK_API_KEY=your_api_key_here

# Windows
set DEEPSEEK_API_KEY=your_api_key_here
```

或在 `config.py` 中直接配置（不推荐，密钥会进入代码仓库）。

#### CRM登录配置

在 `config.py` 中配置CRM系统信息：
```python
CRM_URL = "https://crm.vankun.cn/crm/"
CRM_USERNAME = "your_username"
CRM_PASSWORD = "your_password"
```

#### GitLab 远程模式配置

```python
COMMIT_SOURCE = 'remote'
GITLAB_URL = 'http://your-gitlab-server'
GITLAB_TOKEN = 'your-personal-access-token'  # 建议改用环境变量
```

或使用环境变量：
```bash
export GITLAB_TOKEN=your_token_here
```

#### 本人作者标识配置

程序通过 `MY_GIT_AUTHORS` 区分「本人提交」和「他人提交」，建议把所有使用过的 Git 用户名都填入：

```python
MY_GIT_AUTHORS = ['yourname', 'your.name', 'YourName']
```

#### 简报生成风格配置

可在 `config.py` 中的 `BRIEF_SYSTEM_MODIFIER` 调整AI生成简报的风格：
- 工作描述风格（专业、简洁、详细等）
- 语气修饰（积极、客观、正式等）
- 用词偏好（技术术语、通俗易懂等）

### 4. CRM自动发布（可选）

程序运行完成后会询问是否自动发布到CRM系统：

```
是否要自动发布到 CRM 系统? (y/n):
```

输入 `y` 后，程序会：
1. 自动打开浏览器（使用Playwright）
2. 登录CRM系统
3. 将生成的简报内容自动填入表单
4. 提交日报

使用 `auto` 参数可跳过询问，直接发布：
```bash
python3 main.py auto
```

**注意：**
- 首次使用需要安装Playwright浏览器驱动：`playwright install chromium`
- 浏览器会以非无头模式运行（`headless=False`），方便查看和调试
- 确保 `config.py` 中已正确配置CRM登录信息

### 5. 定时任务（可选）

#### macOS/Linux (使用crontab)

```bash
# 编辑crontab
crontab -e

# 添加每日18:00自动生成并发布（无需人工确认）
0 18 * * * cd /path/to/autoDayReport && /usr/bin/python3 main.py auto
```

#### Windows (使用任务计划程序)

1. 打开"任务计划程序" (Task Scheduler)
2. 创建基本任务
3. 设置触发器为"每天"
4. 设置操作为"启动程序"
5. 程序路径填写Python解释器完整路径，例如：`C:\Python39\python.exe`
6. 参数填写：`main.py`
7. 起始于填写：程序所在目录的完整路径，例如：`C:\Users\YourName\Documents\自动化日报提交`

## 输出示例

### 1. 原始日报（提交清单）

日报会保存到 `reports/日报_YYYYMMDD.txt` 文件，内容格式如下：

```
# 工作日报 - 2026年01月26日

## 今日提交清单

============================================================
今日提交清单 - 2026年01月26日
============================================================

【张三】
------------------------------------------------------------
  仓库: project-a
    [abc1234] 2026-01-26 14:30:00 - 修复登录bug
    [def5678] 2026-01-26 16:20:00 - 添加新功能

【李四】
------------------------------------------------------------
  仓库: project-b
    [ghi9012] 2026-01-26 10:15:00 - 更新文档

============================================================
统计信息:
  总提交数: 3
  参与人员: 2
  涉及仓库: 2
============================================================
```

### 2. AI智能简报

简报会保存到 `reports/简报_YYYYMMDD.txt` 文件，由DeepSeek AI根据提交记录自动生成，格式符合系统要求：

```
*上午时间安排与工作内容
1. 优化证书关联关系的逻辑代码
2. 修复登录模块的bug，提升系统稳定性

*下午时间安排与工作内容
1. 完成变更管理优化方案的讨论和联调测试
2. 添加新的功能模块并完成代码审查

*今日计划的学习内容与进度
学习Spring Boot配置管理相关技术，已完成基础概念学习，正在实践应用
```

**智能特性：**
- **本人有提交**：根据本人提交记录（含完整提交描述体）生成详细工作内容
- **本人无提交，他人有提交**：根据他人提交记录，生成本人「协助、评审、联调」角色的简报，避免与同事日报雷同
- **全天无提交**：自动获取昨日记录，创造性改写为今日简报（换角度描述，避免内容重复）
- **自定义内容**：直接传入工作描述字符串，跳过 Git 记录生成简报
- **学习内容随机**：30% 概率生成相关技术学习内容，70% 概率输出「无」，更真实自然

## 跨平台兼容性说明

### 路径处理
- 程序使用 `os.path` 模块处理路径，自动适配不同操作系统的路径分隔符
- Windows路径（`C:\Users\...`）和Unix路径（`/home/...`）都能正确处理

### Git命令
- 程序使用 `shutil.which()` 自动检测Git命令位置
- Windows上会自动查找 `git.exe`，无需特殊配置
- 确保Git已安装并添加到系统PATH环境变量中

### 权限处理
- 程序包含异常处理，遇到无权限访问的目录会自动跳过并继续搜索
- Windows上某些系统目录（如 `AppData`）会被自动排除

## 注意事项

1. **搜索范围**: 程序会递归搜索指定目录，如果目录很大可能会花费较长时间。建议在 `config.py` 的 `GIT_SEARCH_PATHS` 中指定具体的项目目录，而不是搜索整个用户主目录。

2. **Git要求**: 确保Git已正确安装。可以通过以下命令检查：
   ```bash
   # macOS/Linux
   which git
   
   # Windows
   where git
   ```

3. **文件保存**: 
   - 日报文件保存在程序目录下的 `reports/` 文件夹中，按日期命名（格式：`日报_YYYYMMDD.txt`）
   - 简报文件同样保存在 `reports/` 文件夹中（格式：`简报_YYYYMMDD.txt`）

4. **编码支持**: 程序使用UTF-8编码保存文件，支持中文等非ASCII字符

5. **DeepSeek API**: 
   - 需要有效的DeepSeek API Key才能使用AI简报生成功能
   - 推荐使用环境变量 `DEEPSEEK_API_KEY` 配置，避免密钥泄露
   - API调用失败时，简报会显示错误信息，但不影响日报生成
   - 使用自定义内容模式（`--content`）时同样需要 DeepSeek API Key

6. **Playwright依赖**: 
   - 首次使用CRM自动发布功能时，需要安装Playwright浏览器驱动
   - 运行 `playwright install chromium` 安装（或程序会自动提示）
   - Windows用户可能需要额外安装系统依赖

7. **Windows用户**: 如果遇到"git不是内部或外部命令"错误，请确保：
   - Git已正确安装
   - Git的bin目录已添加到系统PATH环境变量
   - 重启命令行窗口或IDE使环境变量生效

8. **配置管理**: 
   - 所有配置项都集中在 `config.py` 中，修改配置后无需重启程序（下次运行生效）
   - 敏感信息（如API Key、密码）建议使用环境变量，不要直接写在配置文件中
   - 配置文件中的排除目录列表（`EXCLUDE_DIRS`）可以自定义，提高搜索效率

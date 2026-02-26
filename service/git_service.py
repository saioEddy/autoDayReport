"""
Git服务层 - 处理Git仓库相关的业务逻辑（跨平台兼容）
支持两种模式：
  local  - 扫描本地已 clone 的仓库
  remote - 通过 GitLab REST API v4 直接拉取服务器提交，无需本地 clone
"""
import os
import sys
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode, quote
from urllib.error import HTTPError, URLError
import json

from config import EXCLUDE_DIRS


class GitService:
    """Git仓库服务类"""
    
    def __init__(self):
        self.git_repos = []
    
    def discover_git_repos(self, root_path: str = None) -> List[str]:
        """
        自动发现本地Git仓库（跨平台兼容）
        
        Args:
            root_path: 搜索的根路径，默认为用户主目录
            
        Returns:
            Git仓库路径列表
        """
        if root_path is None:
            root_path = os.path.expanduser("~")
        
        # 确保路径是绝对路径，跨平台兼容
        root_path = os.path.abspath(os.path.expanduser(root_path))
        
        if not os.path.exists(root_path):
            print(f"警告: 搜索路径不存在: {root_path}")
            return []
        
        if not os.path.isdir(root_path):
            print(f"警告: 搜索路径不是目录: {root_path}")
            return []
        
        git_repos = []
        
        # 递归搜索.git目录，添加异常处理以处理权限问题（Windows常见）
        try:
            for root, dirs, files in os.walk(root_path):
                # 先检查当前目录是否有.git目录（在过滤之前检查）
                if '.git' in dirs:
                    # 使用os.path.normpath确保路径格式正确（Windows兼容）
                    repo_path = os.path.normpath(root)
                    git_repos.append(repo_path)
                    # 找到.git后不再深入搜索该目录，从dirs中移除
                    dirs.remove('.git')
                
                # 使用 config.EXCLUDE_DIRS 排除非项目目录；Windows 追加平台特定目录
                exclude_dirs = list(EXCLUDE_DIRS)
                if sys.platform == "win32":
                    exclude_dirs.extend(["AppData", "Application Data", "Local Settings"])
                dirs[:] = [d for d in dirs if d not in exclude_dirs]
        except PermissionError as e:
            print(f"警告: 访问目录时权限不足: {str(e)}")
        except Exception as e:
            print(f"警告: 搜索Git仓库时出错: {str(e)}")
        
        self.git_repos = git_repos
        return git_repos
    
    def get_commits_by_date(self, repo_path: str, target_date: datetime = None) -> List[Dict]:
        """
        获取指定仓库指定日期的所有提交记录
        
        Args:
            repo_path: Git仓库路径
            target_date: 目标日期，默认为今天
            
        Returns:
            提交记录列表，每个记录包含：author, date, message, hash
        """
        if not os.path.exists(os.path.join(repo_path, '.git')):
            return []
        
        # 如果未指定日期，使用今天
        if target_date is None:
            target_date = datetime.now()
        
        # 获取目标日期的开始和结束时间
        target_day = target_date.date()
        start_time = datetime.combine(target_day, datetime.min.time())
        end_time = datetime.combine(target_day, datetime.max.time())
        
        # 格式化时间用于git log查询
        start_str = start_time.strftime('%Y-%m-%d 00:00:00')
        end_str = end_time.strftime('%Y-%m-%d 23:59:59')
        
        commits = []
        
        try:
            # 切换到仓库目录（使用绝对路径，跨平台兼容）
            original_dir = os.getcwd()
            repo_path_abs = os.path.abspath(repo_path)
            os.chdir(repo_path_abs)
            
            # 执行git log命令，获取指定日期所有提交
            # 使用--all获取所有分支的提交
            # 跨平台检测git命令位置
            git_cmd = shutil.which('git') or 'git'  # 优先使用which找到的git路径，找不到则使用'git'
            
            # 旧的格式(只有标题): '--pretty=format:%H|%an|%ad|%s',
            # 新的格式(标题+完整提交体): 使用 %s 获取标题, %b 获取提交体
            # 使用特殊分隔符 ||BODY|| 来区分标题和提交体
            cmd = [git_cmd, 'log']
            cmd.extend([
                '--all',
                '--since', start_str,
                '--until', end_str,
                '--pretty=format:%H|%an|%ad|%s||BODY||%b||END||',
                '--date=format:%Y-%m-%d %H:%M:%S'
            ])
            
            # Windows上设置shell=False，但需要处理可能的编码问题
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                shell=False,  # 跨平台兼容，不使用shell
                encoding='utf-8',  # 明确指定编码
                errors='replace'  # 编码错误时替换而不是抛出异常
            )
            
            # 旧的解析逻辑(只有标题):
            # if result.returncode == 0 and result.stdout.strip():
            #     for line in result.stdout.strip().split('\n'):
            #         if '|' in line:
            #             parts = line.split('|', 3)
            #             if len(parts) >= 4:
            #                 commits.append({
            #                     'hash': parts[0][:7],  # 短hash
            #                     'author': parts[1],
            #                     'date': parts[2],
            #                     'message': parts[3],
            #                     'repo': os.path.basename(repo_path)
            #                 })
            
            # 新的解析逻辑(标题+提交体):
            if result.returncode == 0 and result.stdout.strip():
                # 按 ||END|| 分隔每个提交
                commit_blocks = result.stdout.strip().split('||END||')
                for block in commit_blocks:
                    block = block.strip()
                    if not block or '||BODY||' not in block:
                        continue
                    
                    # 分离基本信息和提交体
                    if '||BODY||' in block:
                        basic_info, body = block.split('||BODY||', 1)
                        body = body.strip()
                    else:
                        basic_info = block
                        body = ''
                    
                    # 解析基本信息: hash|author|date|subject
                    if '|' in basic_info:
                        parts = basic_info.split('|', 3)
                        if len(parts) >= 4:
                            commits.append({
                                'hash': parts[0][:7],  # 短hash
                                'author': parts[1],
                                'date': parts[2],
                                'message': parts[3],  # 提交标题
                                'body': body,  # 提交体(完整描述)
                                'repo': os.path.basename(repo_path)
                            })
            
            os.chdir(original_dir)
            
        except subprocess.TimeoutExpired:
            print(f"警告: 获取仓库 {repo_path} 的提交记录超时")
        except Exception as e:
            print(f"错误: 获取仓库 {repo_path} 的提交记录失败: {str(e)}")
        
        return commits
    
    def get_today_commits(self, repo_path: str) -> List[Dict]:
        """
        获取指定仓库今日的所有提交记录
        
        Args:
            repo_path: Git仓库路径
            
        Returns:
            提交记录列表，每个记录包含：author, date, message, hash
        """
        return self.get_commits_by_date(repo_path, datetime.now())
    
    def get_all_commits_by_date(self, repo_paths: List[str] = None, target_date: datetime = None) -> List[Dict]:
        """
        获取所有指定仓库指定日期的提交记录
        
        Args:
            repo_paths: Git仓库路径列表，如果为None则使用discover_git_repos的结果
            target_date: 目标日期，默认为今天
            
        Returns:
            所有仓库指定日期的提交记录列表
        """
        if repo_paths is None:
            repo_paths = self.git_repos if self.git_repos else self.discover_git_repos()
        
        all_commits = []
        
        for repo_path in repo_paths:
            commits = self.get_commits_by_date(repo_path, target_date)
            all_commits.extend(commits)
        
        # 按时间排序
        all_commits.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        return all_commits
    
    def get_all_today_commits(self, repo_paths: List[str] = None) -> List[Dict]:
        """
        获取所有指定仓库今日的提交记录
        
        Args:
            repo_paths: Git仓库路径列表，如果为None则使用discover_git_repos的结果
            
        Returns:
            所有仓库今日的提交记录列表
        """
        return self.get_all_commits_by_date(repo_paths, datetime.now())
    
    def get_all_yesterday_commits(self, repo_paths: List[str] = None) -> List[Dict]:
        """
        获取所有指定仓库昨天的提交记录
        
        Args:
            repo_paths: Git仓库路径列表，如果为None则使用discover_git_repos的结果
            
        Returns:
            所有仓库昨天的提交记录列表
        """
        yesterday = datetime.now() - timedelta(days=1)
        return self.get_all_commits_by_date(repo_paths, yesterday)
    
    def get_current_author(self, repo_path: str = None) -> str:
        """
        获取本人 Git 用户名（user.name），用于区分本人/他人提交。
        优先使用指定仓库的 local 配置，否则使用 global。
        
        Args:
            repo_path: 可选，某仓库路径。若提供则优先读该仓库的 user.name
            
        Returns:
            当前用户 Git 名称，获取失败时返回空字符串
        """
        git_cmd = shutil.which('git') or 'git'
        cmd = [git_cmd, 'config', 'user.name']
        cwd = None
        if repo_path and os.path.exists(os.path.join(os.path.abspath(repo_path), '.git')):
            # 在指定仓库下读 local 配置
            cwd = os.path.abspath(repo_path)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                shell=False,
                encoding='utf-8',
                errors='replace',
                cwd=cwd,
            )
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
            # local 无配置时尝试 global
            if cwd:
                global_cmd = [git_cmd, 'config', '--global', 'user.name']
                r2 = subprocess.run(
                    global_cmd,
                    capture_output=True,
                    text=True,
                    timeout=10,
                    shell=False,
                    encoding='utf-8',
                    errors='replace',
                )
                if r2.returncode == 0 and r2.stdout.strip():
                    return r2.stdout.strip()
        except Exception as e:
            print(f"警告: 获取 Git user.name 失败: {e}")
        return ''

    # ------------------------------------------------------------------ #
    #  GitLab Remote API 模式（无需本地 clone）                             #
    # ------------------------------------------------------------------ #

    def _gitlab_request(self, gitlab_url: str, token: str, path: str, params: dict = None) -> Optional[dict]:
        """
        发起一次 GitLab API GET 请求，返回解析后的 JSON 数据。
        失败时返回 None。
        """
        url = f"{gitlab_url.rstrip('/')}/api/v4{path}"
        if params:
            url += '?' + urlencode(params)
        req = Request(url, headers={'PRIVATE-TOKEN': token})
        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except HTTPError as e:
            print(f"GitLab API 请求失败 [{e.code}]: {url}")
        except URLError as e:
            print(f"GitLab API 连接失败: {e.reason}")
        except Exception as e:
            print(f"GitLab API 异常: {e}")
        return None

    def _gitlab_paged_request(self, gitlab_url: str, token: str, path: str, params: dict = None) -> List[dict]:
        """
        自动翻页，返回所有页合并的列表。
        """
        all_items = []
        page = 1
        base_params = dict(params or {})
        base_params['per_page'] = 100
        while True:
            base_params['page'] = page
            items = self._gitlab_request(gitlab_url, token, path, base_params)
            if not items:
                break
            all_items.extend(items)
            if len(items) < 100:
                break
            page += 1
        return all_items

    def _get_active_project_ids(self, gitlab_url: str, token: str, day) -> set:
        """
        用两路并行策略确定「当天有提交活动」的项目 ID 集合，避免遍历全部项目：

        路由 A：/events?action=pushed  → 自己今天 push 过的项目
        路由 B：/projects?last_activity_after=今天  → 今天有任意活动的成员项目

        两者取并集，通常只有个位数项目，远小于全量 109 个。
        """
        from datetime import timedelta
        after  = (day - timedelta(days=1)).strftime('%Y-%m-%d')
        before = (day + timedelta(days=1)).strftime('%Y-%m-%d')

        # 路由 A：自己的 push events
        my_events = self._gitlab_paged_request(gitlab_url, token, '/events', {
            'action': 'pushed',
            'after':  after,
            'before': before,
        })
        event_ids = {e['project_id'] for e in my_events}

        # 路由 B：last_activity_after 过滤的成员项目
        recent = self._gitlab_paged_request(gitlab_url, token, '/projects', {
            'membership': 'true',
            'simple': 'true',
            'order_by': 'last_activity_at',
            'sort': 'desc',
            'last_activity_after': f"{day}T00:00:00Z",
            'per_page': 50,
        })
        recent_ids = {p['id'] for p in recent}

        return event_ids | recent_ids

    def get_gitlab_today_commits(
        self,
        gitlab_url: str,
        token: str,
        target_date: datetime = None,
        author_username: str = None,
    ) -> List[Dict]:
        """
        通过 GitLab API 获取指定日期内所有可见项目上的提交。

        优化策略：先用 /events + /projects?last_activity_after 定位
        今天有活动的项目（通常只有个位数），再只查这些项目的 commits，
        避免遍历全部 100+ 个项目。

        Args:
            gitlab_url:      GitLab 服务器地址，如 http://10.57.254.12:9999
            token:           Personal Access Token（需要 read_api 或 api 权限）
            target_date:     目标日期，默认今天
            author_username: 只筛选该用户名的提交；None 则返回所有用户

        Returns:
            提交记录列表，字段与本地模式保持一致：
            hash, author, date, message, body, repo
        """
        if target_date is None:
            target_date = datetime.now()

        day   = target_date.date()
        since = f"{day}T00:00:00+08:00"
        until = f"{day}T23:59:59+08:00"

        # 1. 获取当前登录用户信息
        me = self._gitlab_request(gitlab_url, token, '/user')
        if not me:
            print("警告: 无法获取 GitLab 当前用户信息，请检查 Token 是否有效")
            return []
        me_name     = me.get('name', '')
        me_username = me.get('username', '')
        print(f"GitLab 当前用户: {me_name} (@{me_username})")

        # 2. 定位今天有活动的项目（两路策略，通常只有个位数）
        project_ids = self._get_active_project_ids(gitlab_url, token, day)
        print(f"今天有活动的项目数: {len(project_ids)}，正在获取提交...")

        all_commits: List[Dict] = []

        # 3. 只查活跃项目的提交
        for proj_id in project_ids:
            proj = self._gitlab_request(gitlab_url, token, f'/projects/{proj_id}')
            proj_name = proj.get('name', str(proj_id)) if proj else str(proj_id)
            proj_path = proj.get('path_with_namespace', proj_name) if proj else proj_name

            params: dict = {'since': since, 'until': until, 'all': 'true'}
            commits_raw = self._gitlab_paged_request(
                gitlab_url, token,
                f'/projects/{proj_id}/repository/commits',
                params,
            )

            for c in commits_raw:
                committed_dt = c.get('committed_date', '') or c.get('created_at', '')
                try:
                    dt = datetime.fromisoformat(committed_dt.replace('Z', '+00:00'))
                    date_str = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    date_str = committed_dt

                all_commits.append({
                    'hash':      (c.get('id') or '')[:7],
                    'author':    c.get('author_name', ''),
                    'date':      date_str,
                    'message':   c.get('title', ''),
                    'body':      c.get('message', '').replace(c.get('title', ''), '', 1).strip(),
                    'repo':      proj_name,
                    'repo_path': proj_path,
                })

        # 4. 按时间倒序
        all_commits.sort(key=lambda x: x.get('date', ''), reverse=True)
        return all_commits

    def get_gitlab_current_author(self, gitlab_url: str, token: str) -> str:
        """
        通过 GitLab API 获取当前登录用户的 name（用于简报区分本人/他人）。
        """
        me = self._gitlab_request(gitlab_url, token, '/user')
        if me:
            return me.get('name', '')
        return ''

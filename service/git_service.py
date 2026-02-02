"""
Git服务层 - 处理Git仓库相关的业务逻辑（跨平台兼容）
"""
import os
import sys
import subprocess
import shutil
from datetime import datetime, timedelta
from typing import List, Dict
from pathlib import Path

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

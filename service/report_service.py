"""
日报生成服务层 - 处理日报内容生成的业务逻辑
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict


class ReportService:
    """日报生成服务类"""
    
    def __init__(self):
        pass

    def _format_commits_for_prompt(self, commits: List[Dict]) -> str:
        """将提交列表格式化为给 AI 的文本"""
        if not commits:
            return "（无）"
        lines = []
        for c in commits:
            repo = c.get("repo", "")
            date = c.get("date", "")
            author = c.get("author", "")
            msg = c.get("message", "")
            lines.append(f"- [{repo}] {date} {author}: {msg}")
        return "\n".join(lines)
    
    def generate_commit_list(self, commits: List[Dict]) -> str:
        """
        生成今日提交清单
        
        Args:
            commits: 提交记录列表
            
        Returns:
            格式化的提交清单字符串
        """
        if not commits:
            return "今日无提交记录"
        
        # 按作者分组
        commits_by_author = defaultdict(list)
        for commit in commits:
            author = commit.get('author', '未知')
            commits_by_author[author].append(commit)
        
        # 生成清单内容
        report_lines = []
        report_lines.append("=" * 60)
        report_lines.append(f"今日提交清单 - {datetime.now().strftime('%Y年%m月%d日')}")
        report_lines.append("=" * 60)
        report_lines.append("")
        
        # 按作者分组显示
        for author, author_commits in sorted(commits_by_author.items()):
            report_lines.append(f"【{author}】")
            report_lines.append("-" * 60)
            
            # 按仓库分组
            commits_by_repo = defaultdict(list)
            for commit in author_commits:
                repo = commit.get('repo', '未知仓库')
                commits_by_repo[repo].append(commit)
            
            for repo, repo_commits in sorted(commits_by_repo.items()):
                report_lines.append(f"  仓库: {repo}")
                for commit in repo_commits:
                    hash_val = commit.get('hash', '')
                    message = commit.get('message', '')
                    time = commit.get('date', '')
                    report_lines.append(f"    [{hash_val}] {time} - {message}")
                report_lines.append("")
            
            report_lines.append("")
        
        # 统计信息
        report_lines.append("=" * 60)
        report_lines.append("统计信息:")
        report_lines.append(f"  总提交数: {len(commits)}")
        report_lines.append(f"  参与人员: {len(commits_by_author)}")
        report_lines.append(f"  涉及仓库: {len(set(c.get('repo', '') for c in commits))}")
        report_lines.append("=" * 60)
        
        return "\n".join(report_lines)
    
    def generate_daily_report(self, commits: List[Dict]) -> str:
        """
        生成完整的日报内容
        
        Args:
            commits: 提交记录列表
            
        Returns:
            完整的日报内容字符串
        """
        report_content = []
        
        # 日报标题
        report_content.append(f"# 工作日报 - {datetime.now().strftime('%Y年%m月%d日')}")
        report_content.append("")
        
        # 今日提交清单
        report_content.append("## 今日提交清单")
        report_content.append("")
        report_content.append(self.generate_commit_list(commits))
        report_content.append("")
        
        return "\n".join(report_content)
    
    def save_report_to_file(self, report_content: str, file_path: str = None) -> str:
        """
        保存日报到文件
        
        Args:
            report_content: 日报内容
            file_path: 保存路径，如果为None则使用默认路径
            
        Returns:
            保存的文件路径
        """
        if file_path is None:
            # 默认保存到当前目录的reports文件夹（跨平台兼容）
            import os
            # 使用os.path.join确保跨平台路径正确
            reports_dir = os.path.join(os.getcwd(), 'reports')
            # 使用os.makedirs的exist_ok参数，跨平台兼容
            os.makedirs(reports_dir, exist_ok=True)
            
            filename = f"日报_{datetime.now().strftime('%Y%m%d')}.txt"
            file_path = os.path.join(reports_dir, filename)
        
        # 确保目录存在（跨平台兼容）
        import os
        file_dir = os.path.dirname(file_path)
        if file_dir:  # 如果路径包含目录部分
            os.makedirs(file_dir, exist_ok=True)
        
        # 保存文件
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return file_path

    def generate_brief(
        self,
        commits: List[Dict],
        my_author: str,
        deepseek_service,
    ) -> str:
        """
        根据今日提交生成本人工作简报。
        1. 若本人有提交：根据本人提交记录润色成简报；
        2. 若本人无提交：根据他人提交记录，生成本人「协助他人工作」的简报，且不与他人雷同。
        
        Args:
            commits: 今日全部提交记录
            my_author: 本人 Git user.name
            deepseek_service: DeepSeekService 实例
            
        Returns:
            简报正文；无提交时返回说明文字。
        """
        my_commits = [c for c in commits if c.get("author") == my_author]
        others_commits = [c for c in commits if c.get("author") != my_author]

        if not commits:
            return "今日无提交记录，无法生成简报。"

        if my_commits:
            system = (
                "你是工作日报助手。请根据本人今日的 Git 提交记录，润色成一份简洁、专业的工作简报。"
                "只输出简报正文，不要加「简报」、日期等标题前缀。"
            )
            user = "本人今日提交如下：\n" + self._format_commits_for_prompt(my_commits)
        else:
            system = (
                "你是工作日报助手。本人今日无 Git 提交。请根据以下「他人的」今日提交记录，"
                "生成本人今日工作简报。简报须体现本人「协助、支持他人工作」的角色，"
                "用概括性语言说明协助了哪些方面（如评审、联调、支持、协作等），"
                "不要直接照搬他人的提交内容，避免与同事的日报雷同。只输出简报正文，不要加标题、日期等前缀。"
            )
            user = "他人今日提交如下：\n" + self._format_commits_for_prompt(others_commits)

        try:
            return deepseek_service.chat(system=system, user=user, max_tokens=1024)
        except Exception as e:
            return f"[简报生成失败] {e!r}"

    def save_brief_to_file(self, brief_content: str, file_path: Optional[str] = None) -> str:
        """
        保存简报到文件。
        
        Args:
            brief_content: 简报内容
            file_path: 保存路径，None 则使用 reports/简报_YYYYMMDD.txt
            
        Returns:
            保存的文件路径
        """
        if file_path is None:
            reports_dir = os.path.join(os.getcwd(), "reports")
            os.makedirs(reports_dir, exist_ok=True)
            filename = f"简报_{datetime.now().strftime('%Y%m%d')}.txt"
            file_path = os.path.join(reports_dir, filename)
        file_dir = os.path.dirname(file_path)
        if file_dir:
            os.makedirs(file_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(brief_content)
        return file_path

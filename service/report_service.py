"""
日报生成服务层 - 处理日报内容生成的业务逻辑
"""
import os
from datetime import datetime
from typing import List, Dict, Optional
from collections import defaultdict
from config import BRIEF_SYSTEM_MODIFIER, REPORT_SAVE_DIR, REPORT_FILE_FORMAT, BRIEF_FILE_FORMAT


class ReportService:
    """日报生成服务类"""
    
    def __init__(self):
        pass

    def _format_commits_for_prompt(self, commits: List[Dict]) -> str:
        """将提交列表格式化为给 AI 的文本"""
        if not commits:
            return "（无）"
        # 旧的格式化方式(只有标题):
        # lines = []
        # for c in commits:
        #     repo = c.get("repo", "")
        #     date = c.get("date", "")
        #     author = c.get("author", "")
        #     msg = c.get("message", "")
        #     lines.append(f"- [{repo}] {date} {author}: {msg}")
        # return "\n".join(lines)
        
        # 新的格式化方式(标题+完整提交体):
        lines = []
        for c in commits:
            repo = c.get("repo", "")
            date = c.get("date", "")
            author = c.get("author", "")
            msg = c.get("message", "")
            body = c.get("body", "")
            
            # 先添加标题行
            lines.append(f"- [{repo}] {date} {author}: {msg}")
            # 如果有提交体,缩进显示
            if body:
                body_lines = body.split('\n')
                for body_line in body_lines:
                    if body_line.strip():
                        lines.append(f"  {body_line}")
        return "\n".join(lines)
    
    def _generate_brief_from_yesterday(
        self,
        yesterday_commits: List[Dict],
        my_author: str,
        deepseek_service,
    ) -> str:
        """
        当今日无任何提交时，基于昨天的提交记录创造性生成今日简报。
        重点：内容要与昨天不同，要有创造性改写，避免被发现是复制。
        
        Args:
            yesterday_commits: 昨天的提交记录
            my_author: 本人 Git user.name
            deepseek_service: DeepSeekService 实例
            
        Returns:
            创造性改写的简报内容
        """
        # 统一的格式要求
        format_instruction = (
            "请严格按照以下格式输出，只包含三个字段，不要添加任何其他内容：\n\n"
            "*上午时间安排与工作内容\n"
            "[这里填写上午的工作内容，每条不要带时间，直接写内容。例如：\n"
            " 1. 优化证书关联关系的逻辑代码\n"
            " 2. 完成变更管理优化方案的讨论和联调测试]\n\n"
            "*下午时间安排与工作内容\n"
            "[这里填写下午的工作内容，每条不要带时间，直接写内容。例如：\n"
            " 1. 完成变更管理优化方案的讨论和联调测试\n"
            " 2. 优化证书关联关系的逻辑代码]\n\n"
            "*今日计划的学习内容与进度\n"
            "[这里填写今日计划的学习内容和学习进度，例如：学习Spring Boot配置管理相关技术，已完成基础概念学习]\n\n"
            "注意：\n"
            "1. 上午和下午的工作内容要基于提交记录合理分配，但每条内容前不要加时间（禁止 10:20-12:00：、09:00-12:00： 等格式），只写序号和内容，如「1. xxx」「2. xxx」\n"
            "2. 学习内容要合理，可以基于工作内容推断相关技术学习\n"
            "3. 只输出这三个字段的内容，不要添加标题、日期等前缀\n"
            "4. 今日计划的学习内容与进度随机生成,有时生成有时候不生成,占比百分之30生成,百分之70不生成,如果本次不生成,生成一个无\n"
        )
        
        system = (
            "你是工作日报助手。今天团队没有任何代码提交，但你需要基于昨天的提交记录生成今日的工作简报。\n\n"
            "**重要要求：**\n"
            "1. 不能直接复制昨天的工作内容，必须进行创造性改写\n"
            "2. 可以将昨天的工作描述为「持续优化」「深度测试」「问题修复」「代码重构」「性能调优」等延续性工作\n"
            "3. 改变工作的描述角度，例如昨天写「创建XX功能」，今天可以写「完善XX功能的边界处理」「优化XX功能的性能」等\n"
            "4. 调整上午下午的工作内容分配，不要和昨天完全一致\n"
            "5. 学习内容要换一个相关但不同的技术点\n"
            "6. 使用不同的技术细节描述，让内容看起来是今天新做的工作\n\n"
            f"{BRIEF_SYSTEM_MODIFIER}\n\n"
            + format_instruction
        )
        
        user = (
            "昨天的提交记录如下，请基于这些内容创造性地生成今日的工作简报，"
            "要体现工作的延续性，但不能与昨天的描述完全相同：\n\n"
            + self._format_commits_for_prompt(yesterday_commits)
        )
        
        try:
            return deepseek_service.chat(system=system, user=user, max_tokens=1024)
        except Exception as e:
            return f"[基于昨日提交生成简报失败] {e!r}"
    
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
                    body = commit.get('body', '')
                    time = commit.get('date', '')
                    
                    # 旧的显示方式(只有标题):
                    # report_lines.append(f"    [{hash_val}] {time} - {message}")
                    
                    # 新的显示方式(标题+完整提交体):
                    report_lines.append(f"    [{hash_val}] {time} - {message}")
                    # 如果有提交体,缩进显示
                    if body:
                        # 将提交体按行分割,每行前面加上缩进
                        body_lines = body.split('\n')
                        for body_line in body_lines:
                            if body_line.strip():  # 跳过空行
                                report_lines.append(f"      {body_line}")
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
            reports_dir = REPORT_SAVE_DIR
            os.makedirs(reports_dir, exist_ok=True)
            filename = REPORT_FILE_FORMAT.format(date=datetime.now().strftime("%Y%m%d"))
            file_path = os.path.join(reports_dir, filename)
        
        # 确保目录存在（跨平台兼容）
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
        yesterday_commits: List[Dict] = None,
    ) -> str:
        """
        根据今日提交生成本人工作简报，格式符合系统要求。
        1. 若本人有提交：根据本人提交记录生成简报；
        2. 若本人无提交但他人有提交：根据他人提交记录，生成本人「协助他人工作」的简报，且不与他人雷同；
        3. 若今日完全无提交且提供了昨天的提交：基于昨天的提交记录创造性生成简报，但不能与昨天完全相同。
        
        Args:
            commits: 今日全部提交记录
            my_author: 本人 Git user.name
            deepseek_service: DeepSeekService 实例
            yesterday_commits: 昨天的提交记录（可选），用于今日无提交时参考
            
        Returns:
            简报正文，包含三个字段：上午工作内容、下午工作内容、今日计划学习内容与进度；无提交时返回说明文字。
        """
        my_commits = [c for c in commits if c.get("author") == my_author]
        others_commits = [c for c in commits if c.get("author") != my_author]

        # 如果今日完全无提交，尝试使用昨天的提交记录进行创造性生成
        if not commits and yesterday_commits:
            print("今日无任何提交记录，将基于昨天的提交内容进行创造性改写...")
            return self._generate_brief_from_yesterday(yesterday_commits, my_author, deepseek_service)
        
        if not commits:
            return "今日无提交记录，无法生成简报。"

        # 统一的格式要求（当前不输出时间前缀，如 10:20-12:00：）
        format_instruction = (
            "请严格按照以下格式输出，只包含三个字段，不要添加任何其他内容：\n\n"
            "*上午时间安排与工作内容\n"
            "[这里填写上午的工作内容，每条不要带时间，直接写内容。例如：\n"
            " 1. 优化证书关联关系的逻辑代码\n"
            " 2. 完成变更管理优化方案的讨论和联调测试]\n\n"
            "*下午时间安排与工作内容\n"
            "[这里填写下午的工作内容，每条不要带时间，直接写内容。例如：\n"
            " 1. 完成变更管理优化方案的讨论和联调测试\n"
            " 2. 优化证书关联关系的逻辑代码]\n\n"
            "*今日计划的学习内容与进度\n"
            "[这里填写今日计划的学习内容和学习进度，例如：学习Spring Boot配置管理相关技术，已完成基础概念学习]\n\n"
            "注意：\n"
            "1. 上午和下午的工作内容要基于提交记录合理分配，但每条内容前不要加时间（禁止 10:20-12:00：、09:00-12:00： 等格式），只写序号和内容，如「1. xxx」「2. xxx」\n"
            "2. 学习内容要合理，可以基于工作内容推断相关技术学习\n"
            "3. 只输出这三个字段的内容，不要添加标题、日期等前缀\n"
            "4. 今日计划的学习内容与进度随机生成,有时生成有时候不生成,占比百分之30生成,百分之70不生成,如果本次不生成,生成一个无\n"
        )

        if my_commits:
            system = (
                "你是工作日报助手。请根据本人今日的 Git 提交记录，生成符合系统格式要求的工作简报。\n\n"
                f"{BRIEF_SYSTEM_MODIFIER}\n\n"
                + format_instruction
            )
            user = "本人今日提交如下：\n" + self._format_commits_for_prompt(my_commits)
        else:
            system = (
                "你是工作日报助手。本人今日无 Git 提交。请根据以下「他人的」今日提交记录，"
                "生成本人今日工作简报。简报须体现本人「协助、支持他人工作」的角色，"
                "用概括性语言说明协助了哪些方面（如评审、联调、支持、协作等），"
                "不要直接照搬他人的提交内容，避免与同事的日报雷同。\n\n"
                f"{BRIEF_SYSTEM_MODIFIER}\n\n"
                + format_instruction
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
            reports_dir = REPORT_SAVE_DIR
            os.makedirs(reports_dir, exist_ok=True)
            filename = BRIEF_FILE_FORMAT.format(date=datetime.now().strftime("%Y%m%d"))
            file_path = os.path.join(reports_dir, filename)
        file_dir = os.path.dirname(file_path)
        if file_dir:
            os.makedirs(file_dir, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(brief_content)
        return file_path

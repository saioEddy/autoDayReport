"""
日报自动提交程序主入口（跨平台兼容）
"""
import os
import sys
from datetime import datetime
from service.git_service import GitService
from service.report_service import ReportService
from service.deepseek_service import DeepSeekService
from service.crm_service import CRMService
from config import (
    CRM_URL,
    CRM_USERNAME,
    CRM_PASSWORD,
    GIT_REPO_SEARCH_PATH,
    GIT_SEARCH_PATHS,
)


def main():
    """主函数"""
    print(f"开始生成日报 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # 初始化服务
    git_service = GitService()
    report_service = ReportService()
    
    # 1. 自动发现Git仓库
    print("正在搜索本地Git仓库...")
    # 优先使用环境变量 GIT_REPO_SEARCH_PATH；否则使用 config.GIT_SEARCH_PATHS
    if "GIT_REPO_SEARCH_PATH" in os.environ:
        search_paths = [os.environ["GIT_REPO_SEARCH_PATH"]]
    else:
        possible_paths = list(GIT_SEARCH_PATHS)
        if sys.platform == "win32":
            win_docs = os.path.join(os.path.expanduser("~"), "Documents")
            if os.path.exists(win_docs):
                possible_paths.insert(0, win_docs)
            win_projects = os.path.join(os.path.expanduser("~"), "Documents", "Projects")
            if os.path.exists(win_projects):
                possible_paths.insert(0, win_projects)
        search_paths = []
        for path in possible_paths:
            expanded = os.path.abspath(os.path.expanduser(path))
            if os.path.exists(expanded) and os.path.isdir(expanded):
                search_paths.append(expanded)
    if not search_paths:
        search_paths = [os.path.abspath(os.path.expanduser(GIT_REPO_SEARCH_PATH))]
    
    # 显示所有搜索路径
    print(f"搜索路径 ({len(search_paths)} 个):")
    for path in search_paths:
        print(f"  - {path}")
    
    # 在所有路径中搜索Git仓库
    all_git_repos = []
    for search_path in search_paths:
        repos = git_service.discover_git_repos(search_path)
        all_git_repos.extend(repos)
        if repos:
            print(f"  在 {search_path} 中发现 {len(repos)} 个Git仓库")
    
    # 去重（避免同一个仓库被重复添加）
    git_repos = list(dict.fromkeys(all_git_repos))  # 保持顺序的去重方法
    print(f"\n总共发现 {len(git_repos)} 个Git仓库")
    
    if not git_repos:
        print("警告: 未发现任何Git仓库")
        return
    
    # 2. 获取今日所有提交记录
    print("正在获取今日提交记录...")
    today_commits = git_service.get_all_today_commits(git_repos)
    print(f"今日共有 {len(today_commits)} 条提交记录")
    
    # 2.5 如果今日无提交，获取昨天的提交记录作为备用
    yesterday_commits = []
    if not today_commits:
        print("今日无提交记录，正在获取昨天的提交记录作为参考...")
        yesterday_commits = git_service.get_all_yesterday_commits(git_repos)
        print(f"昨天共有 {len(yesterday_commits)} 条提交记录")
    
    # 3. 生成日报内容
    print("正在生成日报内容...")
    report_content = report_service.generate_daily_report(today_commits)
    
    # 4. 保存日报到文件
    report_path = report_service.save_report_to_file(report_content)
    print(f"日报已保存到: {report_path}")
    
    # 5. 打印日报内容到控制台
    print("\n" + "=" * 60)
    print("日报内容预览:")
    print("=" * 60)
    print(report_content)
    print("=" * 60)
    
    # 6. 生成本人简报（DeepSeek 润色）
    print("\n正在生成本人简报（DeepSeek）...")
    my_author = git_service.get_current_author(git_repos[0] if git_repos else None)
    if not my_author:
        print("警告: 未获取到 Git user.name，将无法区分本人/他人提交；简报按「无本人提交」处理。")
    deepseek_service = DeepSeekService()
    brief = report_service.generate_brief(
        today_commits, 
        my_author or "", 
        deepseek_service,
        yesterday_commits=yesterday_commits if yesterday_commits else None
    )
    brief_path = report_service.save_brief_to_file(brief)
    print(f"简报已保存到: {brief_path}")
    print("\n" + "-" * 60)
    print("简报预览:")
    print("-" * 60)
    print(brief)
    print("-" * 60)
    
    print(f"\n日报生成完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 7. 自动发布到 CRM 系统（可选）
    print("\n" + "=" * 60)
    print("是否要自动发布到 CRM 系统? (y/n): ", end="")
    choice = input().strip().lower()
    
    if choice == 'y':
        print("\n正在登录 CRM 系统...")
        crm_service = CRMService(CRM_URL, CRM_USERNAME, CRM_PASSWORD)
        
        try:
            if crm_service.login():
                print("✓ CRM 登录成功")
                print("\n正在发布日报...")
                if crm_service.publish_report(brief):
                    print("\n" + "=" * 60)
                    print("✓ 日报发布成功！")
                    print("=" * 60)
                else:
                    print("\n" + "=" * 60)
                    print("✗ 日报发布失败")
                    print("=" * 60)
            else:
                print("\n" + "=" * 60)
                print("✗ CRM 登录失败")
                print("=" * 60)
        except Exception as e:
            print(f"\n✗ CRM 发布过程出错: {e}")
            import traceback
            traceback.print_exc()
        finally:
            crm_service.close()
    else:
        print("跳过 CRM 自动发布")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"程序执行出错: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

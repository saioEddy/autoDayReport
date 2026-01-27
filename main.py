"""
日报自动提交程序主入口（跨平台兼容）
"""
import os
import sys
from datetime import datetime
from service.git_service import GitService
from service.report_service import ReportService
from service.deepseek_service import DeepSeekService
# from service.crm_service import CRMService
# from config import CRM_URL, CRM_USERNAME, CRM_PASSWORD


def main():
    """主函数"""
    print(f"开始生成日报 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("-" * 60)
    
    # 初始化服务
    git_service = GitService()
    report_service = ReportService()
    
    # 1. 自动发现Git仓库
    print("正在搜索本地Git仓库...")
    # 跨平台兼容的默认路径选择
    # 优先使用环境变量，其次尝试多个常见的项目目录（同时搜索多个路径）
    if 'GIT_REPO_SEARCH_PATH' in os.environ:
        # 如果设置了环境变量，只搜索指定的路径
        search_paths = [os.environ['GIT_REPO_SEARCH_PATH']]
    else:
        # 尝试多个常见的项目目录（跨平台）
        possible_paths = [
            #os.path.expanduser("~/Documents/开发代码"),  # macOS/Linux常见路径 
            os.path.expanduser("~/Desktop/vankun/code"),  
            # os.path.expanduser("~/Projects"),            # macOS常见项目目录
            # os.path.expanduser("~/code"),                # 常见代码目录
            # os.path.expanduser("~"),                     # 用户主目录（最后备选）
        ]
        
        # Windows特定路径
        if sys.platform == 'win32':
            # Windows上Documents路径
            win_docs = os.path.join(os.path.expanduser("~"), "Documents")
            if os.path.exists(win_docs):
                possible_paths.insert(0, win_docs)
            # Windows上常见项目目录
            win_projects = os.path.join(os.path.expanduser("~"), "Documents", "Projects")
            if os.path.exists(win_projects):
                possible_paths.insert(0, win_projects)
        
        # 收集所有存在的路径（而不是只选择第一个）
        search_paths = []
        for path in possible_paths:
            expanded_path = os.path.abspath(os.path.expanduser(path))
            if os.path.exists(expanded_path) and os.path.isdir(expanded_path):
                search_paths.append(expanded_path)
    
    # 如果没有任何路径存在，使用用户主目录作为默认值
    if not search_paths:
        search_paths = [os.path.abspath(os.path.expanduser("~"))]
    
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
    brief = report_service.generate_brief(today_commits, my_author or "", deepseek_service)
    brief_path = report_service.save_brief_to_file(brief)
    print(f"简报已保存到: {brief_path}")
    print("\n" + "-" * 60)
    print("简报预览:")
    print("-" * 60)
    print(brief)
    print("-" * 60)
    
    print(f"\n日报生成完成 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # # 7. 自动发布到 CRM 系统（可选）
    # print("\n是否要自动发布到 CRM 系统? (y/n): ", end="")
    # choice = input().strip().lower()
    # if choice == 'y':
    #     from service.crm_service import CRMService
    #     from config import CRM_URL, CRM_USERNAME, CRM_PASSWORD
    #     
    #     print("\n正在登录 CRM 系统...")
    #     crm_service = CRMService(CRM_URL, CRM_USERNAME, CRM_PASSWORD)
    #     
    #     if crm_service.login():
    #         print("正在发布日报...")
    #         if crm_service.publish_report(brief):
    #             print("✓ 日报发布成功")
    #         else:
    #             print("✗ 日报发布失败")
    #     else:
    #         print("✗ CRM 登录失败")
    #     
    #     crm_service.close()


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

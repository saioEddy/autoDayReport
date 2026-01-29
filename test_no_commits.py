"""
测试无提交时基于昨天提交生成简报的功能
"""
from service.git_service import GitService
from service.report_service import ReportService
from service.deepseek_service import DeepSeekService
from datetime import datetime

def test_no_commits_today():
    """测试今日无提交，基于昨天提交生成简报"""
    print("=" * 60)
    print("测试场景: 今日无任何提交，基于昨天的提交生成简报")
    print("=" * 60)
    
    # 初始化服务
    git_service = GitService()
    report_service = ReportService()
    deepseek_service = DeepSeekService()
    
    # 发现Git仓库
    print("\n正在搜索Git仓库...")
    git_repos = git_service.discover_git_repos("/Users/sai0/Desktop/vankun/code")
    print(f"发现 {len(git_repos)} 个Git仓库")
    
    # 获取昨天的提交记录（模拟今天无提交的场景）
    print("\n正在获取昨天的提交记录...")
    yesterday_commits = git_service.get_all_yesterday_commits(git_repos)
    print(f"昨天共有 {len(yesterday_commits)} 条提交记录")
    
    if not yesterday_commits:
        print("\n警告: 昨天也没有提交记录，无法测试")
        return
    
    # 显示昨天的提交记录
    print("\n昨天的提交记录:")
    for i, commit in enumerate(yesterday_commits[:5], 1):  # 只显示前5条
        print(f"  {i}. [{commit.get('repo')}] {commit.get('author')}: {commit.get('message')}")
    if len(yesterday_commits) > 5:
        print(f"  ... 还有 {len(yesterday_commits) - 5} 条提交")
    
    # 获取当前作者
    my_author = git_service.get_current_author(git_repos[0] if git_repos else None)
    print(f"\n当前Git用户: {my_author}")
    
    # 模拟今日无提交，传入空列表和昨天的提交记录
    print("\n正在生成简报（基于昨天提交）...")
    today_commits = []  # 模拟今日无提交
    brief = report_service.generate_brief(
        today_commits,
        my_author or "",
        deepseek_service,
        yesterday_commits=yesterday_commits
    )
    
    print("\n" + "=" * 60)
    print("生成的简报内容:")
    print("=" * 60)
    print(brief)
    print("=" * 60)
    
    # 保存到临时文件
    test_path = f"/Users/sai0/Documents/开发代码/自动化日报提交/reports/简报_测试_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    with open(test_path, 'w', encoding='utf-8') as f:
        f.write(brief)
    print(f"\n简报已保存到: {test_path}")

if __name__ == "__main__":
    try:
        test_no_commits_today()
    except Exception as e:
        print(f"\n测试出错: {str(e)}")
        import traceback
        traceback.print_exc()

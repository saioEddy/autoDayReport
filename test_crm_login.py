"""
测试 CRM 登录和发布功能
"""
from service.crm_service import CRMService
from config import CRM_URL, CRM_USERNAME, CRM_PASSWORD
import os

def test_login_and_publish():
    """测试登录和发布"""
    print("=" * 60)
    print("开始测试 CRM 自动登录和发布功能")
    print("=" * 60)
    
    # 创建 CRM 服务实例
    crm_service = CRMService(CRM_URL, CRM_USERNAME, CRM_PASSWORD)
    
    # 执行登录
    print("\n第一步: 登录 CRM 系统")
    success = crm_service.login()
    
    if success:
        print("\n✓ 登录测试成功")
        
        # 读取今日简报内容
        from datetime import datetime
        brief_file = os.path.join('reports', f'简报_{datetime.now().strftime("%Y%m%d")}.txt')
        if os.path.exists(brief_file):
            print(f"\n第二步: 读取简报文件: {brief_file}")
            with open(brief_file, 'r', encoding='utf-8') as f:
                brief_content = f.read()
            print("简报内容:")
            print("-" * 60)
            print(brief_content)
            print("-" * 60)
            
            # 测试发布功能
            print("\n第三步: 发布日报")
            crm_service.publish_report(brief_content)
        else:
            print(f"\n警告: 未找到简报文件: {brief_file}")
            print("提示: 请先运行 main.py 生成日报")
            print("\n浏览器将保持打开状态 60 秒...")
            import time
            time.sleep(60)
    else:
        print("\n✗ 登录测试失败")
    
    # 关闭浏览器
    crm_service.close()
    print("\n测试完成")

if __name__ == "__main__":
    test_login_and_publish()

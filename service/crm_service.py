"""
CRM 自动化发布服务层 - 使用 Playwright 实现登录和日报发布
"""
from playwright.sync_api import sync_playwright, Page, Browser
import time
from typing import Optional


class CRMService:
    """CRM 自动化发布服务类"""
    
    def __init__(self, crm_url: str, username: str, password: str):
        """
        初始化 CRM 服务
        
        Args:
            crm_url: CRM 登录页面地址
            username: 用户名
            password: 密码
        """
        self.crm_url = crm_url
        self.username = username
        self.password = password
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
    
    def login(self) -> bool:
        """
        登录 CRM 系统
        
        Returns:
            登录是否成功
        """
        try:
            print(f"正在访问 CRM 登录页面: {self.crm_url}")
            
            # 启动浏览器
            playwright = sync_playwright().start()
            self.browser = playwright.chromium.launch(headless=False)  # headless=False 方便调试
            self.page = self.browser.new_page()
            
            # 访问登录页面
            self.page.goto(self.crm_url, wait_until="networkidle")
            print("登录页面加载完成")
            
            # 等待页面稳定
            time.sleep(3)
            
            # 调试: 打印页面标题
            print(f"页面标题: {self.page.title()}")
            
            # 调试: 查找所有 input 元素
            print("\n正在分析页面上的输入框...")
            all_inputs = self.page.locator('input').all()
            print(f"找到 {len(all_inputs)} 个输入框:")
            for i, inp in enumerate(all_inputs):
                try:
                    input_type = inp.get_attribute('type') or 'text'
                    input_name = inp.get_attribute('name') or ''
                    input_id = inp.get_attribute('id') or ''
                    input_placeholder = inp.get_attribute('placeholder') or ''
                    input_class = inp.get_attribute('class') or ''
                    is_visible = inp.is_visible()
                    print(f"  [{i}] type={input_type}, name={input_name}, id={input_id}, placeholder={input_placeholder}, class={input_class}, visible={is_visible}")
                except:
                    pass
            
            # 调试: 查找所有按钮
            print("\n正在分析页面上的按钮...")
            all_buttons = self.page.locator('button, input[type="submit"], input[type="button"]').all()
            print(f"找到 {len(all_buttons)} 个按钮:")
            for i, btn in enumerate(all_buttons):
                try:
                    btn_text = btn.inner_text() if btn.inner_text() else ''
                    btn_type = btn.get_attribute('type') or ''
                    btn_class = btn.get_attribute('class') or ''
                    is_visible = btn.is_visible()
                    print(f"  [{i}] text={btn_text}, type={btn_type}, class={btn_class}, visible={is_visible}")
                except:
                    pass
            
            # 查找并填写用户名输入框
            print(f"\n正在输入用户名: {self.username}")
            # 根据你提供的 DOM 结构，用户名输入框 id 是 login_user_name
            username_selectors = [
                'input#login_user_name',  # 精确匹配
                'input[name="login_user_name"]',
                'input[placeholder*="请输入账号"]',
                'input[placeholder*="账号"]',
                'input[type="text"]',  # 第一个文本输入框通常是用户名
                'input.text-input',
            ]
            username_input = None
            for selector in username_selectors:
                try:
                    locators = self.page.locator(selector).all()
                    for loc in locators:
                        if loc.is_visible():
                            username_input = loc
                            print(f"  找到用户名输入框: {selector}")
                            break
                    if username_input:
                        break
                except Exception as e:
                    pass
            
            if username_input:
                username_input.click()
                time.sleep(0.5)
                username_input.fill(self.username)
                print("  ✓ 用户名输入完成")
            else:
                print("  ✗ 警告: 未找到用户名输入框")
                print("  提示: 浏览器将保持打开,请手动查看页面结构")
                time.sleep(30)
                return False
            
            # 查找并填写密码输入框
            print("正在输入密码")
            password_selectors = [
                'input[type="password"]',
                'input[name="password"]',
                'input[name="login_password"]',  # 可能的命名
                'input#login_password',
                'input[name="passwd"]',
                'input[name="pwd"]',
                'input#password',
                'input.password',
                'input[placeholder*="密码"]'
            ]
            password_input = None
            for selector in password_selectors:
                try:
                    locators = self.page.locator(selector).all()
                    for loc in locators:
                        if loc.is_visible():
                            password_input = loc
                            print(f"  找到密码输入框: {selector}")
                            break
                    if password_input:
                        break
                except Exception as e:
                    pass
            
            if password_input:
                password_input.click()
                time.sleep(0.5)
                password_input.fill(self.password)
                print("  ✓ 密码输入完成")
            else:
                print("  ✗ 警告: 未找到密码输入框")
                print("  提示: 浏览器将保持打开,请手动查看页面结构")
                time.sleep(30)
                return False
            
            # 查找并点击登录按钮
            print("正在点击登录按钮")
            # 根据你提供的 DOM 结构，登录按钮是一个 <a> 标签，class="btn-submit"
            login_button_selectors = [
                'a.btn-submit',  # 精确匹配你提供的登录按钮
                'a.btn-submit.inline-block',
                'div#form_login a.btn-submit',
                'div.crm-container-btn a.btn-submit',
                'a[onclick*="Check"]',  # 根据 onclick="return Check();" 匹配
                'a:has-text("登 录")',  # 根据按钮文本匹配
                'a:has-text("登录")',
                'button[type="submit"]',
                'input[type="submit"]',
                'button'  # 最后尝试所有按钮
            ]
            login_button = None
            for selector in login_button_selectors:
                try:
                    locators = self.page.locator(selector).all()
                    for loc in locators:
                        if loc.is_visible():
                            login_button = loc
                            print(f"  找到登录按钮: {selector}")
                            break
                    if login_button:
                        break
                except Exception as e:
                    pass
            
            if login_button:
                # 尝试点击前截图(调试用)
                # self.page.screenshot(path="before_login.png")
                login_button.click()
                print("  ✓ 已点击登录按钮")
            else:
                print("  ✗ 警告: 未找到登录按钮")
                print("  提示: 浏览器将保持打开,请手动查看页面结构")
                time.sleep(30)
                return False
            
            # 等待登录完成（等待页面跳转或特定元素出现）
            print("\n等待登录完成...")
            time.sleep(5)
            
            # 检查是否登录成功（通过 URL 变化或页面元素判断）
            current_url = self.page.url
            print(f"当前页面 URL: {current_url}")
            print(f"当前页面标题: {self.page.title()}")
            
            # 尝试多种方式判断登录成功
            login_success = False
            
            # 方式1: URL 变化
            if current_url != self.crm_url and '/login' not in current_url.lower():
                login_success = True
                print("  检测到页面已跳转")
            
            # 方式2: 查找登录后才有的元素(例如用户信息、退出按钮等)
            try:
                logout_elements = self.page.locator('text=/退出|登出|logout/i').all()
                if logout_elements:
                    login_success = True
                    print("  检测到退出按钮")
            except:
                pass
            
            # 方式3: 检查是否还有登录表单
            try:
                login_forms = self.page.locator('input[type="password"]').all()
                if not login_forms:
                    login_success = True
                    print("  登录表单已消失")
            except:
                pass
            
            if login_success:
                print("\n✓ 登录成功")
                
                # 登录成功后，先点击"OA表单"菜单，然后点击"工作汇报"
                print("\n第一步: 查找并点击'OA表单'菜单...")
                
                # 等待页面完全加载，特别是左侧菜单
                print("  等待左侧菜单加载...")
                time.sleep(5)  # 增加等待时间
                
                # 尝试等待左侧菜单容器出现
                try:
                    self.page.wait_for_selector('nav#pageleft_unfold', timeout=10000)
                    print("  ✓ 左侧菜单容器已加载")
                except:
                    print("  ⚠ 左侧菜单容器加载超时，继续尝试...")
                
                # 根据你提供的 DOM 路径查找"OA表单"
                # DOM Path: nav#pageleft_unfold > div#suspensionmenu > div.nav-menu-body > div.limScrollDiv > div.ub-menu > div.page-menu > ul > li[5] > div.page-link .elected > a > span
                oa_form_selectors = [
                    'nav#pageleft_unfold ul.page-menu li:nth-child(5) a',  # 根据 li[5] 定位
                    'nav#pageleft_unfold ul.page-menu li:nth-child(5) div.page-link a',
                    'nav#pageleft_unfold ul li:nth-child(5) span:has-text("OA表单")',
                    'nav#pageleft_unfold ul li:nth-child(5) a span:has-text("OA表单")',
                    'nav#pageleft_unfold a span:has-text("OA表单")',
                    'nav#pageleft_unfold span:has-text("OA表单")',
                    'div.page-menu li:nth-child(5) a',
                    'span:has-text("OA表单")',
                ]
                
                # 调试: 打印菜单项
                print("\n  调试: 查找左侧菜单项...")
                try:
                    menu_items = self.page.locator('nav#pageleft_unfold ul.page-menu li').all()
                    print(f"  找到 {len(menu_items)} 个菜单项:")
                    for i, item in enumerate(menu_items):
                        try:
                            item_text = item.inner_text().strip() if item.inner_text() else ''
                            is_visible = item.is_visible()
                            print(f"    [{i+1}] text='{item_text}', visible={is_visible}")
                        except:
                            pass
                except Exception as e:
                    print(f"    调试信息获取失败: {e}")
                
                oa_form_link = None
                
                # 方法1: 直接查找包含"OA表单"文本的元素
                try:
                    oa_form_span = self.page.locator('span:has-text("OA表单")').first
                    if oa_form_span.is_visible():
                        # 找到父级 a 标签
                        try:
                            parent_a = oa_form_span.locator('xpath=ancestor::a[1]')
                            if parent_a.count() > 0:
                                oa_form_link = parent_a.first
                                print(f"  ✓ 找到'OA表单'菜单 (通过span的父级a)")
                        except:
                            # 如果找不到父级 a，尝试查找父级 div.page-link > a
                            try:
                                parent_div = oa_form_span.locator('xpath=ancestor::div[contains(@class, "page-link")][1]')
                                if parent_div.count() > 0:
                                    parent_a = parent_div.locator('a').first
                                    if parent_a.count() > 0:
                                        oa_form_link = parent_a.first
                                        print(f"  ✓ 找到'OA表单'菜单 (通过div.page-link > a)")
                            except:
                                pass
                except:
                    pass
                
                # 方法2: 如果方法1失败，尝试使用选择器列表
                if not oa_form_link:
                    for selector in oa_form_selectors:
                        try:
                            print(f"  尝试选择器: {selector}")
                            locators = self.page.locator(selector).all()
                            for loc in locators:
                                try:
                                    if loc.is_visible():
                                        # 验证文本内容
                                        link_text = loc.inner_text().strip() if loc.inner_text() else ''
                                        if 'OA表单' in link_text:
                                            oa_form_link = loc
                                            print(f"  ✓ 找到'OA表单'菜单: {selector}")
                                            print(f"    菜单文本: {link_text}")
                                            break
                                except Exception as e:
                                    print(f"    检查元素时出错: {e}")
                                    continue
                            if oa_form_link:
                                break
                        except Exception as e:
                            print(f"    选择器 {selector} 出错: {e}")
                            continue
                
                if oa_form_link:
                    try:
                        # 确保元素在视口中（滚动到可见）
                        oa_form_link.scroll_into_view_if_needed()
                        time.sleep(0.5)
                        
                        # 点击"OA表单"菜单
                        oa_form_link.click()
                        print("  ✓ 已点击'OA表单'菜单")
                        
                        # 等待子菜单展开
                        print("  等待子菜单展开...")
                        time.sleep(3)
                        
                        # 第二步: 在展开的子菜单中查找"工作汇报"
                        print("\n第二步: 在'OA表单'子菜单中查找'工作汇报'...")
                        
                        # 查找"工作汇报"链接
                        work_report_selectors = [
                            'nav#pageleft_unfold a[href*="CooperativeWork"]',
                            'nav#pageleft_unfold a:has-text("工作汇报")',
                            'a[href*="CooperativeWork"]',
                            'a[href="index.php?pageto_module=CooperativeWork&pageto_action=index"]',
                            'a:has-text("工作汇报")',
                        ]
                        
                        # 调试: 打印子菜单中的链接
                        print("\n  调试: 查找子菜单中的链接...")
                        try:
                            submenu_links = self.page.locator('nav#pageleft_unfold a').all()
                            print(f"  找到 {len(submenu_links)} 个链接:")
                            for i, link in enumerate(submenu_links):
                                try:
                                    link_text = link.inner_text().strip() if link.inner_text() else ''
                                    link_href = link.get_attribute('href') or ''
                                    is_visible = link.is_visible()
                                    if is_visible:
                                        print(f"    [{i}] text='{link_text}', href='{link_href}', visible={is_visible}")
                                except:
                                    pass
                        except Exception as e:
                            print(f"    调试信息获取失败: {e}")
                        
                        work_report_link = None
                        for selector in work_report_selectors:
                            try:
                                print(f"  尝试选择器: {selector}")
                                locators = self.page.locator(selector).all()
                                for loc in locators:
                                    try:
                                        if loc.is_visible():
                                            # 验证文本内容
                                            link_text = loc.inner_text().strip() if loc.inner_text() else ''
                                            link_href = loc.get_attribute('href') or ''
                                            if '工作汇报' in link_text or 'CooperativeWork' in link_href:
                                                work_report_link = loc
                                                print(f"  ✓ 找到'工作汇报'菜单: {selector}")
                                                print(f"    链接文本: {link_text}")
                                                print(f"    链接地址: {link_href}")
                                                break
                                    except Exception as e:
                                        print(f"    检查元素时出错: {e}")
                                        continue
                                if work_report_link:
                                    break
                            except Exception as e:
                                print(f"    选择器 {selector} 出错: {e}")
                                continue
                        
                        if work_report_link:
                            # 确保元素在视口中（滚动到可见）
                            work_report_link.scroll_into_view_if_needed()
                            time.sleep(0.5)
                            
                            # 点击"工作汇报"链接
                            work_report_link.click()
                            print("  ✓ 已点击'工作汇报'菜单")
                            
                            # 等待页面跳转
                            print("  等待页面跳转...")
                            time.sleep(5)
                            
                            # 等待新页面加载
                            try:
                                self.page.wait_for_load_state("networkidle", timeout=10000)
                            except:
                                pass
                            
                            current_url = self.page.url
                            print(f"  ✓ 当前页面 URL: {current_url}")
                            
                            if 'CooperativeWork' in current_url:
                                print("  ✓ 已成功跳转到工作汇报页面")
                            else:
                                print("  ⚠ 页面可能未完全跳转，请检查")
                        else:
                            print("  ✗ 未找到'工作汇报'子菜单项")
                            print("  提示: 浏览器将保持打开 30 秒，请手动检查页面结构...")
                            time.sleep(30)
                            
                    except Exception as e:
                        print(f"  ✗ 点击菜单时出错: {str(e)}")
                        import traceback
                        traceback.print_exc()
                else:
                    print("  ✗ 未找到'OA表单'菜单")
                    print("  提示: 浏览器将保持打开 30 秒，请手动检查页面结构...")
                    time.sleep(30)
                
                return True
            else:
                print("\n✗ 登录可能失败")
                print("  提示: 浏览器将保持打开 30 秒,请手动检查")
                time.sleep(30)
                return False
                
        except Exception as e:
            print(f"\n登录过程出错: {str(e)}")
            import traceback
            traceback.print_exc()
            if self.page:
                print("  提示: 浏览器将保持打开 30 秒,请手动检查")
                time.sleep(30)
            return False
    
    def _scroll_element_into_view_in_container(self, element, container_selector='div.Edit_box'):
        """
        在指定的容器内滚动元素到可见区域
        
        Args:
            element: Playwright 元素定位器
            container_selector: 容器选择器，默认是 div.Edit_box
            
        Returns:
            是否成功滚动
        """
        try:
            print(f"    尝试在容器 {container_selector} 内滚动...")
            
            # 尝试多个可能的容器选择器
            selectors_to_try = [
                'div.pubclear.Edit_box',
                'div.Edit_box',
                'div#sendLog',
                'div#sendTxt',
                'div.cont_wrap',
            ]
            
            for selector in selectors_to_try:
                try:
                    container = self.page.locator(selector).first
                    if container.count() == 0:
                        continue
                    
                    # 检查容器是否有滚动条
                    scroll_height = container.evaluate('el => el.scrollHeight')
                    client_height = container.evaluate('el => el.clientHeight')
                    
                    if scroll_height <= client_height:
                        print(f"      容器 {selector} 没有滚动条 (scrollHeight={scroll_height}, clientHeight={client_height})")
                        continue
                    
                    print(f"      找到可滚动容器: {selector} (scrollHeight={scroll_height}, clientHeight={client_height})")
                    
                    # 检查元素是否在这个容器内
                    try:
                        element_in_container = element.evaluate(f'''
                            (el) => {{
                                const container = document.querySelector('{selector}');
                                return container && container.contains(el);
                            }}
                        ''')
                        if not element_in_container:
                            print(f"      元素不在容器 {selector} 内，跳过")
                            continue
                        print(f"      ✓ 元素在容器 {selector} 内")
                    except Exception as check_err:
                        print(f"      检查元素是否在容器内时出错: {check_err}，假设元素在容器内")
                    
                    # 获取元素和容器的位置信息
                    element_box = element.bounding_box()
                    container_box = container.bounding_box()
                    
                    if element_box and container_box:
                        print(f"      元素位置: y={element_box['y']}, 容器位置: y={container_box['y']}")
                        
                        # 计算元素相对于容器的位置
                        element_relative_top = element_box['y'] - container_box['y']
                        container_height = container_box['height']
                        
                        # 获取容器当前的滚动位置
                        current_scroll = container.evaluate('el => el.scrollTop')
                        print(f"      当前滚动位置: {current_scroll}, 元素相对位置: {element_relative_top}")
                        
                        # 计算需要滚动到的位置，使元素在容器中间
                        target_scroll = element_relative_top + current_scroll - container_height / 2
                        # 确保滚动位置在有效范围内
                        target_scroll = max(0, min(target_scroll, scroll_height - client_height))
                        
                        print(f"      滚动到位置: {target_scroll}")
                        
                        # 滚动容器
                        container.evaluate(f'el => el.scrollTop = {target_scroll}')
                        time.sleep(0.8)  # 增加等待时间
                        
                        # 验证滚动是否成功
                        new_scroll = container.evaluate('el => el.scrollTop')
                        print(f"      滚动后位置: {new_scroll}")
                        
                        return True
                except Exception as e:
                    print(f"      尝试容器 {selector} 时出错: {e}")
                    continue
            
            print("    未找到可滚动的容器")
            return False
        except Exception as e:
            print(f"    容器内滚动失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def publish_report(self, brief_content: str) -> bool:
        """
        发布日报到 CRM 系统
        
        Args:
            brief_content: 简报内容，格式应该包含三个部分：
                - 上午时间安排与工作内容
                - 下午时间安排与工作内容
                - 今日计划的学习内容与进度
            
        Returns:
            发布是否成功
        """
        try:
            if not self.page:
                print("错误: 请先登录")
                return False
            
            print("\n正在解析简报内容...")
            # 解析简报内容，提取三个字段
            lines = brief_content.strip().split('\n')
            morning_content = ""
            afternoon_content = ""
            learning_content = ""
            
            current_section = None
            for line in lines:
                original_line = line
                line = line.strip()
                if not line:
                    continue
                # 检查是否是新的章节标题
                if '*上午时间安排与工作内容' in line or '上午时间安排' in line:
                    current_section = 'morning'
                    continue
                elif '*下午时间安排与工作内容' in line or '下午时间安排' in line:
                    current_section = 'afternoon'
                    continue
                elif '*今日计划的学习内容与进度' in line or '*今日计划' in line or ('学习内容' in line and '计划' in line):
                    current_section = 'learning'
                    continue
                # 如果不是章节标题，根据当前章节添加到对应内容
                if current_section == 'morning' and not line.startswith('*'):
                    morning_content += line + '\n'
                elif current_section == 'afternoon' and not line.startswith('*'):
                    afternoon_content += line + '\n'
                elif current_section == 'learning' and not line.startswith('*'):
                    learning_content += line + '\n'
            
            morning_content = morning_content.strip()
            afternoon_content = afternoon_content.strip()
            learning_content = learning_content.strip()
            
            print(f"  上午内容: {morning_content}")
            print(f"  下午内容: {afternoon_content}")
            print(f"  学习内容: {learning_content}")
            
            # 调试：如果学习内容为空，打印原始内容
            if not learning_content:
                print("  ⚠ 警告: 学习内容解析为空，原始简报内容:")
                print("  " + "\n  ".join(brief_content.split('\n')))
            
            # 现在应该在"工作汇报"页面，先点击"日志"标签
            print("\n正在查找并点击'日志'标签...")
            time.sleep(2)  # 等待页面稳定
            
            # 根据你提供的 DOM 结构查找"日志"标签
            log_tab_selectors = [
                'a[tag="day"][cont="sendLog"]',  # 根据你提供的属性
                'a.curr[tag="day"]',  # 当前选中的标签
                'ul#stream-hsent-title a[tag="day"]',
                'ul#stream-hsent-title a:has-text("日志")',
                'a:has-text("日志")',
            ]
            
            log_tab = None
            for selector in log_tab_selectors:
                try:
                    locators = self.page.locator(selector).all()
                    for loc in locators:
                        try:
                            if loc.is_visible():
                                link_text = loc.inner_text().strip() if loc.inner_text() else ''
                                link_tag = loc.get_attribute('tag') or ''
                                link_cont = loc.get_attribute('cont') or ''
                                if '日志' in link_text or (link_tag == 'day' and link_cont == 'sendLog'):
                                    log_tab = loc
                                    print(f"  ✓ 找到'日志'标签: {selector}")
                                    print(f"    标签文本: {link_text}, tag={link_tag}, cont={link_cont}")
                                    break
                        except:
                            continue
                    if log_tab:
                        break
                except Exception as e:
                    print(f"    选择器 {selector} 出错: {e}")
                    continue
            
            if log_tab:
                try:
                    log_tab.click()
                    print("  ✓ 已点击'日志'标签")
                    time.sleep(2)  # 等待标签页切换
                except Exception as e:
                    print(f"  ✗ 点击'日志'标签时出错: {str(e)}")
            else:
                print("  ⚠ 未找到'日志'标签，尝试继续查找表单...")
            
            # 等待表单加载
            print("\n等待表单加载...")
            time.sleep(3)
            
            # 调试：查找所有可能的滚动容器
            print("\n正在查找滚动容器...")
            try:
                # 查找所有可能的容器
                container_selectors = [
                    'div.Edit_box',
                    'div.pubclear.Edit_box',
                    'div#sendLog',
                    'div#sendTxt',
                    'div.cont_wrap',
                    'div.Cbox',
                    'div.middle',
                ]
                
                for selector in container_selectors:
                    try:
                        containers = self.page.locator(selector).all()
                        for i, container in enumerate(containers):
                            if container.is_visible():
                                try:
                                    # 检查是否有滚动条
                                    scroll_height = container.evaluate('el => el.scrollHeight')
                                    client_height = container.evaluate('el => el.clientHeight')
                                    scroll_top = container.evaluate('el => el.scrollTop')
                                    has_scroll = scroll_height > client_height
                                    
                                    print(f"  容器 [{i}] {selector}:")
                                    print(f"    scrollHeight={scroll_height}, clientHeight={client_height}, scrollTop={scroll_top}")
                                    print(f"    有滚动条: {has_scroll}")
                                    
                                    if has_scroll:
                                        print(f"    ✓ 找到可滚动容器: {selector}")
                                except Exception as e:
                                    print(f"    检查容器时出错: {e}")
                    except:
                        pass
            except Exception as e:
                print(f"  查找容器时出错: {e}")
            
            # 分析整个表单，找出所有字段
            print("\n正在分析整个表单...")
            all_form_fields = []
            
            try:
                # 查找所有 textarea 字段
                all_textareas = self.page.locator('textarea').all()
                print(f"  找到 {len(all_textareas)} 个文本域字段")
                
                for i, textarea in enumerate(all_textareas):
                    try:
                        field_name = textarea.get_attribute('name') or ''
                        field_id = textarea.get_attribute('id') or ''
                        field_class = textarea.get_attribute('class') or ''
                        
                        # 尝试获取字段的标签文本（通过查找前面的 label 或父元素中的文本）
                        label_text = ''
                        try:
                            # 尝试查找前面的 label
                            label = textarea.locator('xpath=preceding::label[1]').first
                            if label.count() > 0:
                                label_text = label.inner_text().strip()
                            else:
                                # 尝试查找父元素中的文本
                                parent = textarea.locator('xpath=ancestor::fieldset[1]').first
                                if parent.count() > 0:
                                    parent_text = parent.inner_text().strip()
                                    # 提取第一行作为标签
                                    if parent_text:
                                        label_text = parent_text.split('\n')[0].strip()
                        except:
                            pass
                        
                        # 判断字段类型
                        field_type = 'other'  # 默认为其他字段
                        field_content = '无'  # 默认填写"无"
                        
                        # 只处理日志标签页的字段（字段1-8）
                        if field_name == 'worksummary' and '*上午时间安排' in label_text:
                            field_type = 'morning'
                            field_content = morning_content
                        elif field_name == 'workfld_21' and '*下午时间安排' in label_text:
                            field_type = 'afternoon'
                            field_content = afternoon_content
                        elif field_name == 'workexperience' and '*今日计划的学习内容' in label_text:
                            field_type = 'learning'
                            field_content = learning_content
                        elif '售前' in label_text or '销售' in label_text:
                            field_type = 'presale'
                            field_content = '无'
                        elif '项目交付' in label_text or 'PM' in label_text or '售后' in label_text:
                            field_type = 'delivery'
                            field_content = '无'
                        elif '上级支持' in label_text or '紧急事项' in label_text:
                            field_type = 'support'
                            field_content = '无'
                        
                        all_form_fields.append({
                            'index': i,
                            'element': textarea,
                            'name': field_name,
                            'id': field_id,
                            'class': field_class,
                            'label': label_text,
                            'type': field_type,
                            'content': field_content,
                        })
                        
                        print(f"    字段 [{i}]: name={field_name}, id={field_id}, label={label_text[:30] if label_text else 'N/A'}, type={field_type}")
                    except Exception as e:
                        print(f"    分析字段 [{i}] 时出错: {e}")
                        continue
                
                print(f"\n  ✓ 表单分析完成，共 {len(all_form_fields)} 个字段")
            except Exception as e:
                print(f"  分析表单时出错: {e}")
                import traceback
                traceback.print_exc()
                # 如果分析失败，使用原来的方法
                all_form_fields = [
                    {'element': self.page.locator('textarea[name="worksummary"]').first, 'name': 'worksummary', 'type': 'morning', 'content': morning_content},
                    {'element': self.page.locator('textarea[name="workfld_21"]').first, 'name': 'workfld_21', 'type': 'afternoon', 'content': afternoon_content},
                    {'element': self.page.locator('textarea[name="workexperience"]').first, 'name': 'workexperience', 'type': 'learning', 'content': learning_content},
                ]
            
            # 填写所有表单字段
            print("\n正在填写表单字段...")
            
            # 只填写日志标签页的特定字段（索引1, 2, 3, 5, 6, 7, 8，跳过4）
            target_indices = [1, 2, 3, 5, 6, 7, 8]
            daily_fields = [f for f in all_form_fields if f['index'] in target_indices]
            print(f"  将填写 {len(daily_fields)} 个日志字段 (索引: {target_indices})")
            
            filled_fields = []
            for field_info in daily_fields:
                field = field_info['element']
                field_name = field_info.get('name') or field_info.get('id') or f'field_{field_info["index"]}'
                field_type = field_info.get('type', 'other')
                content = field_info.get('content', '无')
                label_text = field_info.get('label', '')
                
                # 生成字段显示名称
                if field_type == 'morning':
                    display_name = '上午工作内容'
                elif field_type == 'afternoon':
                    display_name = '下午工作内容'
                elif field_type == 'learning':
                    display_name = '今日计划学习内容'
                elif field_type == 'presale':
                    display_name = '售前工作'
                elif field_type == 'delivery':
                    display_name = '项目交付'
                elif field_type == 'support':
                    display_name = '上级支持事项'
                else:
                    display_name = label_text[:20] if label_text else field_name
                
                # 跳过没有内容的字段（但"无"是有效内容）
                if not content:
                    print(f"  ⚠ {display_name} ({field_name}) 内容为空，跳过")
                    continue
                try:
                    print(f"  正在填写{display_name} (name={field_name})...")
                    if content != '无':
                        print(f"    内容预览: {content[:50]}..." if len(content) > 50 else f"    内容: {content}")
                    else:
                        print(f"    内容: {content}")
                    
                    # 先尝试滚动到元素位置（在容器内）
                    try:
                        field.scroll_into_view_if_needed()
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # 如果不可见，尝试在容器内滚动
                    if not field.is_visible():
                        self._scroll_element_into_view_in_container(field)
                        time.sleep(1)
                    
                    # 等待元素可见
                    try:
                        field.wait_for(state="visible", timeout=10000)  # 增加等待时间
                    except:
                        print(f"    ⚠ {field_name} 元素未在10秒内可见，尝试在容器内滚动...")
                        # 尝试滚动容器到底部
                        try:
                            container = self.page.locator('div.Edit_box').first
                            if container.count() > 0:
                                container.evaluate('el => el.scrollTop = el.scrollHeight')
                                time.sleep(1)
                                field.scroll_into_view_if_needed()
                                time.sleep(1)
                        except:
                            pass
                    
                    # 先尝试滚动到元素位置（在容器内滚动）
                    try:
                        field.scroll_into_view_if_needed()
                        time.sleep(0.5)
                    except:
                        pass
                    
                    # 如果不可见，尝试在容器内滚动
                    if not field.is_visible():
                        print(f"    元素不可见，尝试在容器内滚动...")
                        self._scroll_element_into_view_in_container(field)
                        time.sleep(0.8)
                    
                    # 如果仍然不可见，尝试滚动所有可能的容器到底部（特别是学习内容字段）
                    if not field.is_visible() and field_type == 'learning':
                        try:
                            container_selectors = [
                                'div.pubclear.Edit_box',
                                'div.Edit_box',
                                'div#sendLog',
                                'div#sendTxt',
                            ]
                            
                            for selector in container_selectors:
                                try:
                                    container = self.page.locator(selector).first
                                    if container.count() > 0:
                                        scroll_height = container.evaluate('el => el.scrollHeight')
                                        client_height = container.evaluate('el => el.clientHeight')
                                        if scroll_height > client_height:
                                            print(f"    尝试滚动容器 {selector} 到底部...")
                                            container.evaluate('el => el.scrollTop = el.scrollHeight')
                                            time.sleep(1)
                                            field.scroll_into_view_if_needed()
                                            time.sleep(0.5)
                                            if field.is_visible():
                                                print(f"    ✓ 通过滚动容器 {selector} 找到元素")
                                                break
                                except:
                                    continue
                        except Exception as e:
                            print(f"    滚动容器失败: {e}")
                    
                    # 再次检查是否可见
                    if field.is_visible():
                        # 点击聚焦
                        field.click()
                        time.sleep(0.5)
                        
                        # 尝试多种填写方式
                        success = False
                        
                        # 方法1: 使用 fill
                        try:
                            field.fill('')  # 先清空
                            time.sleep(0.3)
                            field.fill(content)  # 再填写
                            time.sleep(0.5)
                            filled_value = field.input_value()
                            if filled_value == content or content in filled_value:
                                print(f"  ✓ 已填写{display_name} (使用fill方法)")
                                filled_fields.append(display_name)
                                success = True
                        except Exception as e:
                            print(f"    fill方法失败: {e}")
                        
                        # 方法2: 如果fill失败，尝试使用type方法
                        if not success:
                            try:
                                field.fill('')  # 先清空
                                time.sleep(0.3)
                                field.type(content, delay=10)  # 使用type方法，每个字符延迟10ms
                                time.sleep(0.5)
                                filled_value = field.input_value()
                                if filled_value == content or content in filled_value:
                                    print(f"  ✓ 已填写{display_name} (使用type方法)")
                                    filled_fields.append(display_name)
                                    success = True
                            except Exception as e:
                                print(f"    type方法失败: {e}")
                        
                        # 方法3: 如果都失败，尝试使用evaluate直接设置value
                        if not success:
                            try:
                                field.evaluate(f'el => el.value = {repr(content)}')
                                # 触发input事件
                                field.evaluate('el => el.dispatchEvent(new Event("input", { bubbles: true }))')
                                time.sleep(0.5)
                                filled_value = field.input_value()
                                if filled_value == content or content in filled_value:
                                    print(f"  ✓ 已填写{display_name} (使用evaluate方法)")
                                    filled_fields.append(display_name)
                                    success = True
                            except Exception as e:
                                print(f"    evaluate方法失败: {e}")
                        
                        if not success:
                            filled_value = field.input_value()
                            print(f"  ✗ {display_name} 填写失败")
                            print(f"    期望内容: {content}")
                            print(f"    实际内容: {filled_value}")
                            print(f"    期望长度: {len(content)}, 实际长度: {len(filled_value)}")
                    else:
                        print(f"  ✗ {display_name} 元素不可见")
                except Exception as e:
                    print(f"  ✗ 填写{display_name}时出错: {str(e)}")
                    import traceback
                    traceback.print_exc()
            
            if filled_fields:
                print(f"\n  ✓ 成功填写了 {len(filled_fields)} 个字段: {', '.join(filled_fields)}")
            else:
                print("\n  ✗ 未能填写任何表单字段")
                return False
            
            # 点击发布按钮
            print("\n正在点击发布按钮...")
            try:
                # 等待发布按钮可见
                publish_btn = self.page.locator('input#ReleaseBtn[type="button"][value="发布"]')
                publish_btn.wait_for(state="visible", timeout=5000)
                
                # 点击发布按钮
                publish_btn.click()
                print("  ✓ 已点击发布按钮")
                
                # 等待发布完成（可能有弹窗或页面跳转）
                time.sleep(3)
                
                # 检查是否有成功提示
                try:
                    # 可能有成功提示的弹窗或消息
                    success_msg = self.page.locator('text=/发布成功|提交成功|保存成功/').first
                    if success_msg.count() > 0:
                        print("  ✓ 发布成功！")
                        return True
                except:
                    pass
                
                print("  ✓ 发布请求已提交")
                
                # 保持页面打开10秒，方便查看结果
                print("\n浏览器将保持打开状态 10 秒，可以查看发布结果...")
                time.sleep(10)
                
                return True
                
            except Exception as e:
                print(f"  ✗ 点击发布按钮失败: {e}")
                print("\n浏览器将保持打开状态 30 秒，可以手动点击发布...")
                time.sleep(30)
                return False
            
        except Exception as e:
            print(f"发布日报出错: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def close(self):
        """关闭浏览器"""
        try:
            if self.browser:
                self.browser.close()
                print("浏览器已关闭")
        except Exception as e:
            print(f"关闭浏览器出错: {str(e)}")

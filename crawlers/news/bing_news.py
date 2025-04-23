"""
Bing新闻爬虫 - Bing News Crawler
爬取Bing新闻中有关公司的新闻报道
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
from urllib.parse import urljoin, quote_plus
import random
import re
import os
from datetime import datetime
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

# 移除sys.path修改，使用相对导入
from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name, format_date

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('bing_news')

class BingNewsCrawler:
    """Bing新闻爬虫"""
    
    BASE_URL = "https://www.bing.com/news/search"
    
    def __init__(self):
        self.anticrawl = get_anticrawl_manager()
        self.storage = get_storage_manager()
        self.session = HTMLSession()
        # 添加输出目录设置
        self.output_dir = os.path.join(os.getcwd(), "output", "bing_news")
        os.makedirs(self.output_dir, exist_ok=True)
    
    def _setup_browser(self):
        """
        配置并返回一个Chrome浏览器实例
        """
        # 配置Chrome选项
        options = uc.ChromeOptions()
        
        # 更高级的伪装设置
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-web-security')
        options.add_argument('--allow-running-insecure-content')
        options.add_argument('--no-sandbox')
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--no-default-browser-check')
        options.add_argument('--no-first-run')
        options.add_argument('--no-service-autorun')
        options.add_argument('--password-store=basic')
        options.add_argument('--start-maximized')
        
        # 使用更多现代常见用户代理
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0'
        ]
        
        selected_agent = random.choice(user_agents)
        options.add_argument(f'--user-agent={selected_agent}')
        
        # 设置语言和区域
        options.add_argument('--lang=en-US')
        options.add_argument('--accept-lang=en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7')
        
        # 设置浏览器首选项
        prefs = {
            'profile.default_content_setting_values.notifications': 2,
            'credentials_enable_service': False,
            'profile.password_manager_enabled': False,
            'profile.default_content_settings.popups': 0,
            'download.prompt_for_download': False,
            'plugins.always_open_pdf_externally': True,
            'intl.accept_languages': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',
            'profile.managed_default_content_settings.images': 1  # 1允许图像，2禁用图像
        }
        options.add_experimental_option('prefs', prefs)
        
        # 删除可识别的特征
        options.add_experimental_option('excludeSwitches', ['enable-automation', 'enable-logging'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # 决定是否使用无头模式
        use_headless = False
        # 检查是否在命令行环境中
        if 'DISPLAY' not in os.environ or os.environ.get('CI') == 'true' or os.environ.get('HEADLESS') == 'true':
            use_headless = True
            logger.info("检测到命令行环境，将使用无头模式")
            options.add_argument('--headless=new')  # 新版Chrome无头模式
            options.add_argument('--window-size=1920,1080')  # 确保足够大的窗口大小
        
        # 创建浏览器实例
        logger.info(f"创建并配置浏览器...{'无头模式' if use_headless else '有头模式'}")
        browser = uc.Chrome(options=options, headless=use_headless)
        
        # 设置页面加载超时为60秒
        browser.set_page_load_timeout(60)
        
        # 添加更多反检测措施
        stealth_js = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
        
        // 覆盖 navigator 属性以避免检测
        const newProto = navigator.__proto__;
        delete newProto.webdriver;
        
        // 覆盖语言设置
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'zh-CN'],
        });
        
        // 添加假插件数据
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // 修改canvas指纹
        const originalGetContext = HTMLCanvasElement.prototype.getContext;
        HTMLCanvasElement.prototype.getContext = function(type) {
            const context = originalGetContext.apply(this, arguments);
            if (type === '2d') {
                const originalFillText = context.fillText;
                context.fillText = function() {
                    return originalFillText.apply(this, arguments);
                }
            }
            return context;
        };
        
        // 覆盖更多检测特征
        Object.defineProperty(window, 'chrome', {
            get: () => ({
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {},
            }),
        });
        
        // 调整屏幕属性
        Object.defineProperty(window, 'outerWidth', {
            get: () => 1920,
        });
        Object.defineProperty(window, 'outerHeight', {
            get: () => 1080,
        });
        
        // 添加更多随机化以减少指纹识别
        const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
        WebGLRenderingContext.prototype.getParameter = function(parameter) {
            // 针对某些常见的检测参数进行模拟
            if (parameter === 37445) {
                return 'Intel Inc.';
            }
            if (parameter === 37446) {
                return 'Intel Iris Pro Graphics';
            }
            return originalGetParameter.apply(this, arguments);
        };
        
        """
        
        try:
            # 在所有页面上应用此JavaScript
            browser.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                "source": stealth_js
            })
            
            # 设置接受所有Cookie
            browser.execute_cdp_cmd('Network.enable', {})
            
            # 设置Cookie处理
            browser.execute_cdp_cmd('Network.setCookieLifecyclePolicy', {'cookieLifecyclePolicy': 'accept'})
            
            # 清除浏览器任何现有的Cookie和缓存数据
            browser.execute_cdp_cmd('Network.clearBrowserCookies', {})
            browser.execute_cdp_cmd('Network.clearBrowserCache', {})
            
            # 添加一些常见的Cookie来模拟真实用户
            common_cookies = [
                {'name': 'CONSENT', 'value': 'YES+', 'domain': '.bing.com'},
                {'name': 'SRCHHPGUSR', 'value': 'SRCHLANG=en', 'domain': '.bing.com'}
            ]
            
            for cookie in common_cookies:
                try:
                    browser.execute_cdp_cmd('Network.setCookie', {
                        'name': cookie['name'],
                        'value': cookie['value'],
                        'domain': cookie['domain'],
                        'path': '/',
                    })
                except Exception as e:
                    logger.debug(f"设置Cookie失败: {e}")
                    
        except Exception as e:
            logger.warning(f"执行CDP命令时出错: {e}")
        
        logger.info("浏览器配置完成")
        return browser
    
    def _try_click_suggestion(self, browser):
        """
        尝试查找并点击Bing的"你是否想要搜索..."建议
        
        参数:
            browser: 浏览器实例
            
        返回:
            bool: 是否成功点击了建议
        """
        logger.info("检查页面上是否有搜索建议...")
        
        # 尝试多种可能的XPath模式来查找搜索建议
        suggestion_xpath_patterns = [
            "//a[contains(text(), 'Did you mean')]",  # 英文"你是否想要"
            "//a[contains(text(), 'mean:')]",  # 英文简化版
            "//a[contains(text(), 'Search instead for')]",  # 英文"改为搜索"
            "//a[contains(text(), '您是否想要:')]",  # 中文"你是否想要"
            "//a[contains(text(), '您是否想找:')]",  # 中文变体
            "//a[contains(text(), '您要查找的是不是:')]",  # 中文变体
            "//span[contains(text(), 'Did you mean')]/following::a[1]",  # 英文后面的第一个链接
            "//span[contains(text(), '您是否想要')]/following::a[1]",  # 中文后面的第一个链接
            "//div[contains(@class, 'b_suggestionText')]/a",  # 通过类查找建议文本
            "//div[contains(@class, 'suggestion')]/a",  # 通过更通用的类查找
            "//div[contains(@id, 'sp_requery')]/a",  # 通过ID查找
            "//div[contains(@class, 'b_subModule')]//a[contains(@class, 'b_restorableLink')]",  # 用于可恢复链接
            # 检查内嵌iframe中可能存在的选择器
            "//iframe[contains(@src, 'suggestions')]/following::a[1]",
            "//iframe//a[contains(text(), 'Did you mean')]",
        ]
        
        # 首先检查主文档
        for xpath in suggestion_xpath_patterns:
            try:
                elements = browser.find_elements_by_xpath(xpath)
                if elements:
                    suggestion_link = elements[0]
                    suggestion_text = suggestion_link.text.strip()
                    if suggestion_text:
                        logger.info(f"找到搜索建议: '{suggestion_text}'，尝试点击...")
                        # 使用JavaScript点击，更可靠
                        browser.execute_script("arguments[0].click();", suggestion_link)
                        # 等待页面加载
                        time.sleep(3)
                        logger.info("成功点击搜索建议")
                        return True
            except Exception as e:
                logger.debug(f"尝试XPath '{xpath}' 失败: {e}")
        
        # 检查是否有iframe，如果有，尝试在iframe中查找建议
        try:
            iframes = browser.find_elements_by_tag_name("iframe")
            if iframes:
                logger.info(f"找到 {len(iframes)} 个iframe，尝试检查其中的搜索建议...")
                
                for i, iframe in enumerate(iframes):
                    try:
                        browser.switch_to.frame(iframe)
                        logger.debug(f"已切换到iframe {i+1}")
                        
                        # 在iframe中尝试所有XPath模式
                        for xpath in suggestion_xpath_patterns:
                            try:
                                iframe_elements = browser.find_elements_by_xpath(xpath)
                                if iframe_elements:
                                    suggestion_link = iframe_elements[0]
                                    suggestion_text = suggestion_link.text.strip()
                                    if suggestion_text:
                                        logger.info(f"在iframe中找到搜索建议: '{suggestion_text}'，尝试点击...")
                                        browser.execute_script("arguments[0].click();", suggestion_link)
                                        time.sleep(3)
                                        browser.switch_to.default_content()
                                        logger.info("成功点击iframe中的搜索建议")
                                        return True
                            except Exception as e:
                                logger.debug(f"在iframe中尝试XPath '{xpath}' 失败: {e}")
                                
                        # 切回主文档，尝试下一个iframe
                        browser.switch_to.default_content()
                    except Exception as iframe_error:
                        logger.warning(f"处理iframe {i+1} 时出错: {iframe_error}")
                        # 确保切回主文档
                        browser.switch_to.default_content()
        except Exception as iframe_search_error:
            logger.warning(f"搜索iframe时出错: {iframe_search_error}")
            # 确保切回主文档
            try:
                browser.switch_to.default_content()
            except:
                pass
                
        # 如果没有找到或点击任何建议，返回False
        logger.info("页面上没有找到搜索建议或点击建议失败")
        return False

    def _is_no_results_page(self, browser, company_name):
        """
        检查当前页面是否显示"无搜索结果"
        
        参数:
            browser: 浏览器实例
            company_name: 搜索的公司名称
            
        返回:
            bool: 是否是无结果页面
        """
        logger.info(f"检查是否为无结果页面...")
        
        # 获取页面源代码和渲染后的HTML
        page_source = browser.page_source
        
        # 无结果的可能指示
        no_results_indicators = [
            f"There are no results for {company_name}",
            f"没有找到与{company_name}相关的结果",
            f"No results found for {company_name}",
            f"No results for {company_name}",
            f"Your search - {company_name} - did not match any documents",
            f"找不到您的查询词{company_name}相关的内容",
            "Sorry, there are no results",
            "抱歉，没有结果",
            "No results available",
            "没有可用结果",
            "We couldn't find any results",
            "我们找不到任何结果",
            "Try different keywords",
            "尝试不同的关键词",
            "Try another search",
            "尝试其他搜索"
        ]
        
        # 检查是否存在无结果指示
        for indicator in no_results_indicators:
            if indicator.lower() in page_source.lower():
                logger.warning(f"检测到无结果页面: '{indicator}'")
                return True
                
        # 即使检测到"无结果"指示，我们也查看页面是否有其他内容
        # 检查是否有任何搜索结果容器
        result_container_selectors = [
            "//div[contains(@class, 'b_results')]",
            "//div[contains(@class, 'b_content')]",
            "//ol[contains(@id, 'b_results')]",
            "//main"
        ]
        
        # 如果存在结果容器，检查是否包含任何结果项
        for selector in result_container_selectors:
            try:
                containers = browser.find_elements_by_xpath(selector)
                if containers:
                    # 检查容器内是否有内容
                    for container in containers:
                        if len(container.text.strip()) > 50:  # 如果有显著内容
                            logger.info(f"找到可能包含结果的容器: {selector}")
                            return False  # 认为页面有结果
            except Exception as e:
                logger.debug(f"检查结果容器选择器时出错: {e}")

        # 检查常见的无结果元素
        try:
            no_result_selectors = [
                "//div[contains(@class, 'b_no')]",
                "//div[contains(@class, 'b_noResults')]",
                "//div[contains(@id, 'b_no_results')]",
                "//div[contains(text(), 'No results')]",
                "//div[contains(text(), '没有结果')]",
                "//div[contains(@class, 'b_searchNoResults')]",
                "//div[contains(@class, 'b_suggestionNoResults')]"
            ]
            
            for selector in no_result_selectors:
                elements = browser.find_elements_by_xpath(selector)
                if elements and len(elements) > 0:
                    logger.warning(f"通过选择器 '{selector}' 检测到无结果元素")
                    return True
        except Exception as e:
            logger.debug(f"检查无结果选择器时出错: {e}")
        
        # 检查是否有任何链接，如果有大量链接存在，可能有结果
        try:
            links = browser.find_elements_by_tag_name("a")
            if len(links) > 10:  # 如果页面上有多个链接
                logger.info(f"页面上有 {len(links)} 个链接，可能有结果")
                return False  # 认为页面有结果
        except Exception as e:
            logger.debug(f"检查链接时出错: {e}")
            
        # 最终，检查页面DOM是否复杂
        try:
            all_elements = browser.find_elements_by_xpath("//*")
            if len(all_elements) > 100:  # 如果DOM复杂
                logger.info(f"页面DOM复杂 ({len(all_elements)} 个元素)，假定有结果")
                return False  # 认为页面有结果
        except Exception as e:
            logger.debug(f"检查DOM复杂度时出错: {e}")
        
        # 如果都没有匹配，则认为有结果
        logger.info("当前页面似乎包含搜索结果")
        return False
    
    def search_news(self, company_name, driver=None, save_html=True):
        """
        在Bing新闻上搜索公司相关新闻
        
        参数:
            company_name (str): 要搜索的公司名称
            driver (WebDriver, optional): 可选的WebDriver实例，如果不提供则创建新实例
            save_html (bool): 是否保存原始HTML，默认为True
        
        返回:
            list: 包含新闻数据的列表
        """
        start_time = time.time()
        self.company_name = company_name
        self.html_save_dir = os.path.join(self.output_dir, "raw_html", self.company_name)
        os.makedirs(self.html_save_dir, exist_ok=True)
        
        # 确保浏览器已配置
        if driver:
            self.browser = driver
            logger.info("使用提供的WebDriver实例")
        else:
            if not hasattr(self, 'browser') or self.browser is None:
                self.browser = self._setup_browser()
        
        all_news = []
        # 构建正常搜索和精确匹配搜索的URL
        search_urls = []
        
        # 正常搜索URL
        standard_search_url = f"https://www.bing.com/news/search?q={quote(company_name)}"
        search_urls.append(standard_search_url)
        
        # 精确匹配搜索URL
        exact_match_url = f"https://www.bing.com/news/search?q=\"{quote(company_name)}\""
        search_urls.append(exact_match_url)
        
        # 添加时间范围搜索URL
        time_filters = [
            ("qdr:d", "过去24小时"),
            ("qdr:w", "过去一周"),
            ("qdr:m", "过去一个月")
        ]
        
        for time_code, time_description in time_filters:
            time_url = f"{standard_search_url}&filters={time_code}"
            search_urls.append((time_url, time_description))
        
        # 添加英文新闻过滤
        search_urls.append(f"{standard_search_url}&cc=us")
        search_urls.append(f"{standard_search_url}&cc=gb")
        
        # 跟踪重试次数
        retry_count = 0
        max_retries = 3
        success = False
        used_url = None
        
        # 尝试每个URL直到成功
        while not success and retry_count < max_retries:
            for search_url in search_urls:
                url_description = ""
                if isinstance(search_url, tuple):
                    search_url, url_description = search_url
                
                logger.info(f"尝试{url_description}搜索URL: {search_url}")
                
                try:
                    # 添加随机延迟以模拟真实用户行为
                    time.sleep(random.uniform(1, 3))
                    
                    # 首先访问Bing主页
                    self.browser.get("https://www.bing.com/")
                    time.sleep(random.uniform(2, 4))
                    
                    # 然后导航到搜索URL
                    self.browser.get(search_url)
                    
                    # 添加随机等待时间，模拟真实用户行为
                    time.sleep(random.uniform(3, 5))
                    
                    # 检查是否有验证码或访问受限页面
                    if self._is_captcha_page() or self._is_access_denied():
                        logger.warning("检测到验证码或访问受限页面，尝试下一个URL")
                        continue
                    
                    # 检查是否为"无结果"页面
                    if self._check_no_results():
                        logger.info(f"在URL {search_url} 中没有找到结果，尝试下一个URL")
                        continue
                    
                    # 模拟滚动以加载更多内容
                    self._scroll_page()
                    
                    # 随机停留，模拟用户查看内容的行为
                    time.sleep(random.uniform(2, 4))
                    
                    # 获取页面HTML
                    page_html = self.browser.page_source
                    
                    # 保存原始HTML
                    if save_html:
                        timestamp = int(time.time())
                        html_filename = f"bing_news_{self.company_name.replace(' ', '_')}_{timestamp}.html"
                        html_path = os.path.join(self.html_save_dir, html_filename)
                        with open(html_path, 'w', encoding='utf-8') as f:
                            f.write(page_html)
                        logger.info(f"已保存HTML到 {html_path}")
                    
                    # 在页面上查找新闻文章元素
                    news_elements = self.browser.find_elements(By.XPATH, "//div[contains(@class, 'news-card')]")
                    
                    # 如果没有找到标准新闻卡片，尝试其他可能的选择器
                    if not news_elements:
                        news_elements = self.browser.find_elements(By.XPATH, "//div[contains(@class, 'newsitem')]")
                    
                    if not news_elements:
                        news_elements = self.browser.find_elements(By.XPATH, "//div[contains(@class, 'card')]")
                    
                    if not news_elements:
                        # 尝试使用Parsel解析HTML寻找结果
                        selector = Selector(text=page_html)
                        # 尝试多种可能的选择器模式
                        article_selectors = [
                            "//div[contains(@class, 'news-card')]",
                            "//div[contains(@class, 'newsitem')]",
                            "//div[contains(@class, 'card')]",
                            "//div[contains(@class, 'item')]//a[contains(@class, 'title')]/..",
                            "//div[contains(@class, 'news')]//a[contains(@href, 'news')]/..",
                            "//div[contains(@id, 'news')]//a",
                            "//div[@id='results']//div[contains(@class, 'result')]"
                        ]
                        
                        for selector_pattern in article_selectors:
                            article_elements = selector.xpath(selector_pattern)
                            if article_elements:
                                logger.info(f"使用选择器 {selector_pattern} 找到 {len(article_elements)} 个结果")
                                
                                # 解析找到的元素
                                for article in article_elements:
                                    try:
                                        # 尝试不同的标题选择器
                                        title_selectors = [
                                            ".//a[contains(@class, 'title')]//text()",
                                            ".//h3//text()",
                                            ".//a//text()"
                                        ]
                                        
                                        title = None
                                        for title_selector in title_selectors:
                                            title_text = article.xpath(title_selector).getall()
                                            if title_text:
                                                title = "".join(title_text).strip()
                                                break
                                        
                                        # 尝试不同的链接选择器
                                        link_selectors = [
                                            ".//a[contains(@class, 'title')]/@href",
                                            ".//a[1]/@href",
                                            ".//a/@href"
                                        ]
                                        
                                        link = None
                                        for link_selector in link_selectors:
                                            link_href = article.xpath(link_selector).get()
                                            if link_href:
                                                link = link_href.strip()
                                                break
                                        
                                        # 尝试不同的日期选择器
                                        date_selectors = [
                                            ".//span[contains(@class, 'date')]//text()",
                                            ".//span[contains(@class, 'time')]//text()",
                                            ".//time//text()"
                                        ]
                                        
                                        date = None
                                        for date_selector in date_selectors:
                                            date_text = article.xpath(date_selector).get()
                                            if date_text:
                                                date = date_text.strip()
                                                break
                                        
                                        # 尝试不同的摘要选择器
                                        summary_selectors = [
                                            ".//p//text()",
                                            ".//div[contains(@class, 'snippet')]//text()",
                                            ".//div[contains(@class, 'desc')]//text()"
                                        ]
                                        
                                        summary = None
                                        for summary_selector in summary_selectors:
                                            summary_text = article.xpath(summary_selector).getall()
                                            if summary_text:
                                                summary = "".join(summary_text).strip()
                                                break
                                        
                                        if title and link:
                                            news_item = {
                                                "title": title,
                                                "link": link,
                                                "date": date if date else "未知日期",
                                                "summary": summary if summary else "",
                                                "source": "Bing News",
                                                "company": company_name,
                                                "timestamp": datetime.now().isoformat()
                                            }
                                            
                                            # 避免重复添加
                                            if news_item not in all_news:
                                                all_news.append(news_item)
                                    except Exception as e:
                                        logger.error(f"解析文章时出错: {e}")
                                
                                if all_news:
                                    success = True
                                    used_url = search_url
                                    break
                    
                    # 如果通过WebDriver找到了元素，处理它们
                    if news_elements and not all_news:
                        logger.info(f"找到 {len(news_elements)} 个新闻元素")
                        
                        for element in news_elements:
                            try:
                                # 尝试获取标题
                                title_element = element.find_element(By.XPATH, ".//a[contains(@class, 'title')] | .//h3 | .//a")
                                title = title_element.text.strip() if title_element else ""
                                
                                # 尝试获取链接
                                link = title_element.get_attribute('href') if title_element else ""
                                
                                # 尝试获取日期
                                try:
                                    date_element = element.find_element(By.XPATH, ".//span[contains(@class, 'date')] | .//span[contains(@class, 'time')] | .//time")
                                    date = date_element.text.strip() if date_element else "未知日期"
                                except:
                                    date = "未知日期"
                                
                                # 尝试获取摘要
                                try:
                                    summary_element = element.find_element(By.XPATH, ".//p | .//div[contains(@class, 'snippet')] | .//div[contains(@class, 'desc')]")
                                    summary = summary_element.text.strip() if summary_element else ""
                                except:
                                    summary = ""
                                
                                if title and link:
                                    news_item = {
                                        "title": title,
                                        "link": link,
                                        "date": date,
                                        "summary": summary,
                                        "source": "Bing News",
                                        "company": company_name,
                                        "timestamp": datetime.now().isoformat()
                                    }
                                    
                                    # 避免重复添加
                                    if news_item not in all_news:
                                        all_news.append(news_item)
                            except Exception as e:
                                logger.error(f"处理新闻元素时出错: {e}")
                    
                    if all_news:
                        success = True
                        used_url = search_url
                        break
                    
                except TimeoutException:
                    logger.warning(f"访问URL超时: {search_url}")
                except Exception as e:
                    logger.error(f"搜索过程中出错: {e}")
            
            if not success:
                retry_count += 1
                if retry_count < max_retries:
                    wait_time = random.uniform(10, 15)
                    logger.info(f"重试 {retry_count}/{max_retries}，等待 {wait_time:.2f} 秒...")
                    time.sleep(wait_time)
                    
                    # 重置浏览器以避免潜在的状态问题
                    try:
                        self.browser.quit()
                    except:
                        pass
                    self.browser = self._setup_browser()
        
        end_time = time.time()
        duration = end_time - start_time
        
        if success:
            logger.info(f"搜索成功完成，使用URL: {used_url}")
            logger.info(f"找到 {len(all_news)} 条新闻，耗时 {duration:.2f} 秒")
        else:
            logger.warning(f"在所有重试后未能找到新闻，耗时 {duration:.2f} 秒")
        
        return all_news
    
    def _check_no_results(self):
        """检查是否为无结果页面"""
        try:
            # 尝试多种可能的"无结果"指示器
            no_results_texts = [
                "没有找到结果",
                "No results found",
                "We couldn't find any results",
                "Try different keywords",
                "尝试不同的关键词",
                "0 results"
            ]
            
            page_text = self.browser.page_source.lower()
            for text in no_results_texts:
                if text.lower() in page_text:
                    return True
            
            # 检查是否存在特定的无结果元素
            try:
                no_results_element = self.browser.find_element(By.XPATH, "//div[contains(@class, 'no-results')]")
                if no_results_element:
                    return True
            except:
                pass
            
            # 检查结果数量是否为零
            try:
                results_count_element = self.browser.find_element(By.XPATH, "//span[contains(@class, 'count')]")
                if results_count_element and ('0' in results_count_element.text or '零' in results_count_element.text):
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            logger.error(f"检查无结果页面时出错: {e}")
            return False
    
    def _is_captcha_page(self):
        """检查是否遇到验证码页面"""
        try:
            captcha_indicators = [
                "robot", "captcha", "verify", "challenge", "human", 
                "验证", "机器人", "人机", "验证码"
            ]
            
            page_source = self.browser.page_source.lower()
            for indicator in captcha_indicators:
                if indicator in page_source:
                    return True
            
            # 检查是否有验证码图像
            try:
                captcha_img = self.browser.find_element(By.XPATH, "//img[contains(@src, 'captcha') or contains(@src, 'challenge')]")
                if captcha_img:
                    return True
            except:
                pass
            
            return False
        except Exception as e:
            logger.error(f"检查验证码页面时出错: {e}")
            return False
    
    def _is_access_denied(self):
        """检查是否访问被拒绝"""
        try:
            denied_indicators = [
                "access denied", "denied access", "blocked", 
                "访问被拒绝", "拒绝访问", "禁止访问", "无法访问"
            ]
            
            page_source = self.browser.page_source.lower()
            for indicator in denied_indicators:
                if indicator in page_source:
                    return True
            
            return False
        except Exception as e:
            logger.error(f"检查访问拒绝时出错: {e}")
            return False
    
    def _scroll_page(self):
        """模拟滚动页面以加载更多内容"""
        try:
            # 获取页面高度
            last_height = self.browser.execute_script("return document.body.scrollHeight")
            
            # 随机滚动3-5次
            scroll_count = random.randint(3, 5)
            
            for i in range(scroll_count):
                # 滚动到页面底部
                self.browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                
                # 添加随机等待时间，模拟真实用户行为
                time.sleep(random.uniform(1, 2))
                
                # 计算新的滚动高度
                new_height = self.browser.execute_script("return document.body.scrollHeight")
                
                # 如果高度没有变化，说明已经到底部
                if new_height == last_height:
                    break
                
                last_height = new_height
                
            # 随机滚动回页面中部
            middle_position = last_height / 2
            self.browser.execute_script(f"window.scrollTo(0, {middle_position});")
            time.sleep(random.uniform(1, 2))
            
        except Exception as e:
            logger.error(f"滚动页面时出错: {e}")


def crawl_bing_news(company_name: str, limit: int = 20) -> Dict[str, Any]:
    """
    爬取Bing新闻中有关公司的信息
    
    Args:
        company_name: 公司名称
        limit: 最大结果数量
        
    Returns:
        爬取结果
    """
    crawler = BingNewsCrawler()
    articles = crawler.search_news(company_name, limit)
    
    result = {
        "source": "Bing News",
        "query": company_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "articles": articles
    }
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "Henderson Land"  # 使用一个知名香港建筑公司作为测试
    result = crawl_bing_news(test_company)
    print(f"Found {len(result['articles'])} news articles for '{test_company}'")
    for article in result['articles']:
        print(f"- {article['title']} ({article['source']}, {article['date']})")
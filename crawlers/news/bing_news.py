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
from urllib.parse import urljoin, quote_plus, quote
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
        logger.info("开始配置浏览器...")
        
        try:
            # 使用最简单的配置创建浏览器实例
            # 仅添加必要的选项以避免兼容性问题
            options = uc.ChromeOptions()
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            
            # 随机选择用户代理
            user_agents = [
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
            ]
            options.add_argument(f'--user-agent={random.choice(user_agents)}')
            
            # 设置浏览器首选项 (最小化配置)
            prefs = {
                'profile.default_content_setting_values.notifications': 2,
                'profile.managed_default_content_settings.images': 1
            }
            options.add_experimental_option('prefs', prefs)
            
            logger.info("正在创建Chrome浏览器...")
            browser = uc.Chrome(options=options)
            browser.set_page_load_timeout(60)
            logger.info("Chrome浏览器创建成功")
            
            return browser
            
        except Exception as e:
            logger.error(f"创建Chrome浏览器失败: {e}")
            # 如果上面的方法失败，尝试使用最基本的配置
            logger.info("尝试使用基本配置创建浏览器...")
            try:
                browser = uc.Chrome()
                logger.info("使用基本配置创建浏览器成功")
                return browser
            except Exception as e2:
                logger.error(f"使用基本配置创建浏览器也失败: {e2}")
                raise Exception(f"无法创建浏览器: {e} -> {e2}")
    
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
    
    def search_news(self, company_name: str, limit: int = 20) -> List[Dict]:
        """
        在Bing新闻上搜索公司相关新闻
        
        Args:
            company_name: 公司名称
            limit: 最大结果数量
            
        Returns:
            搜索结果列表，每个元素为一个新闻信息字典
        """
        logger.info(f"Searching for news about: {company_name}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("www.bing.com")
        
        # 构建搜索URL - 使用quote而不是quote_plus以提高兼容性
        search_url = f"{self.BASE_URL}?q={quote(company_name)}"
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        browser = None
        try:
            # 使用无头浏览器获取动态内容
            browser = self._setup_browser()
            
            # 首先访问Bing主页
            logger.info("访问Bing主页...")
            browser.get("https://www.bing.com/")
            time.sleep(random.uniform(2, 3))
            
            # 然后访问新闻搜索页面
            logger.info(f"访问搜索URL: {search_url}")
            browser.get(search_url)
            
            # 等待页面加载
            time.sleep(random.uniform(5, 7))
            
            # 保存原始页面内容用于调试
            logger.info("获取页面内容...")
            page_source = browser.page_source
            
            # 保存原始数据
            logger.info("保存原始数据...")
            self.storage.save_raw_data("bing_news", page_source, company_name)
            
            # 滚动页面以加载更多内容
            logger.info("滚动页面加载更多内容...")
            try:
                for _ in range(3):
                    browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(1, 2))
            except Exception as e:
                logger.warning(f"滚动页面时出错: {e}")
            
            # 更新页面源代码
            page_source = browser.page_source
            
            # 使用Parsel解析HTML
            selector = Selector(text=page_source)
            
            # 尝试多种可能的新闻文章选择器
            article_selectors = [
                # 最新版本的选择器
                "div.news-card",
                "div.card-with-cluster",
                "div.news-card-body",
                # 备用选择器
                "div.newsitem",
                "div.sa_cc",
                "div.news-body",
                # 通用选择器
                "div.card",
                "div.item-info",
                # 极简选择器
                "div.algocore"
            ]
            
            articles = []
            found_selector = None
            
            # 尝试所有选择器直到找到匹配
            for article_selector in article_selectors:
                article_elements = selector.css(article_selector)
                if article_elements:
                    found_selector = article_selector
                    logger.info(f"找到 {len(article_elements)} 个新闻元素，使用选择器 '{article_selector}'")
                    
                    for article in article_elements:
                        try:
                            # 尝试不同的标题选择器
                            title_selectors = [
                                "a.title::text", "h3::text", "a.news-card-title::text",
                                "div.title::text", "h4::text", "a::text"
                            ]
                            
                            # 尝试提取标题
                            title = None
                            for title_selector in title_selectors:
                                title_text = article.css(title_selector).get()
                                if title_text:
                                    title = clean_text(title_text)
                                    break
                            
                            # 尝试不同的链接选择器
                            link_selectors = [
                                "a.title::attr(href)", "a.news-card-title::attr(href)",
                                "a::attr(href)"
                            ]
                            
                            # 尝试提取链接
                            link = None
                            for link_selector in link_selectors:
                                link_href = article.css(link_selector).get()
                                if link_href:
                                    link = link_href
                                    # 确保链接完整
                                    if not link.startswith(('http://', 'https://')):
                                        link = urljoin("https://www.bing.com", link)
                                    break
                            
                            # 尝试不同的来源选择器
                            source_selectors = [
                                "div.source::text", "span.source::text",
                                "span.provider::text", "cite::text"
                            ]
                            
                            # 尝试提取来源
                            source = None
                            for source_selector in source_selectors:
                                source_text = article.css(source_selector).get()
                                if source_text:
                                    source = clean_text(source_text)
                                    break
                            
                            # 尝试不同的日期选择器
                            date_selectors = [
                                "span.datetime::text", "span.date::text",
                                "span.time::text", "span.timestamp::text"
                            ]
                            
                            # 尝试提取日期
                            date = None
                            for date_selector in date_selectors:
                                date_text = article.css(date_selector).get()
                                if date_text:
                                    date = clean_text(date_text)
                                    break
                            
                            # 尝试不同的摘要选择器
                            summary_selectors = [
                                "p::text", "div.snippet::text",
                                "div.snippet-content::text", "div.description::text"
                            ]
                            
                            # 尝试提取摘要
                            summary = None
                            for summary_selector in summary_selectors:
                                summary_text = article.css(summary_selector).get()
                                if summary_text:
                                    summary = clean_text(summary_text)
                                    break
                            
                            # 如果找到标题和链接，添加到结果
                            if title and link:
                                news_item = {
                                    'title': title,
                                    'url': link,
                                    'source': source or "Unknown Source",
                                    'date': format_date(date) if date else "",
                                    'summary': summary or "",
                                }
                                
                                articles.append(news_item)
                                
                                # 达到限制数量后停止
                                if len(articles) >= limit:
                                    break
                                    
                        except Exception as e:
                            logger.error(f"解析新闻文章时出错: {e}")
                    
                    # 如果找到足够的文章，停止尝试其他选择器
                    if articles:
                        break
            
            # 如果没有找到新闻，尝试直接从页面文本提取
            if not articles:
                logger.warning("未找到新闻元素，尝试直接从页面提取链接...")
                
                # 尝试提取所有链接及其文本
                try:
                    links = browser.find_elements(By.TAG_NAME, "a")
                    
                    for link in links:
                        try:
                            href = link.get_attribute('href')
                            text = link.text.strip()
                            
                            # 检查是否为新闻链接
                            if (href and text and len(text) > 20 and
                                not href.startswith("https://www.bing.com") and 
                                "news" not in href):
                                
                                news_item = {
                                    'title': text,
                                    'url': href,
                                    'source': "Unknown Source",
                                    'date': "",
                                    'summary': "",
                                }
                                
                                articles.append(news_item)
                                
                                # 达到限制数量后停止
                                if len(articles) >= limit:
                                    break
                        except Exception as e:
                            continue
                except Exception as e:
                    logger.error(f"提取链接时出错: {e}")
            
            logger.info(f"找到 {len(articles)} 条关于 '{company_name}' 的新闻")
            
            # 保存结构化数据
            if articles:
                normalized_name = normalize_company_name(company_name)
                self.storage.save_company_data(
                    normalized_name, 
                    "news", 
                    {"source": "bing_news", "articles": articles}
                )
            
            return articles
            
        except Exception as e:
            logger.error(f"搜索Bing新闻时出错: {e}")
            return []
        finally:
            if browser:
                try:
                    browser.quit()
                    logger.info("浏览器已关闭")
                except:
                    pass


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
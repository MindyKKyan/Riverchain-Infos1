"""
Google新闻爬虫 - Google News Crawler
爬取Google新闻中有关公司的新闻报道
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
from urllib.parse import urljoin, quote_plus

from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name, format_date

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('google_news')

class GoogleNewsCrawler:
    """Google新闻爬虫"""
    
    BASE_URL = "https://www.google.com/search"
    
    def __init__(self):
        self.anticrawl = get_anticrawl_manager()
        self.storage = get_storage_manager()
        self.session = HTMLSession()
    
    def _setup_browser(self) -> uc.Chrome:
        """设置无头浏览器"""
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        browser = uc.Chrome(options=options)
        return browser
    
    def search_news(self, company_name: str, limit: int = 20) -> List[Dict]:
        """
        搜索有关公司的新闻
        
        Args:
            company_name: 公司名称
            limit: 最大结果数量
            
        Returns:
            搜索结果列表，每个元素为一个新闻信息字典
        """
        logger.info(f"Searching for news about: {company_name}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("www.google.com")
        
        # 构建查询参数
        params = {
            'q': f"{company_name} news",
            'tbm': 'nws',
            'hl': 'en',
            'gl': 'hk'
        }
        
        # 构建查询URL
        query_string = '&'.join([f"{k}={quote_plus(str(v))}" for k, v in params.items()])
        url = f"{self.BASE_URL}?{query_string}"
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据
            self.storage.save_raw_data("google_news", page_source, company_name)
            
            # 解析搜索结果
            selector = Selector(text=page_source)
            
            articles = []
            # 更新选择器以适应Google新闻的新HTML结构
            for result in selector.css('div.SoaBEf'):
                try:
                    # 提取标题和链接
                    title_elem = result.css('div.n0jPhd::text').get() or result.css('div.mCBkyc::text').get()
                    link_elem = result.css('a.WlydOe::attr(href)').get() or result.css('a::attr(href)').get()
                    
                    # 如果找不到标题或链接，跳过
                    if not title_elem or not link_elem:
                        continue
                    
                    # 提取链接中的真实URL
                    if '/url?q=' in link_elem:
                        link_elem = link_elem.split('/url?q=')[1].split('&')[0]
                    
                    # 提取新闻来源和日期
                    source_date_elem = result.css('div.CEMjEf span::text').get()
                    source = ""
                    date = ""
                    if source_date_elem:
                        parts = source_date_elem.split(' · ')
                        if len(parts) >= 2:
                            source = parts[0].strip()
                            date = parts[1].strip()
                    
                    # 提取摘要
                    summary_elem = result.css('div.GI74Re::text').get()
                    
                    article = {
                        'title': clean_text(title_elem),
                        'url': link_elem,
                        'source': source,
                        'date': format_date(date) if date else "",
                        'summary': clean_text(summary_elem) if summary_elem else "",
                    }
                    
                    articles.append(article)
                    
                    # 达到限制数量后停止
                    if len(articles) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error parsing Google News result: {e}")
            
            logger.info(f"Found {len(articles)} news articles about '{company_name}'")
            
            # 保存结构化数据
            if articles:
                normalized_name = normalize_company_name(company_name)
                self.storage.save_company_data(
                    normalized_name, 
                    "news", 
                    {"source": "google_news", "articles": articles}
                )
            
            return articles
            
        except Exception as e:
            logger.error(f"Error searching Google News: {e}")
            return []
        finally:
            browser.quit()


def crawl_google_news(company_name: str, limit: int = 20) -> Dict[str, Any]:
    """
    爬取Google新闻中有关公司的信息
    
    Args:
        company_name: 公司名称
        limit: 最大结果数量
        
    Returns:
        爬取结果
    """
    crawler = GoogleNewsCrawler()
    articles = crawler.search_news(company_name, limit)
    
    result = {
        "source": "Google News",
        "query": company_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "articles": articles
    }
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "Henderson Land"  # 使用一个知名香港建筑公司作为测试
    result = crawl_google_news(test_company)
    print(f"Found {len(result['articles'])} news articles for '{test_company}'")
    for article in result['articles']:
        print(f"- {article['title']} ({article['source']}, {article['date']})")

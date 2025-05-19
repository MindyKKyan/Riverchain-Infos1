"""
Twitter公开信息爬虫 - Twitter Public Information Crawler
由于Twitter API限制，这个爬虫通过网页抓取公开信息
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
from urllib.parse import urlencode, quote_plus

from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name, format_date

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('twitter_public')

class TwitterPublicCrawler:
    """Twitter公开信息爬虫"""
    
    # 使用Nitter作为Twitter的替代前端，避免登录要求
    # 更新Nitter实例以增加稳定性
    BASE_URL = "https://nitter.net/search"
    ALTERNATE_URLS = [
        "https://nitter.cz/search",
        "https://nitter.poast.org/search",
        "https://nitter.net/search"
    ]
    
    def __init__(self):
        self.anticrawl = get_anticrawl_manager()
        self.storage = get_storage_manager()
        self.session = HTMLSession()
        self.base_url = self._find_working_instance()
    
    def _find_working_instance(self) -> str:
        """尝试找到一个可用的Nitter实例"""
        for url in self.ALTERNATE_URLS:
            try:
                response = self.session.get(url, timeout=5)
                if response.status_code == 200:
                    logger.info(f"Using Nitter instance: {url}")
                    return url
            except Exception as e:
                logger.warning(f"Nitter instance {url} not available: {e}")
        
        # 默认返回第一个
        logger.warning("No working Nitter instance found, using default")
        return self.ALTERNATE_URLS[0]
    
    def _setup_browser(self) -> uc.Chrome:
        """设置无头浏览器"""
        options = uc.ChromeOptions()
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        browser = uc.Chrome(options=options)
        return browser
    
    def search_tweets(self, company_name: str, limit: int = 20) -> List[Dict]:
        """
        搜索有关公司的推文
        
        Args:
            company_name: 公司名称
            limit: 最大结果数量
            
        Returns:
            搜索结果列表，每个元素为一个推文信息字典
        """
        logger.info(f"Searching for tweets about: {company_name}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("nitter.net")
        
        # 构建查询参数
        params = {
            'f': 'tweets',
            'q': f"{company_name} construction",
        }
        
        url = f"{self.base_url}?{urlencode(params)}"
        
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
            self.storage.save_raw_data("twitter_public", page_source, company_name)
            
            # 解析搜索结果
            selector = Selector(text=page_source)
            
            tweets = []
            # 推文选择器（适用于Nitter）
            for result in selector.css('div.timeline-item'):
                try:
                    # 提取用户信息
                    author_elem = result.css('a.username::text').get()
                    author_handle_elem = result.css('a.username::text').get()
                    
                    # 提取推文内容
                    text_elem = result.css('div.tweet-content').get()
                    date_elem = result.css('span.tweet-date a::text').get()
                    
                    # 如果找不到作者或内容，跳过
                    if not author_elem or not text_elem:
                        continue
                    
                    tweet = {
                        'text': clean_text(text_elem),
                        'author': clean_text(author_elem),
                        'author_handle': clean_text(author_handle_elem).strip('@'),
                        'date': format_date(date_elem) if date_elem else "",
                        'platform': 'Twitter',
                        'url': result.css('a.tweet-link::attr(href)').get(),
                    }
                    
                    # 提取互动数据
                    stats = result.css('div.tweet-stats')
                    if stats:
                        tweet['comments'] = clean_text(stats.css('div.icon-container:nth-child(1) span.tweet-stat::text').get() or "0")
                        tweet['retweets'] = clean_text(stats.css('div.icon-container:nth-child(2) span.tweet-stat::text').get() or "0")
                        tweet['likes'] = clean_text(stats.css('div.icon-container:nth-child(3) span.tweet-stat::text').get() or "0")
                    
                    # 提取图片链接（如果有）
                    img_elem = result.css('div.attachment img::attr(src)').get()
                    if img_elem:
                        tweet['media_url'] = img_elem
                    
                    tweets.append(tweet)
                    
                    # 达到限制数量后停止
                    if len(tweets) >= limit:
                        break
                        
                except Exception as e:
                    logger.error(f"Error parsing tweet: {e}")
            
            logger.info(f"Found {len(tweets)} tweets about '{company_name}'")
            
            # 保存结构化数据
            if tweets:
                normalized_name = normalize_company_name(company_name)
                self.storage.save_company_data(
                    normalized_name, 
                    "social", 
                    {"source": "twitter", "posts": tweets}
                )
            
            return tweets
            
        except Exception as e:
            logger.error(f"Error searching Twitter: {e}")
            return []
        finally:
            browser.quit()


def crawl_twitter_public(company_name: str, limit: int = 20) -> Dict[str, Any]:
    """
    爬取Twitter上有关公司的公开信息
    
    Args:
        company_name: 公司名称
        limit: 最大结果数量
        
    Returns:
        爬取结果
    """
    crawler = TwitterPublicCrawler()
    posts = crawler.search_tweets(company_name, limit)
    
    result = {
        "source": "Twitter",
        "query": company_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "posts": posts
    }
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "Henderson Land"  # 使用一个知名香港建筑公司作为测试
    result = crawl_twitter_public(test_company, 5)
    print(f"Found {len(result['posts'])} tweets for '{test_company}'")
    for post in result['posts']:
        print(f"- {post['author']}: {post['text'][:100]}...")
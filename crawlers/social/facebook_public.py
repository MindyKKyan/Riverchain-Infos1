"""
Facebook公开页面爬虫 - Facebook Public Page Crawler
由于Facebook限制，这个爬虫只能抓取公开的公司页面信息
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
import re
from urllib.parse import urlencode

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name, format_date

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('facebook_public')

class FacebookPublicCrawler:
    """Facebook公开页面爬虫"""
    
    SEARCH_URL = "https://www.google.com/search?q=site:facebook.com+{keyword}+company"
    BASE_URL = "https://www.facebook.com"
    
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
        # 添加这些参数以避免Facebook登录墙
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument('--disable-blink-features=AutomationControlled')
        browser = uc.Chrome(options=options)
        return browser
    
    def find_company_page(self, company_name: str) -> Optional[str]:
        """
        通过Google搜索找到公司的Facebook页面
        
        Args:
            company_name: 公司名称
            
        Returns:
            公司Facebook页面URL，如果找不到则返回None
        """
        logger.info(f"Searching for Facebook page of: {company_name}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("www.google.com")
        
        # 构建搜索URL
        search_url = self.SEARCH_URL.format(keyword=company_name.replace(' ', '+'))
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(search_url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 解析搜索结果
            selector = Selector(text=page_source)
            
            # 查找Facebook公司页面链接
            for link in selector.css('a::attr(href)').getall():
                if "facebook.com/" in link and "/posts/" not in link:
                    match = re.search(r'(https://\w+\.facebook\.com/[^/&?]+)', link)
                    if match:
                        return match.group(1)
            
            logger.info(f"No Facebook company page found for {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding Facebook page: {e}")
            return None
        finally:
            browser.quit()
    
    def scrape_company_info(self, facebook_url: str) -> Dict[str, Any]:
        """
        抓取Facebook公司页面信息
        
        Args:
            facebook_url: Facebook公司页面URL
            
        Returns:
            公司信息字典
        """
        logger.info(f"Scraping Facebook page: {facebook_url}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("facebook.com")
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(facebook_url)
            
            # 等待页面加载，Facebook可能需要更长时间
            time.sleep(10)
            
            # 滚动页面以加载更多内容
            browser.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(2)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据
            self.storage.save_raw_data("facebook_company", page_source)
            
            # 解析公司信息
            selector = Selector(text=page_source)
            
            company_info = {
                'url': facebook_url,
                'platform': 'Facebook',
            }
            
            # 尝试处理登录墙
            if "log in or sign up" in page_source.lower():
                company_info['error'] = "Login required - only partial information available"
            
            # 尝试提取公司名称
            name_elem = selector.css('h1::text').get() or selector.css('title::text').get()
            if name_elem:
                company_info['name'] = clean_text(name_elem.split('|')[0] if '|' in name_elem else name_elem)
            
            # 尝试提取关于信息
            about_elems = selector.css('div[data-key="about"] span::text').getall()
            if about_elems:
                company_info['about'] = clean_text(' '.join(about_elems))
            
            # 尝试提取联系信息
            contact_elems = selector.css('div[data-key="contact_info"] a::text').getall()
            if contact_elems:
                company_info['contact'] = [clean_text(c) for c in contact_elems]
            
            # 尝试提取地址
            location_elems = selector.css('div[data-key="location"] span::text').getall()
            if location_elems:
                company_info['location'] = clean_text(' '.join(location_elems))
            
            # 尝试提取关注人数
            followers_elem = selector.css('span:contains("people follow this")::text').get()
            if followers_elem:
                match = re.search(r'([\d,]+)', followers_elem)
                if match:
                    company_info['followers'] = match.group(1)
            
            return company_info
            
        except Exception as e:
            logger.error(f"Error scraping Facebook page: {e}")
            return {'url': facebook_url, 'error': str(e)}
        finally:
            browser.quit()
    
    def scrape_recent_posts(self, facebook_url: str, limit: int = 10) -> List[Dict]:
        """
        抓取Facebook公司页面上的最新帖子
        
        Args:
            facebook_url: Facebook公司页面URL
            limit: 最大结果数量
            
        Returns:
            帖子列表
        """
        logger.info(f"Scraping Facebook posts from: {facebook_url}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("facebook.com")
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(facebook_url)
            
            # 等待页面加载，Facebook可能需要更长时间
            time.sleep(10)
            
            # 滚动几次页面以加载更多帖子
            for _ in range(3):
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(2)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据
            self.storage.save_raw_data("facebook_company_posts", page_source)
            
            # 解析帖子
            selector = Selector(text=page_source)
            
            posts = []
            
            # Facebook的选择器需要根据实际情况调整
            # 由于Facebook的反爬措施和频繁的HTML结构变化，这里的选择器很可能需要更新
            post_elements = selector.css('div[role="article"]')
            
            for post_elem in post_elements[:limit]:
                try:
                    # 提取内容
                    text_elem = post_elem.css('div[data-ad-comet-preview="message"] span::text').getall()
                    date_elem = post_elem.css('span[id*="jsc_c"] a span::text').get()
                    
                    # 提取帖子链接
                    link_elem = post_elem.css('a[aria-label*="comment"]::attr(href)').get()
                    post_url = link_elem if link_elem and link_elem.startswith('http') else None
                    
                    post = {
                        'text': clean_text(' '.join(text_elem)) if text_elem else "No text content available",
                        'date': clean_text(date_elem) if date_elem else "Date not available",
                        'platform': 'Facebook',
                        'url': post_url or facebook_url,
                    }
                    
                    # 提取互动数据（点赞、评论等）
                    likes_elem = post_elem.css('span[aria-label*="reactions"]::text').get()
                    comments_elem = post_elem.css('span[aria-label*="comments"]::text').get()
                    shares_elem = post_elem.css('span[aria-label*="shares"]::text').get()
                    
                    if likes_elem:
                        post['likes'] = clean_text(likes_elem)
                    if comments_elem:
                        post['comments'] = clean_text(comments_elem)
                    if shares_elem:
                        post['shares'] = clean_text(shares_elem)
                    
                    # 提取图片链接
                    img_elem = post_elem.css('img.i09qtzwb::attr(src)').get()
                    if img_elem:
                        post['media_url'] = img_elem
                    
                    posts.append(post)
                    
                except Exception as e:
                    logger.error(f"Error parsing Facebook post: {e}")
            
            logger.info(f"Found {len(posts)} Facebook posts")
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping Facebook posts: {e}")
            return []
        finally:
            browser.quit()


def crawl_facebook_public(company_name: str) -> Dict[str, Any]:
    """
    爬取Facebook上有关公司的公开信息
    
    Args:
        company_name: 公司名称
        
    Returns:
        爬取结果
    """
    crawler = FacebookPublicCrawler()
    
    # 查找公司Facebook页面
    facebook_url = crawler.find_company_page(company_name)
    
    result = {
        "source": "Facebook",
        "query": company_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if facebook_url:
        # 抓取公司信息
        company_info = crawler.scrape_company_info(facebook_url)
        result["company_info"] = company_info
        
        # 抓取公司帖子
        posts = crawler.scrape_recent_posts(facebook_url)
        result["posts"] = posts
        
        # 保存结构化数据
        normalized_name = normalize_company_name(company_name)
        storage_manager = get_storage_manager()
        storage_manager.save_company_data(
            normalized_name, 
            "social", 
            {"source": "facebook", "company_info": company_info, "posts": posts}
        )
    else:
        result["error"] = "Facebook company page not found"
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "Henderson Land Development"  # 使用一个知名香港建筑公司作为测试
    result = crawl_facebook_public(test_company)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("Company Info:")
        for key, value in result.get("company_info", {}).items():
            print(f"- {key}: {value}")
        
        print(f"\nFound {len(result.get('posts', []))} posts")
        for post in result.get("posts", [])[:2]:
            print(f"- Date: {post.get('date')}")
            print(f"  Text: {post.get('text')[:100]}...")
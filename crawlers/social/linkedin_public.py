"""
LinkedIn公开信息爬虫 - LinkedIn Public Information Crawler
由于LinkedIn限制，这个爬虫只能抓取公开的公司页面信息
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
import re

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('linkedin_public')

class LinkedInPublicCrawler:
    """LinkedIn公开信息爬虫"""
    
    SEARCH_URL = "https://www.google.com/search?q=site:linkedin.com/company+{keyword}"
    
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
    
    def find_company_page(self, company_name: str) -> Optional[str]:
        """
        通过Google搜索找到公司的LinkedIn页面
        
        Args:
            company_name: 公司名称
            
        Returns:
            公司LinkedIn页面URL，如果找不到则返回None
        """
        logger.info(f"Searching for LinkedIn page of: {company_name}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("www.google.com")
        
        # 构建更精确的搜索URL - 添加引号使搜索更精确
        search_url = self.SEARCH_URL.format(keyword=f'"{company_name}"'.replace(' ', '+'))
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(search_url)
            
            # 增加等待时间，确保页面完全加载
            time.sleep(5)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据用于调试
            self.storage.save_raw_data("linkedin_search", page_source, company_name)
            
            # 解析搜索结果
            selector = Selector(text=page_source)
            
            # 查找LinkedIn公司页面链接 - 改进正则表达式匹配
            for link in selector.css('a::attr(href)').getall():
                # 检查链接是否包含LinkedIn公司页面URL
                if "linkedin.com/company/" in link:
                    # 尝试从Google搜索结果URL中提取LinkedIn URL
                    match = re.search(r'(?:https?:\/\/)?(?:www\.)?linkedin\.com\/company\/[^&\s/?]+', link)
                    if match:
                        linkedin_url = match.group(0)
                        if not linkedin_url.startswith('http'):
                            linkedin_url = 'https://' + linkedin_url
                        logger.info(f"Found LinkedIn page: {linkedin_url}")
                        return linkedin_url
            
            # 尝试直接构建可能的LinkedIn URL作为备选方案
            normalized_name = company_name.lower().replace(' ', '-').replace(',', '').replace('.', '')
            alternative_url = f"https://www.linkedin.com/company/{normalized_name}"
            logger.info(f"Trying alternative LinkedIn URL: {alternative_url}")
            
            # 验证这个备选URL是否有效
            try:
                browser.get(alternative_url)
                time.sleep(3)
                if "Page not found" not in browser.title and "error" not in browser.title.lower():
                    logger.info(f"Alternative LinkedIn URL is valid: {alternative_url}")
                    return alternative_url
            except Exception as e:
                logger.warning(f"Error checking alternative URL: {e}")
            
            logger.info(f"No LinkedIn company page found for {company_name}")
            return None
            
        except Exception as e:
            logger.error(f"Error finding LinkedIn page: {e}")
            return None
        finally:
            browser.quit()
    
    def scrape_company_info(self, linkedin_url: str) -> Dict[str, Any]:
        """
        抓取LinkedIn公司页面信息
        
        Args:
            linkedin_url: LinkedIn公司页面URL
            
        Returns:
            公司信息字典
        """
        logger.info(f"Scraping LinkedIn page: {linkedin_url}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("linkedin.com")
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(linkedin_url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据
            self.storage.save_raw_data("linkedin_company", page_source)
            
            # 解析公司信息
            selector = Selector(text=page_source)
            
            company_info = {
                'url': linkedin_url,
                'platform': 'LinkedIn',
            }
            
            # 提取公司名称
            name_elem = selector.css('h1.org-top-card-summary__title::text').get()
            if name_elem:
                company_info['name'] = clean_text(name_elem)
            
            # 提取公司简介
            about_elem = selector.css('p.org-about-us-organization-description__text::text').get()
            if about_elem:
                company_info['description'] = clean_text(about_elem)
            
            # 提取公司基本信息
            info_sections = selector.css('dl.org-page-details__definition-list')
            for section in info_sections:
                keys = section.css('dt::text').getall()
                values = section.css('dd::text').getall()
                
                for i, key in enumerate(keys):
                    if i < len(values):
                        company_info[clean_text(key).lower().replace(' ', '_')] = clean_text(values[i])
            
            # 提取公司位置
            location_elem = selector.css('div.org-top-card-summary__headquarter::text').get()
            if location_elem:
                company_info['location'] = clean_text(location_elem)
            
            # 提取公司员工数量
            employees_elem = selector.css('div.org-top-card-summary__info-item::text').get()
            if employees_elem:
                company_info['employees'] = clean_text(employees_elem)
            
            return company_info
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn page: {e}")
            return {'url': linkedin_url, 'error': str(e)}
        finally:
            browser.quit()
    
    def search_company_posts(self, linkedin_url: str, limit: int = 10) -> List[Dict]:
        """
        抓取LinkedIn公司页面上的最新帖子
        
        Args:
            linkedin_url: LinkedIn公司页面URL
            limit: 最大结果数量
            
        Returns:
            帖子列表
        """
        logger.info(f"Scraping LinkedIn posts from: {linkedin_url}/posts")
        
        posts_url = f"{linkedin_url}/posts"
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("linkedin.com")
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(posts_url)
            
            # 等待页面加载
            time.sleep(5)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据
            self.storage.save_raw_data("linkedin_company_posts", page_source)
            
            # 解析帖子
            selector = Selector(text=page_source)
            
            posts = []
            # 帖子选择器（注意：LinkedIn结构可能经常变化，需要根据实际情况调整）
            post_elements = selector.css('div.ember-view.occludable-update')
            
            for post_elem in post_elements[:limit]:
                try:
                    # 提取内容
                    text_elem = post_elem.css('div.feed-shared-update-v2__description span.break-words::text').getall()
                    date_elem = post_elem.css('span.feed-shared-actor__sub-description span::text').get()
                    
                    post = {
                        'text': clean_text(' '.join(text_elem)) if text_elem else "",
                        'date': clean_text(date_elem) if date_elem else "",
                        'platform': 'LinkedIn',
                        'url': posts_url,  # 无法直接获取单条帖子URL
                    }
                    
                    # 提取互动数据
                    likes_elem = post_elem.css('button.social-details-social-counts__reactions-count span::text').get()
                    comments_elem = post_elem.css('button.social-details-social-counts__comments span::text').get()
                    
                    if likes_elem:
                        post['likes'] = clean_text(likes_elem)
                    if comments_elem:
                        post['comments'] = clean_text(comments_elem)
                    
                    # 提取图片链接
                    img_elem = post_elem.css('div.feed-shared-image img::attr(src)').get()
                    if img_elem:
                        post['media_url'] = img_elem
                    
                    posts.append(post)
                    
                except Exception as e:
                    logger.error(f"Error parsing LinkedIn post: {e}")
            
            logger.info(f"Found {len(posts)} LinkedIn posts")
            return posts
            
        except Exception as e:
            logger.error(f"Error scraping LinkedIn posts: {e}")
            return []
        finally:
            browser.quit()


def crawl_linkedin_public(company_name: str) -> Dict[str, Any]:
    """
    爬取LinkedIn上有关公司的公开信息
    
    Args:
        company_name: 公司名称
        
    Returns:
        爬取结果
    """
    crawler = LinkedInPublicCrawler()
    
    # 查找公司LinkedIn页面
    linkedin_url = crawler.find_company_page(company_name)
    
    result = {
        "source": "LinkedIn",
        "query": company_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if linkedin_url:
        # 抓取公司信息
        company_info = crawler.scrape_company_info(linkedin_url)
        result["company_info"] = company_info
        
        # 抓取公司帖子
        posts = crawler.search_company_posts(linkedin_url)
        result["posts"] = posts
        
        # 保存结构化数据
        normalized_name = normalize_company_name(company_name)
        storage_manager = get_storage_manager()
        storage_manager.save_company_data(
            normalized_name, 
            "social", 
            {"source": "linkedin", "company_info": company_info, "posts": posts}
        )
    else:
        result["error"] = "LinkedIn company page not found"
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "Henderson Land Development"  # 使用一个知名香港建筑公司作为测试
    result = crawl_linkedin_public(test_company)
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

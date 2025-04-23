"""
建筑行业新闻爬虫 - Construction Industry News Crawler
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
from urllib.parse import urljoin, urlencode

from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name, format_date, extract_domain

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('construction_news')

class ConstructionNewsCrawler:
    """建筑行业新闻爬虫"""
    
    # 建筑行业主要新闻网站列表
    NEWS_SOURCES = [
        {
            'name': 'Construction News',
            'url': 'https://www.constructionnews.co.uk/search?search={keyword}',
            'article_selector': 'div.search-result-item',
            'title_selector': 'h2.search-result-item__title a::text',
            'link_selector': 'h2.search-result-item__title a::attr(href)',
            'date_selector': 'span.search-result-item__date::text',
            'summary_selector': 'p.search-result-item__description::text',
            'image_selector': 'img.search-result-item__image::attr(src)',
            'base_url': 'https://www.constructionnews.co.uk',
        },
        {
            'name': 'Construction Enquirer',
            'url': 'https://www.constructionenquirer.com/?s={keyword}',
            'article_selector': 'article.post',
            'title_selector': 'h2.entry-title a::text',
            'link_selector': 'h2.entry-title a::attr(href)',
            'date_selector': 'time.entry-date::text',
            'summary_selector': 'div.entry-content p::text',
            'image_selector': 'img.attachment-full::attr(src)',
            'base_url': '',
        },
        {
            'name': 'Building.co.uk',
            'url': 'https://www.building.co.uk/search?search={keyword}',
            'article_selector': 'div.search-result-item',
            'title_selector': 'h2.search-result-item__title a::text',
            'link_selector': 'h2.search-result-item__title a::attr(href)',
            'date_selector': 'span.search-result-item__date::text',
            'summary_selector': 'p.search-result-item__description::text',
            'image_selector': 'img.search-result-item__image::attr(src)',
            'base_url': 'https://www.building.co.uk',
        },
        {
            'name': 'Construction Global',
            'url': 'https://www.constructionglobal.com/search?search={keyword}',
            'article_selector': 'div.search-result',
            'title_selector': 'h3 a::text',
            'link_selector': 'h3 a::attr(href)',
            'date_selector': 'span.date::text',
            'summary_selector': 'p.summary::text',
            'image_selector': 'img::attr(src)',
            'base_url': 'https://www.constructionglobal.com',
        }
    ]
    
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
    
    def search_all_sources(self, company_name: str, limit_per_source: int = 5) -> List[Dict]:
        """
        在所有建筑行业新闻源搜索公司相关新闻
        
        Args:
            company_name: 公司名称
            limit_per_source: 每个源的最大结果数量
            
        Returns:
            搜索结果列表，每个元素为一个新闻信息字典
        """
        logger.info(f"Searching for news about: {company_name} in construction industry news")
        
        all_articles = []
        
        # 使用无头浏览器
        browser = self._setup_browser()
        
        try:
            for source in self.NEWS_SOURCES:
                # 应用反爬虫延迟
                domain = extract_domain(source['url'].format(keyword='test'))
                self.anticrawl.delay_request(domain)
                
                # 构建搜索URL
                search_url = source['url'].format(keyword=company_name.replace(' ', '+'))
                
                logger.info(f"Searching {source['name']} at {search_url}")
                
                # 获取页面内容
                try:
                    browser.get(search_url)
                    
                    # 等待页面加载
                    time.sleep(3)
                    
                    # 获取页面内容
                    page_source = browser.page_source
                    
                    # 保存原始数据
                    self.storage.save_raw_data(f"construction_news_{source['name'].lower().replace(' ', '_')}", 
                                             page_source, company_name)
                    
                    # 解析搜索结果
                    selector = Selector(text=page_source)
                    
                    articles = []
                    for result in selector.css(source['article_selector']):
                        try:
                            # 提取标题和链接
                            title_elem = result.css(source['title_selector']).get()
                            link_elem = result.css(source['link_selector']).get()
                            
                            # 如果找不到标题或链接，跳过
                            if not title_elem or not link_elem:
                                continue
                            
                            # 处理相对URL
                            if source['base_url'] and not link_elem.startswith(('http://', 'https://')):
                                link_elem = urljoin(source['base_url'], link_elem)
                            
                            # 提取日期、摘要和图片
                            date_elem = result.css(source['date_selector']).get()
                            summary_elem = result.css(source['summary_selector']).get()
                            img_elem = result.css(source['image_selector']).get()
                            
                            article = {
                                'title': clean_text(title_elem),
                                'url': link_elem,
                                'source': source['name'],
                                'date': format_date(date_elem) if date_elem else "",
                                'summary': clean_text(summary_elem) if summary_elem else "",
                            }
                            
                            # 添加图片链接（如果有）
                            if img_elem:
                                if source['base_url'] and not img_elem.startswith(('http://', 'https://')):
                                    img_elem = urljoin(source['base_url'], img_elem)
                                article['image_url'] = img_elem
                            
                            articles.append(article)
                            
                            # 达到限制数量后停止
                            if len(articles) >= limit_per_source:
                                break
                                
                        except Exception as e:
                            logger.error(f"Error parsing news article from {source['name']}: {e}")
                    
                    logger.info(f"Found {len(articles)} articles from {source['name']}")
                    all_articles.extend(articles)
                    
                except Exception as e:
                    logger.error(f"Error searching {source['name']}: {e}")
            
            # 保存结构化数据
            if all_articles:
                normalized_name = normalize_company_name(company_name)
                self.storage.save_company_data(
                    normalized_name, 
                    "news", 
                    {"source": "construction_industry_news", "articles": all_articles}
                )
            
            return all_articles
            
        except Exception as e:
            logger.error(f"Error searching construction industry news: {e}")
            return []
        finally:
            browser.quit()


def crawl_construction_news(company_name: str, limit_per_source: int = 5) -> Dict[str, Any]:
    """
    爬取建筑行业新闻中有关公司的信息
    
    Args:
        company_name: 公司名称
        limit_per_source: 每个源的最大结果数量
        
    Returns:
        爬取结果
    """
    crawler = ConstructionNewsCrawler()
    articles = crawler.search_all_sources(company_name, limit_per_source)
    
    result = {
        "source": "Construction Industry News",
        "query": company_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "articles": articles
    }
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "Henderson Land"  # 使用一个知名香港建筑公司作为测试
    result = crawl_construction_news(test_company, 3)
    print(f"Found {len(result['articles'])} news articles for '{test_company}'")
    for article in result['articles']:
        print(f"- {article['title']} ({article['source']}, {article['date']})")
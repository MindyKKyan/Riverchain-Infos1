"""
国际项目招标信息爬虫 - International Tenders Crawler
爬取国际建筑项目招标信息
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
from urllib.parse import urljoin

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name, format_date

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('intl_tenders')

class InternationalTendersCrawler:
    """国际项目招标信息爬虫"""
    
    # 使用多个国际招标网站作为数据源
    SOURCES = [
        {
            'name': 'Construction Tenders',
            'url': 'https://www.tendersinfo.com/global-construction-tenders.php',
            'tender_selector': 'div.search-results div.tender-box',
            'title_selector': 'div.tender-title a::text',
            'link_selector': 'div.tender-title a::attr(href)',
            'date_selector': 'div.tender-date::text',
            'deadline_selector': 'div.tender-deadline::text',
            'location_selector': 'div.tender-location::text',
            'description_selector': 'div.tender-description p::text',
            'base_url': 'https://www.tendersinfo.com'
        },
        {
            'name': 'International Tenders',
            'url': 'https://www.tendersontime.com/construction-tenders',
            'tender_selector': 'div.tender-item',
            'title_selector': 'h3.tender-title a::text',
            'link_selector': 'h3.tender-title a::attr(href)',
            'date_selector': 'span.published-date::text',
            'deadline_selector': 'span.closing-date::text',
            'location_selector': 'span.location::text',
            'description_selector': 'div.tender-description::text',
            'base_url': 'https://www.tendersontime.com'
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
    
    def search_tenders(self, keyword: str = "construction", limit_per_source: int = 5) -> List[Dict[str, Any]]:
        """
        搜索国际建筑项目招标信息
        
        Args:
            keyword: 搜索关键词
            limit_per_source: 每个来源的最大结果数量
            
        Returns:
            招标信息列表
        """
        logger.info(f"Searching for international tenders with keyword: {keyword}")
        
        all_tenders = []
        
        # 使用无头浏览器
        browser = self._setup_browser()
        
        try:
            for source in self.SOURCES:
                # 应用反爬虫延迟
                domain = source['url'].split('/')[2]
                self.anticrawl.delay_request(domain)
                
                search_url = source['url']
                logger.info(f"Scraping tenders from: {search_url}")
                
                try:
                    # 获取页面内容
                    browser.get(search_url)
                    time.sleep(5)  # 允许JavaScript加载
                    
                    # 获取页面内容
                    page_source = browser.page_source
                    
                    # 保存原始数据
                    self.storage.save_raw_data(f"intl_tenders_{source['name'].lower().replace(' ', '_')}", 
                                             page_source, keyword)
                    
                    # 解析搜索结果
                    selector = Selector(text=page_source)
                    
                    tenders = []
                    for tender_elem in selector.css(source['tender_selector'])[:limit_per_source]:
                        try:
                            # 提取标题和链接
                            title = clean_text(tender_elem.css(source['title_selector']).get())
                            link = tender_elem.css(source['link_selector']).get()
                            
                            # 如果找不到标题或链接，跳过
                            if not title or not link:
                                continue
                            
                            # 处理相对URL
                            if source['base_url'] and not link.startswith(('http://', 'https://')):
                                link = urljoin(source['base_url'], link)
                            
                            # 提取其他信息
                            date = clean_text(tender_elem.css(source['date_selector']).get())
                            deadline = clean_text(tender_elem.css(source['deadline_selector']).get())
                            location = clean_text(tender_elem.css(source['location_selector']).get())
                            description = clean_text(tender_elem.css(source['description_selector']).get())
                            
                            tender = {
                                'title': title,
                                'url': link,
                                'date': format_date(date) if date else "",
                                'deadline': format_date(deadline) if deadline else "",
                                'location': location,
                                'description': description,
                                'source': source['name']
                            }
                            
                            tenders.append(tender)
                            
                        except Exception as e:
                            logger.error(f"Error parsing tender from {source['name']}: {e}")
                    
                    logger.info(f"Found {len(tenders)} tenders from {source['name']}")
                    all_tenders.extend(tenders)
                    
                except Exception as e:
                    logger.error(f"Error scraping tenders from {source['name']}: {e}")
            
            return all_tenders
            
        except Exception as e:
            logger.error(f"Error searching international tenders: {e}")
            return []
        finally:
            browser.quit()
    
    def filter_tenders_by_company(self, tenders: List[Dict[str, Any]], company_name: str) -> List[Dict[str, Any]]:
        """
        根据公司名称过滤招标信息
        
        Args:
            tenders: 招标信息列表
            company_name: 公司名称
            
        Returns:
            过滤后的招标信息列表
        """
        filtered_tenders = []
        
        # 规范化公司名称为小写以进行不区分大小写的比较
        normalized_company = company_name.lower()
        
        for tender in tenders:
            # 检查标题和描述中是否包含公司名称
            if (normalized_company in tender.get('title', '').lower() or 
                normalized_company in tender.get('description', '').lower()):
                filtered_tenders.append(tender)
        
        return filtered_tenders


def crawl_intl_tenders(company_name: Optional[str] = None) -> Dict[str, Any]:
    """
    爬取国际项目招标信息
    
    Args:
        company_name: 公司名称（可选，如果提供则过滤与该公司相关的招标）
        
    Returns:
        爬取结果
    """
    crawler = InternationalTendersCrawler()
    
    # 搜索建筑行业招标信息
    tenders = crawler.search_tenders("construction")
    
    result = {
        "source": "International Tenders",
        "query": "construction",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    # 如果提供了公司名称，过滤与该公司相关的招标
    if company_name:
        result["query"] = company_name
        filtered_tenders = crawler.filter_tenders_by_company(tenders, company_name)
        result["tenders"] = filtered_tenders
        
        # 保存结构化数据
        normalized_name = normalize_company_name(company_name)
        storage_manager = get_storage_manager()
        storage_manager.save_company_data(
            normalized_name, 
            "gov", 
            {"source": "intl_tenders", "tenders": filtered_tenders}
        )
    else:
        result["tenders"] = tenders
        
        # 保存结构化数据（不与特定公司关联）
        storage_manager = get_storage_manager()
        storage_manager.save_raw_data(
            "intl_tenders", 
            {"tenders": tenders}
        )
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "Henderson Land Development"  # 使用一个知名香港建筑公司作为测试
    result = crawl_intl_tenders(test_company)
    print(f"Found {len(result['tenders'])} tenders related to '{test_company}'")
    for tender in result['tenders'][:3]:
        print(f"- {tender['title']} ({tender['location']})")
        print(f"  Date: {tender['date']}, Deadline: {tender['deadline']}")
        print(f"  Description: {tender['description'][:100]}...")

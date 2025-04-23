"""
中国企业信息爬虫 - China Company Information Crawler
爬取中国国家企业信用信息公示系统和其他公开信息来源中的公司信息
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
import re
from urllib.parse import urljoin, urlencode

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('china_company')

class ChinaCompanyCrawler:
    """中国企业信息爬虫"""
    
    # 由于官方网站有较强的反爬机制，使用企查查作为替代数据源
    # 注意：实际使用时需要考虑合规问题
    QICHACHA_URL = "https://www.qcc.com/web/search"
    
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
        # 添加随机User-Agent
        browser = uc.Chrome(options=options)
        return browser
    
    def search_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        搜索中国企业信息
        
        Args:
            company_name: 公司名称
            
        Returns:
            公司基本信息，如果找不到则返回None
        """
        logger.info(f"Searching for China company: {company_name}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("www.qcc.com")
        
        # 构建搜索URL
        search_url = f"{self.QICHACHA_URL}?key={company_name}"
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(search_url)
            
            # 等待页面加载，企查查页面可能加载较慢
            time.sleep(5)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据
            self.storage.save_raw_data("china_company_search", page_source, company_name)
            
            # 解析搜索结果
            selector = Selector(text=page_source)
            
            # 检查是否有搜索结果
            company_cards = selector.css('div.search-result-single')
            if not company_cards:
                logger.info(f"No company information found for {company_name}")
                return None
            
            # 默认使用第一个搜索结果
            first_company = company_cards[0]
            
            # 提取公司基本信息
            company_info = {
                'name': clean_text(first_company.css('div.title a::text').get('')),
                'url': urljoin(self.QICHACHA_URL, first_company.css('div.title a::attr(href)').get('')),
            }
            
            # 提取注册资本、成立时间等信息
            tags = first_company.css('div.tag-list span::text').getall()
            info_text = ' '.join(tags)
            
            # 提取注册资本
            reg_capital_match = re.search(r'注册资本[:：]\s*([\d\.]+)万?元?', info_text)
            if reg_capital_match:
                company_info['registered_capital'] = reg_capital_match.group(1) + '万元'
            
            # 提取成立时间
            establish_time_match = re.search(r'成立时间[:：]\s*(\d{4}-\d{2}-\d{2})', info_text)
            if establish_time_match:
                company_info['established_time'] = establish_time_match.group(1)
            
            # 提取法定代表人
            legal_rep_match = re.search(r'法定代表人[:：]\s*([^\s]+)', info_text)
            if legal_rep_match:
                company_info['legal_representative'] = legal_rep_match.group(1)
            
            # 如果找到了详情页URL，跳转到详情页获取更多信息
            if company_info.get('url'):
                browser.get(company_info['url'])
                time.sleep(5)
                detail_page_source = browser.page_source
                detail_selector = Selector(text=detail_page_source)
                
                # 保存原始数据
                self.storage.save_raw_data("china_company_detail", detail_page_source, company_name)
                
                # 提取更多详细信息
                detail_table = detail_selector.css('section.cominfo-normal')
                if detail_table:
                    # 提取经营范围
                    business_scope = detail_selector.css('div:contains("经营范围") + div::text').get()
                    if business_scope:
                        company_info['business_scope'] = clean_text(business_scope)
                    
                    # 提取注册地址
                    address = detail_selector.css('div:contains("注册地址") + div::text').get()
                    if address:
                        company_info['registered_address'] = clean_text(address)
                    
                    # 提取统一社会信用代码
                    credit_code = detail_selector.css('div:contains("统一社会信用代码") + div::text').get()
                    if credit_code:
                        company_info['credit_code'] = clean_text(credit_code)
            
            logger.info(f"Found company: {company_info['name']}")
            return company_info
            
        except Exception as e:
            logger.error(f"Error searching China company: {e}")
            return None
        finally:
            browser.quit()
    
    def get_company_projects(self, company_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        获取公司的工程项目信息
        
        Args:
            company_name: 公司名称
            limit: 最大结果数量
            
        Returns:
            项目列表
        """
        logger.info(f"Getting projects for company: {company_name}")
        
        # 这里实现工程项目信息的抓取
        # 例如，可以从建筑市场监管平台或行业网站抓取
        # 简化实现，返回一些模拟数据
        projects = [
            {
                'project_name': f"{company_name}示范项目",
                'location': '香港新界',
                'contract_value': '1.2亿港元',
                'start_date': '2022-03-15',
                'status': '在建'
            },
            {
                'project_name': f"{company_name}商业中心",
                'location': '深圳南山区',
                'contract_value': '2.5亿人民币',
                'start_date': '2021-08-10',
                'status': '已完工'
            }
        ]
        
        return projects[:limit]


def crawl_china_company(company_name: str) -> Dict[str, Any]:
    """
    爬取中国企业信息系统中有关公司的信息
    
    Args:
        company_name: 公司名称
        
    Returns:
        爬取结果
    """
    crawler = ChinaCompanyCrawler()
    
    # 搜索公司基本信息
    company_info = crawler.search_company(company_name)
    
    result = {
        "source": "China Company Registry",
        "query": company_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if company_info:
        result["company_info"] = company_info
        
        # 获取公司项目信息
        projects = crawler.get_company_projects(company_name)
        result["projects"] = projects
        
        # 保存结构化数据
        normalized_name = normalize_company_name(company_name)
        storage_manager = get_storage_manager()
        storage_manager.save_company_data(
            normalized_name, 
            "gov", 
            {"source": "china_company", "company_info": company_info, "projects": projects}
        )
    else:
        result["error"] = "Company not found in China company registry"
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "中国建筑股份有限公司"  # 使用一个知名中国建筑公司作为测试
    result = crawl_china_company(test_company)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("Company Info:")
        for key, value in result.get("company_info", {}).items():
            print(f"- {key}: {value}")
        
        print(f"\nFound {len(result.get('projects', []))} projects")
        for project in result.get("projects", []):
            print(f"- {project['project_name']} ({project['location']}): {project['contract_value']}")

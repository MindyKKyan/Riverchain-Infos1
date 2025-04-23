"""
SEC EDGAR爬虫 - SEC EDGAR Database Crawler
爬取美国证券交易委员会EDGAR数据库中的公司信息和报告
"""
import time
import logging
import pandas as pd
from typing import Dict, List, Any, Optional
from requests_html import HTMLSession
import undetected_chromedriver as uc
from parsel import Selector
import re
from urllib.parse import urljoin

import sys
import os
# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from core.anticrawl import get_anticrawl_manager
from core.storage import get_storage_manager
from core.utils import clean_text, normalize_company_name

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('sec_edgar')

class SECEdgarCrawler:
    """SEC EDGAR爬虫"""
    
    BASE_URL = "https://www.sec.gov/edgar/searchedgar/companysearch"
    SEARCH_URL = "https://www.sec.gov/cgi-bin/browse-edgar"
    
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
    
    def search_company(self, company_name: str) -> Optional[Dict[str, Any]]:
        """
        在SEC EDGAR数据库中搜索公司
        
        Args:
            company_name: 公司名称
            
        Returns:
            公司基本信息，如果找不到则返回None
        """
        logger.info(f"Searching for company in SEC EDGAR: {company_name}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("www.sec.gov")
        
        # 构建查询参数
        params = {
            'company': company_name,
            'owner': 'exclude',
            'action': 'getcompany'
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.SEARCH_URL}?{query_string}"
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        headers['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        
        # SEC网站要求添加一个联系方式邮箱到User-Agent
        headers['User-Agent'] = f"{headers['User-Agent']} (riverchain@example.com)"
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据
            self.storage.save_raw_data("sec_edgar_search", page_source, company_name)
            
            # 解析搜索结果
            selector = Selector(text=page_source)
            
            # 检查是否有公司信息
            company_info_table = selector.css('div.companyInfo')
            if not company_info_table:
                logger.info(f"No company information found for {company_name} in SEC EDGAR")
                return None
            
            # 提取公司基本信息
            company_info = {
                'name': clean_text(selector.css('span.companyName::text').get('')),
                'cik': clean_text(selector.css('input[name="CIK"]::attr(value)').get('')),
                'sic': clean_text(selector.css('div.companyInfo p:contains("SIC:")::text').re_first(r'SIC:\s*(\d+)')),
                'sic_description': clean_text(selector.css('div.companyInfo p:contains("SIC:")::text').re_first(r'SIC:.*?-\s*(.+)')),
                'fiscal_year_end': clean_text(selector.css('div.companyInfo p:contains("Fiscal Year End:")::text').re_first(r'Fiscal Year End:\s*(\d+)')),
                'state_of_inc': clean_text(selector.css('div.companyInfo p:contains("State of Inc:")::text').re_first(r'State of Inc:\s*(\w+)')),
                'file_number': clean_text(selector.css('div.companyInfo p:contains("File Number:")::text').re_first(r'File Number:\s*(\d+-\d+)')),
            }
            
            logger.info(f"Found company in SEC EDGAR: {company_info['name']} (CIK: {company_info['cik']})")
            return company_info
            
        except Exception as e:
            logger.error(f"Error scraping SEC EDGAR: {e}")
            return None
        finally:
            browser.quit()
    
    def get_company_filings(self, cik: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        获取公司最近的SEC申报文件
        
        Args:
            cik: 公司CIK编号
            limit: 最大结果数量
            
        Returns:
            申报文件列表
        """
        logger.info(f"Getting SEC filings for CIK: {cik}")
        
        # 应用反爬虫延迟
        self.anticrawl.delay_request("www.sec.gov")
        
        # 构建查询参数
        params = {
            'CIK': cik,
            'owner': 'exclude',
            'action': 'getcompany',
            'count': '100'  # 请求足够多的结果
        }
        
        query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
        url = f"{self.SEARCH_URL}?{query_string}"
        
        # 获取随机请求头
        headers = self.anticrawl.get_request_headers()
        headers['User-Agent'] = f"{headers['User-Agent']} (riverchain@example.com)"
        
        # 使用无头浏览器获取动态内容
        browser = self._setup_browser()
        try:
            browser.get(url)
            
            # 等待页面加载
            time.sleep(3)
            
            # 获取页面内容
            page_source = browser.page_source
            
            # 保存原始数据
            self.storage.save_raw_data("sec_edgar_filings", page_source, cik)
            
            # 解析申报文件列表
            selector = Selector(text=page_source)
            
            filings = []
            # 申报文件列表表格
            table = selector.css('table.tableFile2')
            if not table:
                logger.info(f"No filings found for CIK: {cik}")
                return []
            
            # 提取表格行
            rows = table.css('tr')
            # 跳过表头行
            for row in rows[1:limit+1]:
                try:
                    cells = row.css('td')
                    if len(cells) < 5:
                        continue
                    
                    # 提取文件信息
                    filing_type = clean_text(cells[0].css('::text').get())
                    filing_date = clean_text(cells[3].css('::text').get())
                    filing_desc = clean_text(cells[2].css('::text').get())
                    
                    # 提取文件链接
                    filing_link = cells[1].css('a::attr(href)').get()
                    if filing_link:
                        filing_link = urljoin(self.BASE_URL, filing_link)
                    
                    filing = {
                        'type': filing_type,
                        'date': filing_date,
                        'description': filing_desc,
                        'url': filing_link
                    }
                    
                    filings.append(filing)
                    
                except Exception as e:
                    logger.error(f"Error parsing filing row: {e}")
            
            logger.info(f"Found {len(filings)} filings for CIK: {cik}")
            return filings
            
        except Exception as e:
            logger.error(f"Error getting SEC filings: {e}")
            return []
        finally:
            browser.quit()


def crawl_sec_edgar(company_name: str) -> Dict[str, Any]:
    """
    爬取SEC EDGAR数据库中有关公司的信息
    
    Args:
        company_name: 公司名称
        
    Returns:
        爬取结果
    """
    crawler = SECEdgarCrawler()
    
    # 先搜索公司基本信息
    company_info = crawler.search_company(company_name)
    
    result = {
        "source": "SEC EDGAR",
        "query": company_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    
    if company_info:
        result["company_info"] = company_info
        
        # 如果找到公司，获取最近的申报文件
        if 'cik' in company_info and company_info['cik']:
            filings = crawler.get_company_filings(company_info['cik'])
            result["filings"] = filings
        
        # 保存结构化数据
        normalized_name = normalize_company_name(company_name)
        storage_manager = get_storage_manager()
        storage_manager.save_company_data(
            normalized_name, 
            "gov", 
            {"source": "sec_edgar", "company_info": company_info, "filings": result.get("filings", [])}
        )
    else:
        result["error"] = "Company not found in SEC EDGAR database"
    
    return result


if __name__ == "__main__":
    # 测试代码
    test_company = "China Construction Bank"  # 使用一个可能在SEC注册的中国/香港公司
    result = crawl_sec_edgar(test_company)
    if "error" in result:
        print(f"Error: {result['error']}")
    else:
        print("Company Info:")
        for key, value in result.get("company_info", {}).items():
            print(f"- {key}: {value}")
        
        print(f"\nFound {len(result.get('filings', []))} filings")
        for filing in result.get("filings", [])[:3]:
            print(f"- {filing['type']} ({filing['date']}): {filing['description']}")
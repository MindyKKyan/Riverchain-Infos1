"""
反爬虫对抗模块 - Anti-crawling detection measures
"""
import random
import time
from typing import Dict, List, Optional
from fake_useragent import UserAgent
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('anticrawl')

class AntiCrawlManager:
    """反爬虫管理器，提供随机User-Agent、控制请求间隔、IP代理池等功能"""
    
    def __init__(self, 
                 min_delay: float = 1.0, 
                 max_delay: float = 3.0,
                 proxy_list: Optional[List[str]] = None):
        """
        初始化反爬虫管理器
        
        Args:
            min_delay: 最小请求间隔时间(秒)
            max_delay: 最大请求间隔时间(秒)
            proxy_list: 代理IP列表，格式如 ["http://ip:port", ...]
        """
        self.min_delay = min_delay
        self.max_delay = max_delay
        self.ua = UserAgent()
        self.proxy_list = proxy_list or []
        self.domain_last_access: Dict[str, float] = {}
        logger.info(f"AntiCrawl manager initialized with delay {min_delay}-{max_delay}s")
    
    def get_random_user_agent(self) -> str:
        """获取随机User-Agent"""
        return self.ua.random
    
    def get_random_proxy(self) -> Optional[str]:
        """获取随机代理"""
        if not self.proxy_list:
            return None
        return random.choice(self.proxy_list)
    
    def delay_request(self, domain: str) -> None:
        """
        根据域名控制请求间隔，避免频繁请求同一域名
        
        Args:
            domain: 目标网站域名
        """
        current_time = time.time()
        if domain in self.domain_last_access:
            elapsed = current_time - self.domain_last_access[domain]
            required_delay = random.uniform(self.min_delay, self.max_delay)
            
            if elapsed < required_delay:
                sleep_time = required_delay - elapsed
                logger.debug(f"Delaying request to {domain} for {sleep_time:.2f}s")
                time.sleep(sleep_time)
        
        # 更新最后访问时间
        self.domain_last_access[domain] = time.time()
    
    def get_request_headers(self) -> Dict[str, str]:
        """获取包含随机User-Agent的请求头"""
        return {
            'User-Agent': self.get_random_user_agent(),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
    
    def check_robots_txt(self, domain: str, path: str) -> bool:
        """
        检查robots.txt规则，确定是否可以抓取
        
        Args:
            domain: 目标网站域名
            path: 请求路径
            
        Returns:
            是否允许抓取
        """
        # 这里应实现robots.txt解析逻辑
        # 简化实现，实际项目中应更完善
        logger.info(f"Checking robots.txt for {domain}{path}")
        return True  # 默认允许


# 创建默认实例供模块内使用
default_manager = AntiCrawlManager()

def get_anticrawl_manager() -> AntiCrawlManager:
    """获取默认的反爬虫管理器实例"""
    return default_manager 
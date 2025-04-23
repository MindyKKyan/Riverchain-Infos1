#!/usr/bin/env python3
"""
测试脚本：Bing News爬虫性能测试
"""
import os
import sys
import time
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bing_news_test.log')
    ]
)
logger = logging.getLogger('test_bing_news')

# 导入爬虫
from crawlers.news.bing_news import crawl_bing_news

def test_bing_news_crawler():
    """测试Bing News爬虫性能"""
    
    # 创建测试公司列表
    test_companies = [
        "RiverChain",
        "Henderson Land Development",
        "Sun Hung Kai Properties",
        "Swire Properties",
        "New World Development",
        "China State Construction"
    ]
    
    results = {}
    
    print("\n===== Bing News爬虫测试 =====")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"测试公司数量: {len(test_companies)}")
    print("=" * 50)
    
    for i, company in enumerate(test_companies):
        print(f"\n[{i+1}/{len(test_companies)}] 测试公司: {company}")
        
        # 记录开始时间
        start_time = time.time()
        
        # 爬取新闻
        result = crawl_bing_news(company)
        
        # 计算耗时
        duration = time.time() - start_time
        
        # 记录结果
        results[company] = {
            'article_count': len(result['articles']),
            'duration': duration
        }
        
        # 打印结果概要
        print(f"找到 {len(result['articles'])} 篇新闻")
        print(f"耗时: {duration:.2f} 秒")
        
        # 打印详细信息
        if result['articles']:
            print("\n前三篇新闻:")
            for idx, article in enumerate(result['articles'][:3]):
                print(f"  {idx+1}. {article['title']}")
                print(f"     来源: {article['source']}")
                print(f"     日期: {article['date']}")
                print(f"     链接: {article['url'][:60]}...")
                if article.get('summary'):
                    print(f"     摘要: {article['summary'][:100]}...")
                print("")
        else:
            print("没有找到相关新闻")
        
        # 每次测试间隔以避免被封
        if i < len(test_companies) - 1:
            wait_time = 10
            print(f"\n等待 {wait_time} 秒后继续下一个测试...")
            time.sleep(wait_time)
    
    # 打印测试结果摘要
    print("\n===== 测试结果摘要 =====")
    total_articles = sum(res['article_count'] for res in results.values())
    avg_duration = sum(res['duration'] for res in results.values()) / len(results)
    
    print(f"总共找到 {total_articles} 篇新闻")
    print(f"平均每个公司找到 {total_articles/len(results):.2f} 篇新闻")
    print(f"平均爬取时间: {avg_duration:.2f} 秒")
    print("\n详细结果:")
    for company, res in results.items():
        print(f"  {company}: {res['article_count']} 篇新闻, 耗时 {res['duration']:.2f} 秒")
    
    return results

if __name__ == "__main__":
    test_bing_news_crawler() 
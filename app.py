"""
RiverInfos - Construction Industry Company Information Crawler System
Streamlit main interface
"""
import os
import logging
import time
import pandas as pd
import streamlit as st
from io import BytesIO
from typing import Dict, List, Any, Optional, Tuple
import importlib
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('app')

# Import core modules
from core.storage import get_storage_manager
from core.utils import normalize_company_name
from adapters.file_upload.file_handler import process_temp_file

# Set page
st.set_page_config(
    page_title="RiverInfos - Construction Industry Company Information Crawler",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize storage manager
storage_manager = get_storage_manager()

# Define available crawlers
AVAILABLE_CRAWLERS = {
    # News crawlers
    'google_news': {
        'module': 'crawlers.news.google_news',
        'function': 'crawl_google_news',
        'name': 'Google News',
        'description': 'Crawl Google News search results',
        'category': 'news',
        'enabled': True
    },
    'bing_news': {
        'module': 'crawlers.news.bing_news',
        'function': 'crawl_bing_news',
        'name': 'Bing News',
        'description': 'Crawl Bing News search results',
        'category': 'news',
        'enabled': True
    },
    'hk_news': {
        'module': 'crawlers.news.hk_news',
        'function': 'crawl_hk_news',
        'name': 'Hong Kong Local News',
        'description': 'Crawl Hong Kong local news websites',
        'category': 'news',
        'enabled': True
    },
    'construction_news': {
        'module': 'crawlers.news.construction_news',
        'function': 'crawl_construction_news',
        'name': 'Construction Industry News',
        'description': 'Crawl construction industry news websites',
        'category': 'news',
        'enabled': True
    },
    
    # Social media crawlers
    'twitter_public': {
        'module': 'crawlers.social.twitter_public',
        'function': 'crawl_twitter_public',
        'name': 'Twitter Public Information',
        'description': 'Crawl public information on Twitter',
        'category': 'social',
        'enabled': True
    },
    'linkedin_public': {
        'module': 'crawlers.social.linkedin_public',
        'function': 'crawl_linkedin_public',
        'name': 'LinkedIn Public Information',
        'description': 'Crawl public company information on LinkedIn',
        'category': 'social',
        'enabled': True
    },
    
    # Government data crawlers
    'hk_companies_registry': {
        'module': 'crawlers.government.hk_companies_registry',
        'function': 'crawl_hk_companies_registry',
        'name': 'Hong Kong Companies Registry',
        'description': 'Crawl company information from Hong Kong Companies Registry',
        'category': 'government',
        'enabled': True
    },
    'hk_judiciary': {
        'module': 'crawlers.government.hk_judiciary',
        'function': 'crawl_hk_judiciary',
        'name': 'Hong Kong Judiciary Records',
        'description': 'Crawl public records from Hong Kong judiciary system',
        'category': 'government',
        'enabled': True
    },
    
    # Industry information crawlers
    'construction_qualifications': {
        'module': 'crawlers.industry.construction_qualifications',
        'function': 'crawl_construction_qualifications',
        'name': 'Construction Qualifications',
        'description': 'Crawl construction industry qualification information',
        'category': 'industry',
        'enabled': True
    },
    'environmental_compliance': {
        'module': 'crawlers.industry.environmental_compliance',
        'function': 'crawl_environmental_compliance',
        'name': 'Environmental Compliance Records',
        'description': 'Crawl environmental compliance record information',
        'category': 'industry',
        'enabled': True
    },
}

def import_crawler(crawler_id: str) -> Tuple[Any, str, str]:
    """
    Dynamically import crawler module
    
    Args:
        crawler_id: Crawler ID
        
    Returns:
        (Crawler function, module name, function name)
    """
    if crawler_id not in AVAILABLE_CRAWLERS:
        raise ValueError(f"Unknown crawler: {crawler_id}")
    
    crawler_info = AVAILABLE_CRAWLERS[crawler_id]
    module_name = crawler_info['module']
    function_name = crawler_info['function']
    
    try:
        module = importlib.import_module(module_name)
        crawler_function = getattr(module, function_name)
        return crawler_function, module_name, function_name
    except (ImportError, AttributeError) as e:
        logger.error(f"Failed to import crawler {crawler_id}: {e}")
        # If the actual module doesn't exist, return a placeholder function
        def placeholder_crawler(company_name: str, **kwargs):
            return {
                "error": f"Crawler {crawler_id} not implemented yet",
                "company_name": company_name
            }
        return placeholder_crawler, module_name, function_name

def run_crawler(crawler_id: str, company_name: str) -> Dict[str, Any]:
    """
    Run the specified crawler
    
    Args:
        crawler_id: Crawler ID
        company_name: Company name
        
    Returns:
        Crawl results
    """
    try:
        crawler_function, module_name, function_name = import_crawler(crawler_id)
        
        # Record start time
        start_time = time.time()
        
        # Run crawler
        result = crawler_function(company_name)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Add metadata
        if isinstance(result, dict):
            result['_metadata'] = {
                'crawler_id': crawler_id,
                'module': module_name,
                'function': function_name,
                'duration': duration,
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
        
        return result
    
    except Exception as e:
        logger.error(f"Error running crawler {crawler_id}: {e}")
        logger.error(traceback.format_exc())
        return {
            "error": str(e),
            "crawler_id": crawler_id,
            "company_name": company_name
        }

def get_crawlers_by_category() -> Dict[str, List[Dict]]:
    """
    Get crawlers by category
    
    Returns:
        Crawlers grouped by category
    """
    categories = {}
    
    for crawler_id, crawler_info in AVAILABLE_CRAWLERS.items():
        category = crawler_info.get('category', 'other')
        
        if category not in categories:
            categories[category] = []
        
        categories[category].append({
            'id': crawler_id,
            'name': crawler_info.get('name', crawler_id),
            'description': crawler_info.get('description', ''),
            'enabled': crawler_info.get('enabled', True)
        })
    
    return categories

def display_news_results(results: Dict[str, Any]):
    """Display news crawl results"""
    if 'articles' not in results or not results['articles']:
        st.info("No relevant news found")
        return
    
    articles = results['articles']
    st.subheader(f"Found {len(articles)} news articles")
    
    for i, article in enumerate(articles):
        st.markdown(f"**{article.get('title', 'No Title')}**")
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown(f"**Source**: {article.get('source', 'Unknown')}")
            st.markdown(f"**Date**: {article.get('date', 'Unknown')}")
            st.markdown(f"**Summary**: {article.get('summary', 'No Summary')}")
            if 'url' in article:
                st.markdown(f"[Read Original]({article['url']})")
        with col2:
            if 'image_url' in article and article['image_url']:
                st.image(article['image_url'], use_column_width=True)
        st.markdown("---")

def display_social_results(results: Dict[str, Any]):
    """Display social media crawl results"""
    if 'posts' not in results or not results['posts']:
        st.info("No relevant social media information found")
        return
    
    posts = results['posts']
    st.subheader(f"Found {len(posts)} social media posts")
    
    for i, post in enumerate(posts):
        st.markdown(f"**{post.get('author', 'Unknown User')} - {post.get('date', 'Unknown Date')}**")
        st.markdown(post.get('text', 'No Content'))
        if 'media_url' in post and post['media_url']:
            st.image(post['media_url'], width=300)
        if 'url' in post:
            st.markdown(f"[View Original]({post['url']})")
        st.markdown(f"**Platform**: {post.get('platform', 'Unknown')}")
        st.markdown(f"**Engagement**: Likes {post.get('likes', 0)}, Comments {post.get('comments', 0)}, Shares {post.get('shares', 0)}")
        st.markdown("---")

def display_government_results(results: Dict[str, Any]):
    """Display government data crawl results"""
    if 'companies' not in results or not results['companies']:
        st.info("No relevant government records found")
        return
    
    companies = results['companies']
    st.subheader(f"Found {len(companies)} government records")
    
    for i, company in enumerate(companies):
        st.markdown(f"**{company.get('company_name', 'Unknown Company')}**")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**Registration Number**: {company.get('company_number', 'Unknown')}")
            st.markdown(f"**Company Status**: {company.get('company_status', 'Unknown')}")
            st.markdown(f"**Incorporation Date**: {company.get('incorporation_date', 'Unknown')}")
        with col2:
            st.markdown(f"**Registered Address**: {company.get('address', 'Unknown')}")
            if 'detail_url' in company:
                st.markdown(f"[View Details]({company['detail_url']})")
        st.markdown("---")
    
    # If there is company details, display them
    if 'details' in results:
        st.subheader("Company Details")
        details = results['details']
        
        st.markdown(f"**Company Status**: {details.get('status', 'Unknown')}")
        st.markdown(f"**Registered Address**: {details.get('registered_address', 'Unknown')}")
        st.markdown(f"**Business Nature**: {details.get('business_nature', 'Unknown')}")
        
        # Display director information
        if 'directors' in details and details['directors']:
            st.markdown("**Directors Information**:")
            directors_df = pd.DataFrame(details['directors'])
            st.dataframe(directors_df)

def display_industry_results(results: Dict[str, Any]):
    """Display industry information crawl results"""
    if 'qualifications' in results:
        st.subheader("Construction Qualifications")
        qual_df = pd.DataFrame(results['qualifications'])
        st.dataframe(qual_df)
    
    if 'projects' in results:
        st.subheader(f"Found {len(results['projects'])} project records")
        
        for i, project in enumerate(results['projects']):
            st.markdown(f"**{project.get('project_name', 'Unknown Project')}**")
            st.markdown(f"**Project Type**: {project.get('project_type', 'Unknown')}")
            st.markdown(f"**Project Status**: {project.get('status', 'Unknown')}")
            st.markdown(f"**Start Date**: {project.get('start_date', 'Unknown')}")
            st.markdown(f"**Completion Date**: {project.get('completion_date', 'Unknown')}")
            st.markdown(f"**Project Amount**: {project.get('amount', 'Unknown')}")
            st.markdown(f"**Project Description**: {project.get('description', 'No Description')}")
            st.markdown("---")

def display_file_upload_results(results: Dict[str, Any]):
    """Display file upload processing results"""
    if not results.get('success', False):
        st.error(f"File processing failed: {results.get('error', 'Unknown error')}")
        return
    
    file_type = results.get('file_type', 'unknown')
    result_data = results.get('result', {})
    
    st.subheader(f"File Processing Results - {results.get('filename', 'Unknown File')}")
    
    if file_type == 'pdf':
        # Display PDF processing results
        if 'company_names' in result_data:
            st.markdown("**Detected Company Names:**")
            for name in result_data['company_names']:
                st.markdown(f"- {name}")
        
        if 'contacts' in result_data:
            st.markdown("**Contact Information:**")
            for contact in result_data['contacts']:
                st.markdown(f"- {contact}")
        
        if 'addresses' in result_data:
            st.markdown("**Address Information:**")
            for address in result_data['addresses']:
                st.markdown(f"- {address}")
        
        if 'projects' in result_data:
            st.markdown("**Project Information:**")
            for project in result_data['projects']:
                st.markdown(f"- {project}")
        
        if 'amounts' in result_data:
            st.markdown("**Amount Information:**")
            for amount in result_data['amounts']:
                st.markdown(f"- {amount}")
        
        if 'tables' in result_data:
            st.markdown(f"**Detected {len(result_data['tables'])} tables**")
    
    elif file_type == 'excel':
        # Display Excel processing results
        company_info = result_data.get('company_info', {})
        
        if company_info.get('company_names'):
            st.markdown("**Detected Company Names:**")
            for name in company_info['company_names']:
                st.markdown(f"- {name}")
        
        if company_info.get('project_names'):
            st.markdown("**Project Information:**")
            for project in company_info['project_names']:
                st.markdown(f"- {project}")
        
        if company_info.get('financial_data'):
            st.markdown("**Financial Data:**")
            for data in company_info['financial_data']:
                st.markdown(f"- Column: {data['column']}, Sum: {data['sum']}, Mean: {data['mean']}")
        
        # Display table structure information
        if 'multi_sheet' in result_data:
            if result_data['multi_sheet']:
                st.markdown(f"**Excel file contains {result_data.get('sheets_count', 0)} worksheets**")
            else:
                df_info = result_data.get('df_info', {})
                st.markdown(f"**Table dimensions: {df_info.get('shape', (0, 0))}**")
                st.markdown(f"**Number of columns: {len(df_info.get('columns', []))}**")

def run_all_crawlers(company_name: str, selected_crawlers: List[str]) -> Dict[str, Any]:
    """
    Run all selected crawlers
    
    Args:
        company_name: Company name
        selected_crawlers: List of selected crawler IDs
        
    Returns:
        Results from all crawlers
    """
    results = {}
    
    # Normalize company name for storage
    normalized_name = normalize_company_name(company_name)
    
    with st.spinner("Crawling information..."):
        progress_bar = st.progress(0)
        total_crawlers = len(selected_crawlers)
        
        for i, crawler_id in enumerate(selected_crawlers):
            # Update progress bar
            progress = (i / total_crawlers)
            progress_bar.progress(progress)
            
            # Display current crawler
            st.text(f"Currently crawling: {AVAILABLE_CRAWLERS[crawler_id]['name']}")
            
            # Run crawler
            result = run_crawler(crawler_id, company_name)
            results[crawler_id] = result
            
            # Pause briefly to avoid requests overwhelming
            time.sleep(0.5)
        
        # Complete progress bar
        progress_bar.progress(1.0)
    
    return results

def main():
    """Main function"""
    st.title("RiverInfos - Construction Industry Company Information Crawler")
    st.markdown("Construction company information crawler system developed for RiverChain, focusing on Hong Kong and international companies")
    
    # Sidebar
    st.sidebar.header("Settings")
    
    # Company name input
    company_name = st.sidebar.text_input("Enter Company Name", value="RiverChain")
    
    # Crawler category selection
    st.sidebar.subheader("Select Crawlers to Use")
    crawlers_by_category = get_crawlers_by_category()
    
    selected_crawlers = []
    for category, crawlers in crawlers_by_category.items():
        st.sidebar.markdown(f"**{category.capitalize()}**")
        for crawler in crawlers:
            if crawler['enabled']:
                if st.sidebar.checkbox(f"{crawler['name']} - {crawler['description']}", value=True):
                    selected_crawlers.append(crawler['id'])
    
    # File upload
    st.sidebar.subheader("Upload File")
    uploaded_file = st.sidebar.file_uploader("Select a PDF or Excel file", type=['pdf', 'xlsx', 'xls', 'csv'])
    
    # Crawl button
    if st.sidebar.button("Start Crawling"):
        if not company_name:
            st.error("Please enter a company name")
        else:
            # Run all selected crawlers
            results = run_all_crawlers(company_name, selected_crawlers)
            
            # Display results
            st.header(f"Crawl Results for {company_name}")
            
            # Display results by category
            for category in crawlers_by_category.keys():
                st.subheader(f"{category.capitalize()} Data")
                
                # Get results for this category
                category_results = {}
                for crawler_id, crawler_info in AVAILABLE_CRAWLERS.items():
                    if crawler_info.get('category') == category and crawler_id in results:
                        category_results[crawler_id] = results[crawler_id]
                
                # If no results, show message
                if not category_results:
                    st.info(f"No {category} crawlers selected")
                    continue
                
                # Display results by category, using tabs instead of nested expanders
                crawler_tabs = st.tabs([AVAILABLE_CRAWLERS[crawler_id]['name'] for crawler_id in category_results.keys()])
                for i, (crawler_id, result) in enumerate(category_results.items()):
                    with crawler_tabs[i]:
                        if 'error' in result:
                            st.error(f"Crawl failed: {result['error']}")
                        else:
                            if category == 'news':
                                display_news_results(result)
                            elif category == 'social':
                                display_social_results(result)
                            elif category == 'government':
                                display_government_results(result)
                            elif category == 'industry':
                                display_industry_results(result)
                            else:
                                # Generic result display
                                st.json(result)
    
    # Process file upload
    if uploaded_file is not None:
        with st.spinner("Processing uploaded file..."):
            # Get file content
            file_content = uploaded_file.read()
            
            # Process file
            results = process_temp_file(file_content, uploaded_file.name, company_name)
            
            # Display results
            st.header(f"Processing Results for File {uploaded_file.name}")
            display_file_upload_results(results)

if __name__ == "__main__":
    main() 
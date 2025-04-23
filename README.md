
# RiverInfos - 建筑公司信息爬虫系统 | Construction Company Information Crawler

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.0+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**[中文](#中文详细说明) | [English](#detailed-english-description)**

## 中文详细说明

RiverInfos是一个专为建筑行业定制的综合信息采集与分析系统，能够自动从多种渠道爬取、处理和展示香港及国际建筑公司的相关信息。本系统旨在帮助建筑行业从业者快速获取竞争对手和潜在合作伙伴的全面信息，辅助商业决策。

### 📑 核心功能

#### 多源数据采集
- **新闻媒体爬虫**
  - Google新闻：从Google新闻搜索并提取公司相关新闻
  - Bing新闻：利用Bing新闻API获取更全面的媒体报道
  - 香港本地新闻：专注于香港本地媒体（如南华早报、香港经济日报等）
  - 建筑行业新闻：针对建筑行业专业媒体的定向爬虫

- **社交媒体监测**
  - Twitter公开信息：采集Twitter上公司及行业相关公开讨论
  - LinkedIn公开信息：提取LinkedIn上的公司公开信息和动态
  - Facebook公开页面：抓取Facebook公开页面的内容和互动数据

- **政府与监管数据**
  - 香港公司注册处：公司基本信息查询
  - 香港司法记录：诉讼案件、法院判决等
  - SEC EDGAR数据库：美国上市公司报告查询
  - 中国企业信息：中国大陆企业信息查询
  - 国际招标信息：国际工程招标信息采集

- **行业专业信息**
  - 建筑资质认证：各类建筑和工程资质信息
  - 环保合规记录：环境评估和合规情况
  - 项目历史记录：历史项目数据与案例分析

#### 文件处理能力
- **文档解析与分析**
  - PDF文件处理：自动提取PDF中的公司、项目和财务信息
  - Excel数据分析：处理各类表格数据，提取关键业务指标
  - 结构化数据存储：将非结构化文档转换为可查询的结构化数据

#### 智能分析功能
- 情感分析：评估公司在媒体和社交平台的声誉情况
- 文本摘要：自动生成信息摘要，突出关键内容
- 数据可视化：直观展示公司指标、项目分布、媒体曝光等

### 🚀 安装指南

#### 系统要求
- Python 3.8或更高版本
- Chrome浏览器 (用于Selenium和无头浏览器爬虫)
- 稳定的网络连接

#### 安装步骤

1. **克隆仓库**:
   ```bash
   git clone https://github.com/MindyKKyan/RiverchainCrawler.git
   cd RiverchainCrawler/riverInfos
   ```

2. **创建并激活虚拟环境** (推荐):
   ```bash
   # 使用venv
   python -m venv venv
   
   # Windows激活
   venv\Scripts\activate
   
   # macOS/Linux激活
   source venv/bin/activate
   ```

3. **安装依赖**:
   ```bash
   pip install -r requirements.txt
   ```

4. **运行应用**:
   ```bash
   python run.py
   ```
   或直接使用Streamlit:
   ```bash
   streamlit run app.py
   ```

5. **在浏览器中访问应用**:
   打开浏览器，访问 `http://localhost:8501`

### 💻 使用指南

#### 基本流程
1. 在侧边栏输入要研究的目标公司名称
2. 选择需要使用的爬虫类型(新闻、社交媒体、政府数据等)
3. 点击"开始爬取"按钮启动信息采集
4. 系统会自动处理并展示结果，包括:
   - 媒体报道摘要
   - 社交媒体动态
   - 公司注册信息
   - 司法记录
   - 行业资质与项目历史

#### 文件上传分析
1. 切换到"文件上传"选项卡
2. 上传与目标公司相关的文档(PDF、Excel、Word等)
3. 选择文件处理类型
4. 系统将自动提取并分析文档中的关键信息

### 📂 项目结构

```
riverInfos/
├── crawlers/               # 爬虫模块集合
│   ├── news/               # 新闻媒体爬虫
│   │   ├── google_news.py  # Google新闻爬虫
│   │   ├── bing_news.py    # Bing新闻爬虫
│   │   ├── hk_news.py      # 香港本地新闻爬虫
│   │   └── construction_news.py  # 建筑行业新闻爬虫
│   ├── social/             # 社交媒体爬虫
│   │   ├── twitter_public.py     # Twitter公开信息爬虫
│   │   ├── linkedin_public.py    # LinkedIn公开信息爬虫
│   │   └── facebook_public.py    # Facebook公开页面爬虫
│   ├── government/         # 政府数据爬虫
│   │   ├── sec_edgar.py          # SEC EDGAR数据库爬虫
│   │   ├── china_company.py      # 中国企业信息爬虫
│   │   ├── hk_companies_registry.py  # 香港公司注册处爬虫
│   │   ├── hk_judiciary.py       # 香港司法记录爬虫
│   │   └── intl_tenders.py       # 国际招标信息爬虫
│   └── industry/           # 行业信息爬虫
│       ├── construction_qualifications.py  # 建筑资质爬虫
│       ├── environmental_compliance.py     # 环保合规记录爬虫
│       └── project_history.py             # 项目历史爬虫
├── core/                   # 核心功能模块
│   ├── anticrawl.py        # 反爬虫对抗技术
│   ├── storage.py          # 数据存储管理
│   └── utils.py            # 通用工具函数
├── adapters/               # 适配器和处理器
│   ├── file_upload/        # 文件上传处理模块
│   │   ├── pdf_processor.py     # PDF文件处理器
│   │   ├── excel_processor.py   # Excel文件处理器
│   │   └── file_handler.py      # 文件上传处理器
│   └── ai_hooks/           # AI集成接口
│       ├── sentiment_analysis.py  # 情感分析钩子
│       └── nlp_processor.py       # NLP处理接口
├── tests/                  # 测试模块
│   ├── test_crawlers.py         # 爬虫测试
│   ├── test_file_processors.py  # 文件处理器测试
│   └── test_anticrawl.py        # 反爬技术测试
├── app.py                  # Streamlit主应用
├── run.py                  # 启动脚本
└── requirements.txt        # 项目依赖
```

### ⚠️ 注意事项

- 本系统设计用于合法收集公开信息，请遵守相关法律法规和网站使用条款
- 建议限制爬取频率，避免对目标网站造成过大负担
- 数据准确性依赖于源网站，结果仅供参考，重要决策请核实信息
- 定期更新爬虫选择器，以适应目标网站的变化

### 📄 许可证

本项目采用[MIT许可证](LICENSE)。

### 👥 贡献指南

欢迎贡献代码或提出建议！请遵循以下步骤：

1. Fork本仓库
2. 创建功能分支 (`git checkout -b feature/amazing-feature`)
3. 提交更改 (`git commit -m 'Add amazing feature'`)
4. 推送到分支 (`git push origin feature/amazing-feature`)
5. 创建Pull Request

---

## Detailed English Description

RiverInfos is a comprehensive information collection and analysis system tailored for the construction industry, capable of automatically crawling, processing, and displaying relevant information about Hong Kong and international construction companies from multiple sources. This system aims to help construction industry professionals quickly obtain comprehensive information about competitors and potential partners to assist in business decision-making.

### 📑 Core Features

#### Multi-source Data Collection
- **News Media Crawlers**
  - Google News: Searches and extracts company-related news from Google News
  - Bing News: Utilizes Bing News API for more comprehensive media coverage
  - Hong Kong Local News: Focuses on Hong Kong local media (e.g., SCMP, HKET)
  - Construction Industry News: Targeted crawler for construction industry professional media

- **Social Media Monitoring**
  - Twitter Public Information: Collects public discussions about companies and industry on Twitter
  - LinkedIn Public Information: Extracts public company information and activities from LinkedIn
  - Facebook Public Pages: Captures content and interaction data from public Facebook pages

- **Government and Regulatory Data**
  - Hong Kong Companies Registry: Basic company information queries
  - Hong Kong Judiciary Records: Litigation cases, court judgments, etc.
  - SEC EDGAR Database: US listed company reports queries
  - Chinese Enterprise Information: Mainland China enterprise information queries
  - International Tender Information: International engineering tender information collection

- **Industry-specific Information**
  - Construction Qualifications: Various construction and engineering qualification information
  - Environmental Compliance Records: Environmental assessment and compliance status
  - Project History Records: Historical project data and case analysis

#### Document Processing Capabilities
- **Document Parsing and Analysis**
  - PDF Processing: Automatically extracts company, project, and financial information from PDFs
  - Excel Data Analysis: Processes various tabular data to extract key business metrics
  - Structured Data Storage: Converts unstructured documents into queryable structured data

#### Intelligent Analysis Features
- Sentiment Analysis: Evaluates company reputation in media and social platforms
- Text Summarization: Automatically generates information summaries highlighting key content
- Data Visualization: Intuitively displays company metrics, project distribution, media exposure, etc.

### 🚀 Installation Guide

#### System Requirements
- Python 3.8 or higher
- Chrome browser (for Selenium and headless browser crawling)
- Stable internet connection

#### Installation Steps

1. **Clone the repository**:
   ```bash
   git clone https://github.com/MindyKKyan/RiverchainCrawler.git
   cd RiverchainCrawler/riverInfos
   ```

2. **Create and activate a virtual environment** (recommended):
   ```bash
   # Using venv
   python -m venv venv
   
   # Activate on Windows
   venv\Scripts\activate
   
   # Activate on macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**:
   ```bash
   python run.py
   ```
   Or directly using Streamlit:
   ```bash
   streamlit run app.py
   ```

5. **Access the application in your browser**:
   Open your browser and visit `http://localhost:8501`

### 💻 Usage Guide

#### Basic Workflow
1. Enter the target company name to research in the sidebar
2. Select the crawler types to use (news, social media, government data, etc.)
3. Click the "Start Crawling" button to initiate information collection
4. The system will automatically process and display results, including:
   - Media coverage summaries
   - Social media activities
   - Company registration information
   - Judicial records
   - Industry qualifications and project history

#### File Upload Analysis
1. Switch to the "File Upload" tab
2. Upload documents related to the target company (PDF, Excel, Word, etc.)
3. Select the file processing type
4. The system will automatically extract and analyze key information from the documents

### 📂 Project Structure

```
riverInfos/
├── crawlers/               # Crawler module collection
│   ├── news/               # News media crawlers
│   │   ├── google_news.py  # Google News crawler
│   │   ├── bing_news.py    # Bing News crawler
│   │   ├── hk_news.py      # Hong Kong local news crawler
│   │   └── construction_news.py  # Construction industry news crawler
│   ├── social/             # Social media crawlers
│   │   ├── twitter_public.py     # Twitter public information crawler
│   │   ├── linkedin_public.py    # LinkedIn public information crawler
│   │   └── facebook_public.py    # Facebook public page crawler
│   ├── government/         # Government data crawlers
│   │   ├── sec_edgar.py          # SEC EDGAR database crawler
│   │   ├── china_company.py      # Chinese enterprise information crawler
│   │   ├── hk_companies_registry.py  # Hong Kong Companies Registry crawler
│   │   ├── hk_judiciary.py       # Hong Kong judicial records crawler
│   │   └── intl_tenders.py       # International tender information crawler
│   └── industry/           # Industry information crawlers
│       ├── construction_qualifications.py  # Construction qualifications crawler
│       ├── environmental_compliance.py     # Environmental compliance records crawler
│       └── project_history.py             # Project history crawler
├── core/                   # Core functionality modules
│   ├── anticrawl.py        # Anti-crawling technologies
│   ├── storage.py          # Data storage management
│   └── utils.py            # Common utility functions
├── adapters/               # Adapters and processors
│   ├── file_upload/        # File upload processing modules
│   │   ├── pdf_processor.py     # PDF file processor
│   │   ├── excel_processor.py   # Excel file processor
│   │   └── file_handler.py      # File upload handler
│   └── ai_hooks/           # AI integration interfaces
│       ├── sentiment_analysis.py  # Sentiment analysis hooks
│       └── nlp_processor.py       # NLP processing interface
├── tests/                  # Test modules
│   ├── test_crawlers.py         # Crawler tests
│   ├── test_file_processors.py  # File processor tests
│   └── test_anticrawl.py        # Anti-crawling technology tests
├── app.py                  # Streamlit main application
├── run.py                  # Startup script
└── requirements.txt        # Project dependencies
```

### ⚠️ Usage Notes

- This system is designed for legal collection of public information; please comply with relevant laws, regulations, and website terms of use
- It is recommended to limit crawling frequency to avoid excessive burden on target websites
- Data accuracy depends on source websites; results are for reference only, please verify information for important decisions
- Update crawler selectors regularly to adapt to changes in target websites

### 📄 License

This project is licensed under the [MIT License](LICENSE).

### 👥 Contribution Guidelines

Contributions of code or suggestions are welcome! Please follow these steps:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Create a Pull Request

# RiverInfos - Construction Company Information Crawler

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Streamlit](https://img.shields.io/badge/streamlit-1.0+-red.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

**[English](#detailed-english-description)**

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


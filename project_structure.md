# RiverInfos Project Structure

```
riverInfos/
├── crawlers/
│   ├── news/
│   │   ├── google_news.py
│   │   ├── bing_news.py
│   │   ├── hk_news.py                  # 香港本地新闻
│   │   └── construction_news.py        # 建筑行业新闻
│   ├── social/
│   │   ├── twitter_public.py
│   │   ├── linkedin_public.py          # 领英公开信息
│   │   └── facebook_public.py          # 脸书公开页面
│   ├── government/
│   │   ├── sec_edgar.py
│   │   ├── china_company.py
│   │   ├── hk_companies_registry.py    # 香港公司注册处
│   │   ├── hk_judiciary.py             # 香港司法记录
│   │   └── intl_tenders.py             # 国际项目招标信息
│   └── industry/
│       ├── construction_qualifications.py  # 建筑资质认证
│       ├── environmental_compliance.py     # 环保合规记录
│       └── project_history.py             # 项目历史
├── core/
│   ├── anticrawl.py                    # 反爬对抗模块
│   ├── storage.py                      # 存储控制器
│   └── utils.py                        # 通用工具函数
├── adapters/
│   ├── file_upload/
│   │   ├── pdf_processor.py            # PDF文件处理
│   │   ├── excel_processor.py          # Excel文件处理
│   │   └── file_handler.py             # 文件上传处理器
│   └── ai_hooks/
│       ├── sentiment_analysis.py       # 情感分析钩子
│       └── nlp_processor.py            # NLP处理接口
├── tests/
│   ├── test_crawlers.py
│   ├── test_file_processors.py
│   └── test_anticrawl.py
├── app.py                              # Streamlit主界面
├── requirements.txt                    # 项目依赖
└── README.md                           # 项目说明
``` 
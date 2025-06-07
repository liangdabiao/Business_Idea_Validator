### # 商业创意验证器 评论调研应用程序

我开发了一个市场调研AI，输入一个生意点子，例如“在苏州卖陈皮”，随意都可以，商业调研：“新会陈皮在深圳人的口碑” 等等， 然后AI就到小红书大量收集资料和评论分析，得出这个生意靠谱不，用户怎样评价等等
#开发 #创新解决方案 #开发新客户 #技术解决方案 #开发者选项 #行业研究 #研究报告 #个人开发者 #开发者模式 #产品经理 #AI工具

这是一种 AI 驱动的工具，可通过自动 Web 抓取和智能分析来验证业务概念。该系统通过分析在线讨论和生成评分验证报告来评估市场需求、竞争水平和可行性。
这是一款专业的商业调研应用程序，为用户提供友好的界面来：1.验证商业创意 ， 2.分析用户评论。

该应用通过分析网络讨论，识别与您商业创意相关的痛点、兴奋信号和竞争对手。 分析用户评论,得出多维度商业数据分析。

目前数据收集主要在：小红书，公众号，reddit，hacker news,其他社交媒体和重要渠道都可以轻松加入， 整合了多个第三方数据方案。第三方数据方案:
https://www.scraperapi.com/ , https://api.tikhub.io ,等等。

参考教程：https://juejin.cn/post/7511247197331456027 《基于AI大模型开发一个小红书商业调研应用》
https://juejin.cn/post/7504007819075862555 《教你一键分析小红书评论-利用chatgpt+web scraper分析喜茶“芝芝柑普”》

需要amazon评论分析,trustpilot评论分析，请看看我的另一个项目： https://github.com/liangdabiao/easy-amazon-voc

本项目灵感和基础代码参考：github.com/hassancs91/scraper-api ，我增加大量功能和修改，适合国内用户进行商业调研，收集数据，可视化分析，评论分析，多渠道商业分析等等。

## 功能特点

- 输入商业创意并获取验证结果
- 通过交互式图表可视化验证评分
- 查看痛点、兴奋信号和竞争对手的详细分析
- 获取包含建议的专业执行摘要
- 支持JSON格式报告下载

## 系统要求

- Python 3.9+
- 依赖项详见`requirements.txt`

## 安装指南

1. 克隆本代码库
2. 安装所需依赖：

```bash
pip install -r requirements.txt
```

3. 秘钥配置：

数据接口key配置在 business_validator/config.py
OPENAI_API等大模型key 配置：openai_llm.py



## 使用说明

1. 运行应用入口：

```bash
streamlit run business_validator_ui.py   # hackernews reddit 商业调研
streamlit run business_validator_ui_cn.py   # 小红书商业调研
python app.py   # 小红书评论分析
python app_reddit.py # reddit评论分析
```

2. 打开浏览器访问终端显示的URL（通常是http://localhost:8501）

3. 在文本区域输入商业创意，点击"验证商业创意"

4. 等待验证流程完成

5. 查看结果并按需下载报告

## 工作原理

商业创意验证器：

1. 接收用户输入的商业创意
2. 生成相关关键词
3. 在Reddit、ProductHunt、小红书等平台搜索相关讨论
4. 使用AI分析内容并提取：
   - 用户痛点
   - 市场兴奋信号
   - 竞争对手信息
   - 代表性用户评论
   - 潜在风险信号
5. 基于分析结果计算评分
6. 生成包含建议的执行摘要

Analysis Framework
分析框架

Content analysis uses structured Pydantic models to ensure consistent data extraction:
内容分析使用结构化的 Pydantic 模型来确保一致的数据提取：

TextWithRelevance: Associates text content with relevance scores (0-10)
TextWithRelevance：将文本内容与相关性分数关联 （0-10）
BusinessIdeaAnalysis: Comprehensive analysis including pain points, excitement signals, competitors, notable quotes, red flags, and coherence scores
BusinessIdeaAnalysis：综合分析，包括痛点、兴奋信号、竞争对手、值得注意的引述、危险信号和连贯性分数
KeywordModel: Validated list of generated keywords
KeywordModel：已验证的已生成关键字列表


## 配置说明

应用通过 文件配置：

- ScraperAPI和OpenAI的API密钥
- 不同因素的评分权重
- 验证阈值设置
- 每个站点的抓取页数
- 生成关键词数量

## 许可协议

本项目采用MIT许可证，详见LICENSE文件。
代码参考开源项目： github.com/hassancs91/scraper-api


## 展示图片报告

小红书商业调研：
![Class Diagram](report_demo/微信图片_20250602191051.png)
![Class Diagram](report_demo/微信图片_20250602191058.png)
![Class Diagram](report_demo/微信图片_20250602191105.png)

小红书评论分析：
![Class Diagram](report_demo/微信截图_20250601091702.png)
![Class Diagram](report_demo/微信图片_20250606210915.png)

reddit评论分析：
![Class Diagram](report_demo/微信图片_20250606210802.png)

![Class Diagram](report_demo/微信图片_20250606210915.png)
![Class Diagram](report_demo/微信图片_20250606210919.png)
![Class Diagram](report_demo/微信图片_20250606210927.png)

reddit商业调研：
![Class Diagram](report_demo/微信截图_20250601091510.png)
![Class Diagram](report_demo/微信截图_20250601091649.png)

![Class Diagram](report_demo/微信截图_20250601091702.png)

![Class Diagram](report_demo/微信截图_20250601093444.png)



# Business Idea Validator Streamlit App

A professional Streamlit application that provides a user-friendly interface for validating business ideas. This app analyzes online discussions to identify pain points, excitement signals, and competitors related to your business idea.

## Features

- Input your business idea and get it validated
- Visualize validation scores with interactive charts
- View detailed analysis of pain points, excitement signals, and competitors
- Get professional executive summary with recommendations
- Download reports in JSON format

## Requirements

- Python 3.9+
- Dependencies listed in `requirements.txt`

## Installation

1. Clone this repository
2. Install the required dependencies:

```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:

```bash
streamlit run business_validator_ui.py   # hackernews reddit 商业调研
streamlit run business_validator_ui_cn.py   # 小红书  商业调研
python app.py   # 小红书评论分析
python app_reddit.py #reddit评论分析
```

2. Open your web browser and navigate to the URL displayed in the terminal (typically http://localhost:8501)

3. Enter your business idea in the text area and click "Validate Business Idea"

4. Wait for the validation process to complete

5. Review the results and download reports if needed

## How It Works

The Business Idea Validator:

1. Takes your business idea as input
2. Generates relevant keywords
3. Searches online platforms (Reddit, ProductHunt) for discussions related to these keywords
4. Analyzes the content using AI to extract:
   - Pain points
   - Excitement signals
   - Competitors
   - Notable quotes
   - Red flags
5. Calculates scores based on the findings
6. Generates an executive summary with recommendations

## Configuration

The app uses the following configuration from `test_enhanced.py`:

- API keys for ScraperAPI and OpenAI
- Scoring weights for different factors
- Validation thresholds
- Number of pages to fetch per site
- Number of keywords to generate

## License

This project is licensed under the MIT License - see the LICENSE file for details.








 
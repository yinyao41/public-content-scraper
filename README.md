# public-content-scraper
# 微博 & 微信公众号公开内容爬取系统

基于 Streamlit 的可视化爬取工具，支持输入微博 UID 或微信公众号名称，直接爬取公开内容并下载。  
**已支持实时进度条显示**。

## 功能特点

- 微博：输入 UID 爬取用户公开微博（支持只爬原创、页数控制）
- 微信公众号：支持 Cookie + Token 获取历史文章，或搜狗搜索兜底
- 实时进度条 + 状态文字提示
- 结果一键下载 CSV

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
playwright install chromium

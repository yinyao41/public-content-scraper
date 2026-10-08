import pandas as pd
import requests
import time
import json
from typing import Optional, Callable
from bs4 import BeautifulSoup
from urllib.parse import quote


def crawl_wechat(
    account: str,
    cookie: str = "",
    token: str = "",
    max_count: int = 20,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Optional[pd.DataFrame]:
    """
    微信公众号文章爬取（支持进度回调）
    """
    if cookie and token:
        return _crawl_with_cookie(account, cookie, token, max_count, progress_callback)
    else:
        return _crawl_with_sogou(account, max_count, progress_callback)


def _crawl_with_cookie(
    account: str,
    cookie: str,
    token: str,
    max_count: int,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Optional[pd.DataFrame]:
    headers = {
        "Cookie": cookie,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    if progress_callback:
        progress_callback(0.05, "正在搜索公众号...")

    # 搜索公众号获取 fakeid
    search_url = "https://mp.weixin.qq.com/cgi-bin/searchbiz"
    params = {
        "action": "search_biz",
        "begin": 0,
        "count": 5,
        "query": account,
        "token": token,
        "lang": "zh_CN",
        "f": "json",
        "ajax": 1
    }

    try:
        resp = requests.get(search_url, params=params, headers=headers, timeout=15)
        data = resp.json()
        if data.get("base_resp", {}).get("ret") != 0:
            return None

        list_data = data.get("list", [])
        if not list_data:
            return None

        fakeid = list_data[0]["fakeid"]
        nickname = list_data[0]["nickname"]
    except Exception as e:
        print(f"搜索公众号异常: {e}")
        return None

    if progress_callback:
        progress_callback(0.15, f"找到公众号：{nickname}，开始获取文章列表...")

    articles = []
    begin = 0
    count = 5
    max_loops = (max_count // count) + 2

    for loop in range(max_loops):
        if len(articles) >= max_count:
            break

        if progress_callback:
            progress = 0.15 + (loop / max_loops) * 0.8
            progress_callback(progress, f"正在获取第 {loop+1} 批文章... 当前已获取 {len(articles)} 篇")

        appmsg_url = "https://mp.weixin.qq.com/cgi-bin/appmsgpublish"
        params = {
            "sub": "list",
            "search_field": "null",
            "begin": begin,
            "count": count,
            "query": "",
            "fakeid": fakeid,
            "type": "101_1",
            "free_publish_type": 1,
            "sub_action": "list_ex",
            "token": token,
            "lang": "zh_CN",
            "f": "json",
            "ajax": 1
        }

        try:
            resp = requests.get(appmsg_url, params=params, headers=headers, timeout=15)
            data = resp.json()
            if data.get("base_resp", {}).get("ret") != 0:
                break

            publish_page = data.get("publish_page")
            if not publish_page:
                break

            publish_list = json.loads(publish_page).get("publish_list", [])
            if not publish_list:
                break

            for item in publish_list:
                for art in item.get("publish_info", {}).get("appmsgex", []):
                    articles.append({
                        "标题": art.get("title", ""),
                        "链接": art.get("link", ""),
                        "发布时间": art.get("create_time", ""),
                        "摘要": art.get("digest", ""),
                        "封面": art.get("cover", ""),
                        "公众号": nickname
                    })
                    if len(articles) >= max_count:
                        break
                if len(articles) >= max_count:
                    break

            begin += count
            time.sleep(2)
        except Exception as e:
            print(f"获取文章列表异常: {e}")
            break

    if progress_callback:
        progress_callback(1.0, f"完成！共获取 {len(articles)} 篇文章")

    if not articles:
        return None

    return pd.DataFrame(articles)


def _crawl_with_sogou(
    account: str,
    max_count: int = 10,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Optional[pd.DataFrame]:
    if progress_callback:
        progress_callback(0.3, "使用搜狗搜索（免登录模式）...")

    url = f"https://weixin.sogou.com/weixin?type=1&query={quote(account)}&ie=utf8"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    try:
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "lxml")

        results = []
        items = soup.select(".news-list2 li")[:max_count]
        for i, item in enumerate(items):
            if progress_callback:
                progress_callback(0.3 + (i / max(len(items), 1)) * 0.6, f"解析第 {i+1} 条...")
            title_tag = item.select_one(".tit")
            if title_tag:
                results.append({
                    "标题": title_tag.get_text(strip=True),
                    "链接": "",
                    "发布时间": "",
                    "摘要": "",
                    "封面": "",
                    "公众号": account
                })

        if progress_callback:
            progress_callback(1.0, f"完成！共获取 {len(results)} 条结果")

        if results:
            return pd.DataFrame(results)
        return None
    except Exception as e:
        print(f"搜狗搜索失败: {e}")
        return None

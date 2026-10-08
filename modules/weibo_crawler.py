import requests
import pandas as pd
import time
import re
from typing import Optional, Callable
from bs4 import BeautifulSoup


def crawl_weibo(
    uid: str,
    only_original: bool = True,
    max_pages: int = 10,
    delay: float = 1.5,
    cookie: str = "",
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Optional[pd.DataFrame]:
    """
    改进版纯 requests 微博爬虫（提高完整性）
    强烈建议填写 Cookie 以获取更多内容
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://m.weibo.cn/u/{uid}",
        "MWeibo-Pwa": "1",
        "X-Requested-With": "XMLHttpRequest",
    }

    if cookie:
        headers["Cookie"] = cookie.strip()

    session = requests.Session()
    session.headers.update(headers)

    all_posts = []
    seen_ids = set()
    since_id = None

    for page in range(1, max_pages + 1):
        if progress_callback:
            progress = (page - 1) / max_pages
            progress_callback(progress, f"正在爬取第 {page}/{max_pages} 页，当前已获取 {len(all_posts)} 条...")

        # 构建 URL
        if page == 1:
            url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}"
        else:
            if since_id:
                url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}&since_id={since_id}"
            else:
                url = f"https://m.weibo.cn/api/container/getIndex?type=uid&value={uid}&containerid=107603{uid}&page={page}"

        try:
            resp = session.get(url, timeout=20)
            if resp.status_code != 200:
                break

            data = resp.json()
            if data.get("ok") != 1:
                # 尝试换一种翻页方式
                if page > 1:
                    break
                continue

            cards = data.get("data", {}).get("cards", [])
            if not cards:
                break

            new_count = 0
            for card in cards:
                mblog = card.get("mblog")
                if not mblog:
                    continue

                mid = str(mblog.get("id", ""))
                if mid in seen_ids:
                    continue
                seen_ids.add(mid)

                # 是否原创
                is_retweet = "retweeted_status" in mblog
                if only_original and is_retweet:
                    continue

                # 处理正文（去除 HTML 标签）
                text = mblog.get("text", "")
                text = BeautifulSoup(text, "lxml").get_text(separator="\n").strip()

                # 图片
                pics = []
                if mblog.get("pics"):
                    for p in mblog["pics"]:
                        large = p.get("large", {}).get("url") or p.get("url", "")
                        if large:
                            pics.append(large)

                # 视频
                video_url = ""
                page_info = mblog.get("page_info") or {}
                if page_info.get("type") == "video":
                    media = page_info.get("media_info") or {}
                    video_url = media.get("stream_url_hd") or media.get("stream_url") or ""

                all_posts.append({
                    "微博ID": mid,
                    "内容": text,
                    "发布时间": mblog.get("created_at", ""),
                    "转发数": mblog.get("reposts_count", 0),
                    "评论数": mblog.get("comments_count", 0),
                    "点赞数": mblog.get("attitudes_count", 0),
                    "是否原创": "是" if not is_retweet else "否",
                    "图片链接": ",".join(pics),
                    "视频链接": video_url,
                })
                new_count += 1

            # 获取下一页 since_id
            cardlist_info = data.get("data", {}).get("cardlistInfo", {})
            since_id = cardlist_info.get("since_id") or since_id

            if new_count == 0:
                break

            time.sleep(delay)

        except Exception as e:
            print(f"第 {page} 页失败: {e}")
            time.sleep(2)
            continue

    if progress_callback:
        progress_callback(1.0, f"完成！共获取 {len(all_posts)} 条微博")

    if not all_posts:
        return None

    return pd.DataFrame(all_posts)

import pandas as pd
from typing import Optional, Callable
import time
import os
import subprocess

try:
    from crawl4weibo import WeiboClient
except ImportError:
    WeiboClient = None


def _try_install_playwright():
    """尝试自动安装 Playwright 浏览器（仅本地有效）"""
    try:
        subprocess.run(["playwright", "install", "chromium"], check=False, timeout=120)
        return True
    except Exception:
        return False


def crawl_weibo(
    uid: str,
    only_original: bool = True,
    max_pages: int = 5,
    delay: float = 1.5,
    progress_callback: Optional[Callable[[float, str], None]] = None
) -> Optional[pd.DataFrame]:
    if WeiboClient is None:
        raise ImportError("请先安装 crawl4weibo: pip install crawl4weibo")

    if progress_callback:
        progress_callback(0.02, "正在初始化微博客户端...")

    try:
        client = WeiboClient()
    except Exception as e:
        err_msg = str(e)
        if "Executable doesn't exist" in err_msg or "playwright" in err_msg.lower():
            # 尝试自动安装
            if progress_callback:
                progress_callback(0.05, "检测到缺少浏览器内核，正在尝试自动安装 Chromium...")
            success = _try_install_playwright()
            if success:
                client = WeiboClient()
            else:
                raise RuntimeError(
                    "Playwright 浏览器未安装。\n"
                    "请在终端运行以下命令后重试：\n\n"
                    "playwright install chromium\n\n"
                    "如果是 Streamlit Cloud，请参考 README 中的 Cloud 部署说明。"
                )
        else:
            raise e

    all_posts = []

    for page in range(1, max_pages + 1):
        if progress_callback:
            progress = (page - 1) / max_pages
            progress_callback(progress, f"正在爬取第 {page}/{max_pages} 页...")

        try:
            posts = client.get_user_posts(uid, page=page, expand=True)
            if not posts:
                break
            all_posts.extend(posts)
            time.sleep(delay)
        except Exception as e:
            print(f"第 {page} 页爬取失败: {e}")
            break

    if progress_callback:
        progress_callback(0.95, "正在整理数据...")

    if not all_posts:
        return None

    data = []
    for p in all_posts:
        is_retweet = getattr(p, "retweeted_status", None) is not None or getattr(p, "is_retweet", False)
        if only_original and is_retweet:
            continue

        data.append({
            "微博ID": getattr(p, "id", ""),
            "内容": getattr(p, "text", ""),
            "发布时间": getattr(p, "created_at", ""),
            "转发数": getattr(p, "reposts_count", 0),
            "评论数": getattr(p, "comments_count", 0),
            "点赞数": getattr(p, "attitudes_count", 0),
            "是否原创": "是" if not is_retweet else "否",
            "图片链接": ",".join(getattr(p, "pic_urls", []) or []),
            "视频链接": getattr(p, "video_url", "") or "",
        })

    if progress_callback:
        progress_callback(1.0, f"完成！共获取 {len(data)} 条微博")

    return pd.DataFrame(data)

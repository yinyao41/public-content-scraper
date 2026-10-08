import os
import subprocess

# Streamlit Cloud 专用：安装 Playwright 浏览器 + 系统依赖
if os.path.exists("/home/appuser"):
    try:
        # 安装系统依赖（通过 packages.txt 已经处理大部分）
        subprocess.run(["playwright", "install-deps"], check=False, timeout=60)
        # 安装 Chromium
        subprocess.run(["playwright", "install", "chromium"], check=False, timeout=180)
    except Exception:
        pass

import streamlit as st
import pandas as pd
from modules.weibo_crawler import crawl_weibo
from modules.wechat_crawler import crawl_wechat
from modules.utils import save_dataframe

st.set_page_config(
    page_title="微博 & 微信公众号公开内容爬取系统",
    page_icon="🕷️",
    layout="wide"
)

st.title("🕷️ 微博 & 微信公众号公开内容爬取系统")
st.markdown("输入用户 ID 即可爬取公开内容，结果支持下载 CSV。支持实时进度显示。")

tab1, tab2 = st.tabs(["📱 微博爬取", "📢 微信公众号爬取"])

# ==================== 微博 Tab ====================
with tab1:
    st.subheader("微博用户公开内容爬取")

    col1, col2 = st.columns([2, 1])
    with col1:
        weibo_uid = st.text_input(
            "微博 UID",
            placeholder="例如：2656274875（央视新闻）",
            help="在微博用户主页地址栏中获取，格式为 weibo.com/u/数字",
            key="weibo_uid"
        )
    with col2:
        only_original = st.checkbox("只爬原创微博", value=True, key="only_original")

    max_pages = st.slider("最大爬取页数（每页约 10~20 条）", 1, 30, 5, key="max_pages")

    if st.button("🚀 开始爬取微博", type="primary", use_container_width=True, key="btn_weibo"):
        if not weibo_uid.strip():
            st.error("请输入微博 UID")
        else:
            # 创建进度条和状态文本
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(progress: float, message: str):
                progress_bar.progress(min(progress, 1.0))
                status_text.text(message)

            try:
                df = crawl_weibo(
                    uid=weibo_uid.strip(),
                    only_original=only_original,
                    max_pages=max_pages,
                    progress_callback=update_progress
                )

                if df is not None and not df.empty:
                    st.success(f"✅ 成功获取 {len(df)} 条微博")
                    st.dataframe(df, use_container_width=True)

                    csv = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label="📥 下载 CSV 文件",
                        data=csv,
                        file_name=f"weibo_{weibo_uid}.csv",
                        mime="text/csv"
                    )

                    path = save_dataframe(df, f"weibo_{weibo_uid}")
                    st.info(f"结果已保存到：{path}")
                else:
                    st.warning("未获取到数据，请检查 UID 是否正确，或稍后重试")
            except Exception as e:
                st.error(f"爬取失败：{str(e)}")
            finally:
                # 清理进度显示
                progress_bar.empty()
                status_text.empty()

# ==================== 微信公众号 Tab ====================
with tab2:
    st.subheader("微信公众号文章爬取")

    st.info(
        "推荐方式：登录 [微信公众平台](https://mp.weixin.qq.com) 后，获取 Cookie 和 Token，可获取较完整历史文章。"
        "不填则使用搜狗搜索（仅最近少量文章，成功率较低）。"
    )

    account = st.text_input("公众号名称 或 fakeid", placeholder="例如：央视新闻", key="account")

    with st.expander("🔑 高级设置（推荐填写 Cookie + Token）", expanded=False):
        cookie = st.text_area("Cookie", height=100, help="从浏览器开发者工具中复制完整 Cookie", key="cookie")
        token = st.text_input("Token", help="在公众平台页面源代码或网络请求中可找到", key="token")

    max_articles = st.slider("最大文章数量", 5, 100, 20, key="max_articles")

    if st.button("🚀 开始爬取公众号", type="primary", use_container_width=True, key="btn_wechat"):
        if not account.strip():
            st.error("请输入公众号名称")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()

            def update_progress(progress: float, message: str):
                progress_bar.progress(min(progress, 1.0))
                status_text.text(message)

            try:
                df = crawl_wechat(
                    account=account.strip(),
                    cookie=cookie.strip(),
                    token=token.strip(),
                    max_count=max_articles,
                    progress_callback=update_progress
                )

                if df is not None and not df.empty:
                    st.success(f"✅ 成功获取 {len(df)} 篇文章")
                    st.dataframe(df, use_container_width=True)

                    csv = df.to_csv(index=False).encode("utf-8-sig")
                    st.download_button(
                        label="📥 下载 CSV 文件",
                        data=csv,
                        file_name=f"wechat_{account}.csv",
                        mime="text/csv"
                    )

                    path = save_dataframe(df, f"wechat_{account}")
                    st.info(f"结果已保存到：{path}")
                else:
                    st.warning("未获取到数据。建议填写 Cookie 和 Token 后重试")
            except Exception as e:
                st.error(f"爬取失败：{str(e)}")
            finally:
                progress_bar.empty()
                status_text.empty()

st.markdown("---")
st.caption("仅用于学习研究公开内容，请遵守平台规则与相关法律法规。")

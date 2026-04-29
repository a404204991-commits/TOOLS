import streamlit as st
import fitz
import pdfplumber
import os
import io
from PIL import Image

# 页面配置
st.set_page_config(page_title="万能PDF图文提取工具", page_icon="📄", layout="wide")
st.title("📄 万能PDF图文提取工具（适配所有排版）")
st.caption("智能筛选项目图片，不依赖固定排版 | 支持自定义过滤+手动勾选")

# ===================== 【通用筛选控制面板】 =====================
st.sidebar.header("⚙️ 图片筛选规则")
# 1. 自定义尺寸阈值（通用可调）
min_width = st.sidebar.slider("最小宽度（像素）", 200, 2000, 800)
min_height = st.sidebar.slider("最小高度（像素）", 200, 2000, 600)
# 2. 比例过滤（剔除细长logo）
enable_ratio_filter = st.sidebar.checkbox("开启比例过滤（剔除长条logo）", value=True)
max_ratio = st.sidebar.slider("最大宽高比", 1.0, 5.0, 3.0)
# 3. 页码范围（自由选择）
st.sidebar.divider()
page_start = st.sidebar.number_input("起始页码", 0, 999, 0)
page_end = st.sidebar.number_input("结束页码", 0, 999, 999)
# ==============================================================

def extract_clean_text(pdf_file):
    """提取纯净文字（通用版，无固定排版过滤）"""
    core_text = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            # 自定义页码范围
            end = min(page_end, total_pages)
            for page_num in range(page_start, end):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if text:
                    core_text.append(text)
    except Exception as e:
        st.error(f"文字提取失败：{str(e)}")
        return ""
    return "\n\n".join(core_text)

def extract_all_images(pdf_file):
    """提取所有图片 + 智能过滤（通用版）"""
    filtered_images = []
    try:
        doc = fitz.open("pdf", pdf_file.read())
        total_pages = doc.page_count
        end = min(page_end, total_pages)

        for page_num in range(page_start, end):
            page = doc[page_num]
            img_list = page.get_images(full=True)

            for img in img_list:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                # 处理透明通道
                if pix.n >= 5:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                w, h = pix.width, pix.height
                # ===================== 通用过滤规则 =====================
                # 1. 尺寸过滤
                if w < min_width or h < min_height:
                    pix = None
                    continue
                # 2. 比例过滤（剔除细长logo）
                if enable_ratio_filter:
                    ratio = max(w/h, h/w)
                    if ratio > max_ratio:
                        pix = None
                        continue
                # ======================================================

                # 转PIL图片
                img_bytes = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_bytes))
                filtered_images.append((page_num+1, pil_img))  # 记录页码
                pix = None

    except Exception as e:
        st.error(f"图片提取失败：{str(e)}")
        return []
    return filtered_images

# ===================== 主界面 =====================
uploaded_file = st.file_uploader("上传任意PDF文件", type="pdf")

if uploaded_file is not None:
    # 1. 提取文字
    with st.spinner("提取文字中..."):
        clean_text = extract_clean_text(uploaded_file)
        with st.expander("📝 查看/下载核心文字", expanded=True):
            st.text_area("文本内容", clean_text, height=250)
            st.download_button("💾 下载文字", clean_text, "核心文字.txt", "text/plain")

    # 重置文件
    uploaded_file.seek(0)

    # 2. 提取并筛选图片
    with st.spinner("提取并智能筛选图片中..."):
        images = extract_all_images(uploaded_file)
        st.subheader(f"🖼️ 智能筛选后图片（共{len(images)}张）")

        if images:
            # 手动勾选功能（万能兜底，适配任何排版）
            selected_imgs = []
            cols = st.columns(3)
            for idx, (page, img) in enumerate(images):
                with cols[idx % 3]:
                    st.image(img, caption=f"第{page}页 - 图{idx+1}", use_column_width=True)
                    if st.checkbox(f"保留此图", key=f"img_{idx}", value=True):
                        selected_imgs.append(img)

            st.divider()
            st.success(f"✅ 已选中 {len(selected_imgs)} 张项目图片")
            
            # 批量下载
            if st.button("📥 下载选中的所有图片"):
                with st.spinner("打包下载中..."):
                    for i, img in enumerate(selected_imgs):
                        buf = io.BytesIO()
                        img.save(buf, format="PNG")
                        st.download_button(
                            label=f"下载项目图{i+1}",
                            data=buf.getvalue(),
                            file_name=f"项目图_{i+1}.png",
                            mime="image/png"
                        )
        else:
            st.warning("未筛选到符合条件的图片，可降低尺寸阈值重试")

    st.balloons()

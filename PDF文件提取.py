import streamlit as st
import fitz
import pdfplumber
import os
import io
from PIL import Image

# 页面配置
st.set_page_config(page_title="PDF项目图文提取工具", page_icon="📄", layout="wide")
st.title("📄 PDF 项目图文提取工具")
st.caption("仅提取：项目核心文字 + 实景/设计图 | 自动剔除Logo、广告、尾页推荐图")

# ---------------------- 核心参数 ----------------------
FILTER_MIN_WIDTH = 800    # 过滤小图标/Logo
FILTER_MIN_HEIGHT = 600
FILTER_END_PAGES = 5      # 跳过最后5页广告
# ------------------------------------------------------

def extract_clean_text(pdf_file):
    """提取清洗后的核心文字"""
    core_text = []
    try:
        with pdfplumber.open(pdf_file) as pdf:
            total_pages = len(pdf.pages)
            end_page = max(0, total_pages - FILTER_END_PAGES)
            
            for page_num in range(end_page):
                page = pdf.pages[page_num]
                text = page.extract_text()
                if not text:
                    continue
                
                # 过滤广告/标识文字
                filter_keys = ["安邸AD", "推荐阅读", "播客", "订阅", "ARCHITECTURAL DIGEST", 
                              "AD100", "粉丝破百万", "全新上市", "快请进家里聊聊"]
                lines = [line.strip() for line in text.split("\n") if line.strip()]
                clean_lines = [l for l in lines if not any(key in l for key in filter_keys)]
                core_text.extend(clean_lines)
    
    except Exception as e:
        st.error(f"文字提取失败：{str(e)}")
        return ""
    
    return "\n".join(core_text)

def extract_filtered_images(pdf_file):
    """提取过滤后的项目图片（无Logo/广告）"""
    project_images = []
    try:
        doc = fitz.open("pdf", pdf_file.read())
        total_pages = doc.page_count
        end_page = max(0, total_pages - FILTER_END_PAGES)

        for page_num in range(end_page):
            page = doc[page_num]
            img_list = page.get_images(full=True)

            for img in img_list:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                
                # 处理透明通道
                if pix.n >= 5:
                    pix = fitz.Pixmap(fitz.csRGB, pix)

                w, h = pix.width, pix.height
                # 过滤小尺寸Logo
                if w < FILTER_MIN_WIDTH or h < FILTER_MIN_HEIGHT:
                    pix = None
                    continue

                # 转为PIL图片
                img_bytes = pix.tobytes("png")
                pil_img = Image.open(io.BytesIO(img_bytes))
                project_images.append(pil_img)
                pix = None

    except Exception as e:
        st.error(f"图片提取失败：{str(e)}")
        return []
    
    return project_images

# ---------------------- 主界面 ----------------------
uploaded_file = st.file_uploader("上传PDF文件", type="pdf")

if uploaded_file is not None:
    st.success("✅ 文件上传成功！开始提取...")
    
    # 1. 提取文字
    with st.spinner("正在提取核心文字..."):
        clean_text = extract_clean_text(uploaded_file)
        st.subheader("📝 提取的核心文字")
        st.text_area("纯净文本", clean_text, height=300)
        
        # 文字下载
        text_io = io.StringIO(clean_text)
        st.download_button(
            label="💾 下载文字文件",
            data=text_io.getvalue(),
            file_name="项目核心文字.txt",
            mime="text/plain"
        )

    # 重置文件指针
    uploaded_file.seek(0)

    # 2. 提取图片
    with st.spinner("正在提取项目图片..."):
        images = extract_filtered_images(uploaded_file)
        st.subheader(f"🖼️ 提取的项目原图（共{len(images)}张）")
        
        if images:
            # 网格展示图片
            cols = st.columns(3)
            for idx, img in enumerate(images):
                with cols[idx % 3]:
                    st.image(img, caption=f"项目图 {idx+1}", use_column_width=True)
        else:
            st.warning("未提取到符合条件的项目图片")

    st.balloons()
    st.success("🎉 提取完成！仅保留项目核心图文，已剔除所有广告/Logo")

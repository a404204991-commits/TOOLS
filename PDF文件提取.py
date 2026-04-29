import fitz  # PyMuPDF 用于提取图片
import pdfplumber  # 用于提取文字
import os
from PIL import Image

# ===================== 【配置区】按需修改 =====================
PDF_PATH = "西安灞河边，推开家门跃进游园秘境.pdf"  # 你的PDF文件路径
OUTPUT_FOLDER = "pdf_extract_result"  # 输出文件夹
PIC_FOLDER = f"{OUTPUT_FOLDER}/project_images"  # 项目图片保存文件夹
TEXT_PATH = f"{OUTPUT_FOLDER}/core_text.txt"  # 核心文字保存路径

# 图片过滤规则（剔除logo/小图标/尾页广告图）
FILTER_MIN_WIDTH = 800    # 最小宽度（小于此判定为logo）
FILTER_MIN_HEIGHT = 600   # 最小高度（小于此判定为logo）
FILTER_END_PAGES = 5      # 剔除最后5页（广告/推荐/播客都在尾页）
# ==============================================================

def extract_clean_text(pdf_path, save_path):
    """提取并清洗PDF核心文字（剔除广告、互动、尾页）"""
    core_text = []
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        # 只提取前N-5页（剔除尾页广告）
        for page_num in range(total_pages - FILTER_END_PAGES):
            page = pdf.pages[page_num]
            text = page.extract_text()
            if not text:
                continue
            # 剔除无关文字
            lines = [line.strip() for line in text.split("\n") if line.strip()]
            lines = [l for l in lines if not any(key in l for key in [
                "安邸AD", "推荐阅读", "话题互动", "播客", "订阅", "ARCHITECTURAL DIGEST",
                "全新上市", "粉丝破百万", "AD100", "快请进家里聊聊"
            ])]
            core_text.extend(lines)
    
    # 保存纯净文字
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    with open(save_path, "w", encoding="utf-8") as f:
        f.write("\n".join(core_text))
    print(f"✅ 核心文字已保存：{save_path}")

def extract_project_images(pdf_path, save_folder):
    """提取并过滤【仅项目图片】，剔除logo/广告/尾页图"""
    os.makedirs(save_folder, exist_ok=True)
    doc = fitz.open(pdf_path)
    total_pages = doc.page_count
    img_index = 1

    for page_num in range(total_pages - FILTER_END_PAGES):
        page = doc[page_num]
        img_list = page.get_images(full=True)
        
        for img in img_list:
            xref = img[0]
            # 提取图片
            pix = fitz.Pixmap(doc, xref)
            # 转RGB（避免透明通道报错）
            if pix.n >= 5:
                pix = fitz.Pixmap(fitz.csRGB, pix)
            
            # 获取图片尺寸
            w, h = pix.width, pix.height
            # 过滤：太小=logo，直接跳过
            if w < FILTER_MIN_WIDTH or h < FILTER_MIN_HEIGHT:
                pix = None
                continue
            
            # 保存项目图片
            img_path = os.path.join(save_folder, f"project_img_{img_index}.png")
            pix.save(img_path)
            pix = None
            img_index += 1

    print(f"✅ 项目图片已提取：{img_index-1}张，保存至：{save_folder}")

if __name__ == "__main__":
    print("🚀 开始提取PDF文字+项目图片...")
    # 1. 提取纯净文字
    extract_clean_text(PDF_PATH, TEXT_PATH)
    # 2. 提取过滤后的项目图片
    extract_project_images(PDF_PATH, PIC_FOLDER)
    print("🎉 提取完成！所有结果在：pdf_extract_result 文件夹")

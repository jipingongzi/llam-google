import fitz  # PyMuPDF
from pathlib import Path
import os


def pdf_image_pages_to_images(pdf_path,
                              output_relative_dir="../doc/pic",
                              img_format="png",
                              dpi=200):
    try:
        current_file_path = Path(os.path.abspath(__file__))
        current_file_dir = current_file_path.parent
        output_dir = current_file_dir / output_relative_dir
        output_dir.mkdir(parents=True, exist_ok=True)

        pdf_path = Path(pdf_path).resolve()

        if not pdf_path.exists():
            return []
        if pdf_path.suffix.lower() != ".pdf":
            return []

        pdf_name = pdf_path.stem
        image_paths = []
        image_pages = []

        zoom = dpi / 72
        render_matrix = fitz.Matrix(zoom, zoom)
        fitz.TOOLS.set_aa_level(3)

        with fitz.open(pdf_path) as pdf_doc:
            total_pages = len(pdf_doc)
            print(f"检测到PDF共{total_pages}页，仅处理含图片的页面...")

            for page_idx in range(total_pages):
                page = pdf_doc[page_idx]
                actual_page_num = page_idx + 1

                if page.get_images(full=False):
                    image_pages.append(actual_page_num)

                    page_img = page.get_pixmap(
                        matrix=render_matrix,
                        alpha=False,
                        colorspace=fitz.csRGB
                    )

                    img_filename = f"{pdf_name}_page{actual_page_num}.{img_format}"
                    img_save_path = output_dir / img_filename

                    if img_format.lower() == "jpg":
                        page_img.save(str(img_save_path), quality=95)
                    else:
                        page_img.save(str(img_save_path))

                    image_paths.append(str(img_save_path.resolve()))
                    print(f"已转换：第{actual_page_num}页 → {img_save_path.name}")
                else:
                    print(f"跳过：第{actual_page_num}页（无图片）")

        if not image_paths:
            return []
        else:
            return image_paths

    except Exception as e:
        print(str(e))
        return []

if __name__ == "__main__":
    TEST_PDF_PATH = "test.pdf"

    result = pdf_image_pages_to_images(
        pdf_path=TEST_PDF_PATH,
        img_format="png",
        dpi=200
    )
    print(result)

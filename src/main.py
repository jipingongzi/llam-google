from rag.doc_fetcher import export_drive_file
from rag.image_fetcher import pdf_image_pages_to_images
from rag.model_analyst_qwen import analyze_image
from dto.pdf_image_dto import pdf_image_dto
from rag.model_vector import vector, query


def extract_page_number(image_path: str) -> int:
    import re
    pattern = r'_page(\d+)\.'
    match = re.search(pattern, image_path)
    if match:
        return int(match.group(1))
    else:
        return None


if __name__ == "__main__":
    file_id = "1ZawDnCnk8q4lUVrDhxPgwcK-aW_una4nSV4_imiWsYA"
    file_path = export_drive_file(file_id=file_id)
    print(file_path)
    image_paths = pdf_image_pages_to_images(file_path)
    image_dtos = []
    print(image_paths)
    for img_path in image_paths:
        extract_page_number(img_path)
        image_dto = pdf_image_dto(file_id=file_id, page_number=extract_page_number(img_path))
        print(f"start analysis image:{img_path}")
        image_dto.analysis_result = analyze_image(img_path)
        print(f"image analysis:{image_dto}")
        image_dtos.append(image_dto)
    print("start vectorize")
    query_engine = vector(file_path=file_path, file_id=file_id, dtos=image_dtos)
    query("What is BMS?", query_engine)
    query("What is BMS problem now?", query_engine)
    query("How to fix BMS problem now?", query_engine)

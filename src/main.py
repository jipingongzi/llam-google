from dto.pdf_image_dto import pdf_image_dto
from rag.doc_folder_fetcher import export_drive_folder
from rag.image_fetcher import pdf_image_pages_to_images
from rag.model_analyst_qwen import analyze_image
from rag.model_vector import vector, query_print


def extract_page_number(image_path: str) -> int:
    import re
    pattern = r'_page(\d+)\.'
    match = re.search(pattern, image_path)
    if match:
        return int(match.group(1))
    else:
        return None


def start():
    folder_id = "17KzRpzFrZMEO-bHzOV3-4sl99UyviOnx"
    items = export_drive_folder(folder_id=folder_id)
    print(items)
    query_engine = None
    for item in items:
        file_id = item["id"]
        file_path = item["file_path"]
        file_name = item["name"]
        image_paths = pdf_image_pages_to_images(file_path)
        image_dtos = []
        print(image_paths)
        for img_path in image_paths:
            extract_page_number(img_path)
            image_dto = pdf_image_dto(file_id=file_id, page_number=extract_page_number(img_path))
            print(f"start analysis image:{img_path}")
            image_dto.analysis_result = analyze_image(img_path, file_name)
            print(f"image analysis:{image_dto}")
            image_dtos.append(image_dto)
        print("start vectorize")
        query_engine = vector(file_id, file_path, file_name, image_dtos)
    return query_engine


if __name__ == "__main__":
    my_query_engine = start()
    query_print("What is BMS?", my_query_engine)
    query_print("What is BMS problem now?", my_query_engine)
    query_print("How to fix BMS problem now?", my_query_engine)
    query_print("Tell me the deployment of BMS?", my_query_engine)
    query_print("Tell me the cloud architecture of BMS?", my_query_engine)

from doc_fetcher import export_drive_file
from image_fetcher import pdf_image_pages_to_images
from model_analyst import analyze_image

file_id = "1ZawDnCnk8q4lUVrDhxPgwcK-aW_una4nSV4_imiWsYA"
file_path = export_drive_file(file_id=file_id)
print(file_path)
images = pdf_image_pages_to_images(file_path)
print(images)
for img in images:
    print(analyze_image(img))

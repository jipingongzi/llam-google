from pathlib import Path

def get_filename_without_extension(filename):
    last_dot_index = filename.rfind('.')
    if last_dot_index != -1 and last_dot_index != len(filename) - 1:
        return filename[:last_dot_index]
    return filename


def export_drive_file(file_id, drive_service) -> str:
    save_dir = Path("./doc")
    save_dir.mkdir(parents=True, exist_ok=True)

    file_metadata = drive_service.files().get(
        fileId=file_id,
        fields="name, mimeType"
    ).execute()

    original_filename = file_metadata.get("name", f"file_{file_id}")
    base_filename = get_filename_without_extension(original_filename)
    save_path = save_dir / f"{base_filename}.pdf"
    request = drive_service.files().export_media(
        fileId=file_id,
        mimeType="application/pdf"
    )

    with open(save_path, "wb") as f:
        f.write(request.execute())
    return save_path

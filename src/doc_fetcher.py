from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build


def export_drive_file(file_id) -> str:
    try:
        save_dir = Path("./doc")
        save_dir.mkdir(parents=True, exist_ok=True)
        credentials = service_account.Credentials.from_service_account_file(
            str(Path.home() / ".credentials" / "credentials.json"),
            scopes=["https://www.googleapis.com/auth/drive.readonly"]
        )
        drive_service = build("drive", "v3", credentials=credentials)
        file_metadata = drive_service.files().get(fileId=file_id).execute()
        original_filename = file_metadata.get("name", "unknown_file")
        save_path = save_dir / f"{original_filename}.pdf"
        request = drive_service.files().export_media(
            fileId=file_id,
            mimeType="application/pdf"
        )
        with open(save_path, "wb") as f:
            response = request.execute()
            f.write(response)
        return str(save_path.resolve())
    except Exception as e:
        return str(e)


if __name__ == "__main__":
    FILE_ID = "1ZawDnCnk8q4lUVrDhxPgwcK-aW_una4nSV4_imiWsYA"
    result = export_drive_file(FILE_ID)
    print(result)

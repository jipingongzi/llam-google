from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import logging

from .doc_fetcher import export_drive_file

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

GOOGLE_MIME_TYPES = {
    "application/vnd.google-apps.document": "application/pdf",
    "application/vnd.google-apps.spreadsheet": "application/pdf",
    "application/vnd.google-apps.presentation": "application/pdf",
    "application/vnd.google-apps.drawing": "application/pdf"
}


def get_drive_service():
    creds_path = Path.home() / ".credentials" / "credentials.json"
    if not creds_path.exists():
        logger.error(f"credentials not found: {creds_path}")
        return None

    with open(creds_path, 'r') as f:
        creds_data = json.load(f)
        service_account_email = creds_data.get('client_email')
        logger.info(f"service account email: {service_account_email}")

    credentials = service_account.Credentials.from_service_account_file(
        str(creds_path),
        scopes=[
            "https://www.googleapis.com/auth/drive.readonly",
            "https://www.googleapis.com/auth/drive.metadata.readonly"
        ]
    )
    return build("drive", "v3", credentials=credentials)


def get_detailed_file_info(service, file_id):
    fields = (
        "id, name, mimeType, parents, driveId, createdTime, modifiedTime, "
        "owners(emailAddress, displayName), lastModifyingUser(emailAddress), "
        "shared, size, version, webViewLink"
    )
    return service.files().get(
        fileId=file_id,
        fields=fields,
        supportsAllDrives=True
    ).execute()


def list_folder_contents(service, folder_id) -> []:
    results = []
    folder_info = get_detailed_file_info(service, folder_id)
    logger.info(f"\n===== folder: {folder_info.get('name')} (ID: {folder_id}) =====")
    print(f"{json.dumps(folder_info, indent=2, ensure_ascii=False)}")

    page_token = None
    total_items = 0
    while True:
        response = service.files().list(
            q=f"'{folder_id}' in parents and trashed=false",
            corpora="allDrives",
            includeItemsFromAllDrives=True,
            supportsAllDrives=True,
            fields="nextPageToken, files(id, name, mimeType)",
            pageToken=page_token,
            pageSize=100
        ).execute()

        items = response.get("files", [])
        total_items += len(items)

        for item in items:
            item_id = item["id"]
            item_name = item["name"]
            item_type = item["mimeType"]

            item_info = get_detailed_file_info(service, item_id)
            print(f"{json.dumps(item_info, indent=2, ensure_ascii=False)}")

            if item_type == "application/vnd.google-apps.folder":
                logger.info(f"\n--- sub-folder: {item_name} (ID: {item_id}) ---")
                sub_results = list_folder_contents(service, item_id)
                results.extend(sub_results)
            else:
                logger.info(f"\n export: --- file: {item_name} (ID: {item_id}) ---")
                if item_type in GOOGLE_MIME_TYPES:
                    file_path = export_drive_file(item_id, service)
                    item["file_path"] = file_path
                    results.append(item)
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return results


def export_drive_folder(folder_id: str):
    drive_service = get_drive_service()
    return list_folder_contents(drive_service, folder_id)


if __name__ == "__main__":
    export_drive_folder("17KzRpzFrZMEO-bHzOV3-4sl99UyviOnx")

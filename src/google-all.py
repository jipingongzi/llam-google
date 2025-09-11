from pathlib import Path
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def get_drive_service():
    """创建并返回Google Drive服务实例"""
    try:
        creds_path = Path.home() / ".credentials" / "credentials.json"
        logger.info(f"加载凭据文件: {creds_path}")

        if not creds_path.exists():
            logger.error(f"凭据文件不存在: {creds_path}")
            return None

        # 读取服务账号邮箱
        with open(creds_path, 'r') as f:
            creds_data = json.load(f)
            service_account_email = creds_data.get('client_email')
            logger.info(f"服务账号邮箱: {service_account_email}")

        credentials = service_account.Credentials.from_service_account_file(
            str(creds_path),
            scopes=[
                "https://www.googleapis.com/auth/drive.readonly",
                "https://www.googleapis.com/auth/drive.metadata.readonly"
            ]
        )
        return build("drive", "v3", credentials=credentials)
    except Exception as e:
        logger.error(f"创建Drive服务失败: {str(e)}", exc_info=True)
        return None


def get_detailed_file_info(service, file_id):
    """获取文件或文件夹的详细信息"""
    # 指定需要获取的详细字段
    fields = (
        "id, name, mimeType, parents, driveId, createdTime, modifiedTime, "
        "owners(emailAddress, displayName), lastModifyingUser(emailAddress), "
        "shared, size, version, webViewLink"
    )

    try:
        return service.files().get(
            fileId=file_id,
            fields=fields,
            supportsAllDrives=True
        ).execute()
    except Exception as e:
        logger.error(f"获取文件 {file_id} 信息失败: {str(e)}")
        return None


def list_folder_contents(service, folder_id, indent_level=0):
    """递归列出文件夹中的所有内容（文件和子文件夹）"""
    indent = "  " * indent_level
    results = []

    try:
        # 获取当前文件夹信息
        folder_info = get_detailed_file_info(service, folder_id)
        if folder_info:
            logger.info(f"\n{indent}===== 文件夹: {folder_info.get('name')} (ID: {folder_id}) =====")
            print(f"{indent}{json.dumps(folder_info, indent=2, ensure_ascii=False)}")
        else:
            logger.info(f"\n{indent}===== 文件夹 (ID: {folder_id}) =====")

        # 列出文件夹中的所有项目
        page_token = None
        total_items = 0

        while True:
            response = service.files().list(
                q=f"'{folder_id}' in parents and trashed=false",
                corpora="allDrives",
                includeItemsFromAllDrives=True,
                supportsAllDrives=True,
                fields="nextPageToken, files(id, name, mimeType)",  # 先获取基本信息
                pageToken=page_token,
                pageSize=100
            ).execute()

            items = response.get("files", [])
            total_items += len(items)

            for item in items:
                item_id = item["id"]
                item_name = item["name"]
                item_type = item["mimeType"]

                # 获取项目详细信息
                item_info = get_detailed_file_info(service, item_id)

                if item_type == "application/vnd.google-apps.folder":
                    logger.info(f"\n{indent}--- 子文件夹: {item_name} (ID: {item_id}) ---")
                    if item_info:
                        print(f"{indent}{json.dumps(item_info, indent=2, ensure_ascii=False)}")
                    # 递归列出子文件夹内容
                    sub_results = list_folder_contents(service, item_id, indent_level + 1)
                    results.extend(sub_results)
                else:
                    logger.info(f"\n{indent}--- 文件: {item_name} (ID: {item_id}) ---")
                    if item_info:
                        print(f"{indent}{json.dumps(item_info, indent=2, ensure_ascii=False)}")
                    results.append(item_info)

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        logger.info(
            f"\n{indent}===== 文件夹 {folder_info.get('name') if folder_info else folder_id} 共包含 {total_items} 个项目 =====")

    except Exception as e:
        error_msg = f"{indent}处理文件夹 {folder_id} 时出错: {str(e)}"
        logger.error(error_msg)
        results.append({"error": error_msg})

    return results


def main():
    # 要查询的文件夹ID
    TARGET_FOLDER_ID = "17KzRpzFrZMEO-bHzOV3-4sl99UyviOnx"  # 替换为实际的folderId

    if TARGET_FOLDER_ID == "请替换为你的文件夹ID":
        logger.error("请先将TARGET_FOLDER_ID替换为实际的文件夹ID")
        return

    # 创建服务
    drive_service = get_drive_service()
    if not drive_service:
        return

    # 列出文件夹内容
    logger.info(f"开始列出文件夹 {TARGET_FOLDER_ID} 中的所有内容...")
    list_folder_contents(drive_service, TARGET_FOLDER_ID)


if __name__ == "__main__":
    main()

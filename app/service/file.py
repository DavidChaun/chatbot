import os
from typing import Optional
from botocore.exceptions import ClientError

from app import (
    s3_client,
    S3_FILE_PATH_BASE,
    S3_BUCKET_NAME,
    LOCAL_TEMP_FILE_PATH_BASE,
)
from app.logging_ import logger
from app.utils import Timer


def upload(content: bytes, path: str) -> tuple[str, str]:
    """
    上传文件至S3
    :param content: 文件内容
    :param path: 相对于 LOCAL_TEMP_FILE_PATH_BASE 的路径
    :return: 本地文件路径 & s3路径
    """
    with Timer(desc=f"Uploading {path} cost: "):
        local_path = f"{LOCAL_TEMP_FILE_PATH_BASE}/{path}"
        if not os.path.exists(local_path):
            # 创建文件夹
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            with open(local_path, "wb") as f:
                f.write(content)

        s3_path = f"{S3_FILE_PATH_BASE}/{path}"
        s3_client.upload_file(local_path, S3_BUCKET_NAME, s3_path)

        return local_path, s3_path


def fullpath_upload(local_path: str, s3_path: str) -> bool:
    """
    上传文件至S3
    :param local_path: 本地路径
    :param s3_path: s3路径
    :return: 是否上传成功
    """
    with Timer(desc=f"Uploading local {local_path} cost: "):
        s3_client.upload_file(local_path, S3_BUCKET_NAME, s3_path)

        return True


def get_local_file(path: str) -> str:
    """
    获取本地文件路径，如果本地不存在，则从 s3 上下载
    :param path: 相对于 LOCAL_TEMP_FILE_PATH_BASE 的路径
    :return: 本地文件路径
    """

    local_path = f"{LOCAL_TEMP_FILE_PATH_BASE}/{path}"

    # 因为都是基于S3_FILE_PATH_BASE前缀，因此需要先转换一道
    path = f"{S3_FILE_PATH_BASE}/{path}"

    metadata = _head_object(path)
    if not metadata:
        raise FileNotFoundError(f"Path {path} not found in remote destination.")

    # 本地文件存在，且跟远端文件一致，则直接返回
    if (
        os.path.exists(local_path)
        and os.path.getmtime(local_path) == metadata["LastModified"].timestamp()
    ):
        return local_path

    # 当确认远端文件存在时才 mkdir，避免污染本地的文件系统
    if not os.path.exists(os.path.dirname(local_path)):
        os.makedirs(os.path.dirname(local_path))

    with Timer(desc=f"downloading {path} cost -> "):
        s3_client.download_file(S3_BUCKET_NAME, path, local_path)

        # 下载完之后更新本地的文件的时间戳，方便对比
        mod_time = metadata["LastModified"].timestamp()
        os.utime(local_path, (mod_time, mod_time))

    return local_path


def _head_object(path: str) -> Optional[dict]:
    """
    获取 s3 文件的 metadata
    """
    try:
        return s3_client.head_object(
            Bucket=S3_BUCKET_NAME,
            Key=path,
        )
    except ClientError as e:
        if int(e.response["Error"]["Code"]) == 404:
            return None

        raise e


def delete_remote_file(path: str):
    """
    删除文件
    """

    local_path = f"{LOCAL_TEMP_FILE_PATH_BASE}/{path}"
    if os.path.exists(local_path):
        # 删除文件
        os.remove(local_path)

    # 因为都是基于S3_FILE_PATH_BASE前缀，因此需要先转换一道
    path = f"{S3_FILE_PATH_BASE}/{path}"

    try:
        # 尝试删除文件
        s3_client.delete_object(Bucket=S3_BUCKET_NAME, Key=path)
    except ClientError as e:
        # 捕获S3客户端错误
        error_code = e.response["Error"]["Code"]
        if error_code == "NoSuchKey":
            logger.warn(f"File {path} does not exist in {S3_BUCKET_NAME}")
        else:
            logger.warn(f"An error occurred: {e}")

import os
import boto3
from contextvars import ContextVar
from dotenv import load_dotenv

from app.utils import file_relative_path

load_dotenv()

APP_NAME = "chatbot"
REQUEST_ID_CONTEXT = ContextVar("trace_id", default="N/A")

CHAT_CALLBACK_URL = os.getenv("CHAT_CALLBACK_URL", "http://localhost:3000")

# files storage
LOCAL_TEMP_FILE_PATH_BASE = os.getenv(
    "LOCAL_TEMP_FILE_PATH_BASE", file_relative_path(__file__, "../tmp")
)
S3_FILE_PATH_BASE = os.getenv("S3_FILE_PATH_BASE", "")
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "")
S3_ENDPOINT_DOMAIN = os.getenv("S3_ENDPOINT_DOMAIN", "")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID", "")
S3_SECRET_ACCESS_KEY = os.getenv("S3_ACCESS_KEY_SECRET", "")
S3_USE_SSL = os.getenv("S3_USE_SSL", "false").lower() == "true"
s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    use_ssl=S3_USE_SSL,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
    region_name="us-east-1",
    config=boto3.session.Config(s3={"addressing_style": "path"}),
)

ZHIPUAI_API_KEY = os.getenv("ZHIPUAI_API_KEY", "")
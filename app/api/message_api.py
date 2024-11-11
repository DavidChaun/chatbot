import io
import shortuuid
import requests
from typing import Tuple
from bs4 import BeautifulSoup
from datetime import datetime
from fastapi import APIRouter, Depends, File, Path, UploadFile, Form, BackgroundTasks
from PIL import Image

from app.core import message_receive_queue, message_reply_queue
from app.database import save_entity
from app.model import message as msg_storage
from app.model.message import Message, MessageExtra
from app.logging_ import logger
from app.utils import datetime_string, get_file_extension, file_relative_path
from app.service import file as file_service

router = APIRouter()


pic_content_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
video_content_types = ["video/mp4", "video/quicktime", "video/x-msvideo"]
audio_content_types = ["audio/mp3", "audio/ogg", "audio/wav"]
file_content_types = [
    "application/pdf",
]


@router.post(
    "/messages",
    dependencies=[],
    tags=["Messages"],
    status_code=204,
)
def receive_msg(
    from_username: str = Form(description="from_username"),
    to_username: str = Form(description="to_username", default="bot"),
    session_id: str = Form(description="session_id"),
    is_group: bool = Form(description="是否为群组消息", default=False),
    type_: str = Form(alias="type"),
    content: str = Form(default=None),
    uploaded_file: UploadFile = File(default=None),
) -> None:
    """
    接收来自wechat的消息
    """
    messaged, reply_message = _decorate_message(
        type_, content, from_username, to_username, session_id, is_group
    )
    if reply_message:
        message_reply_queue.send(session_id, reply_message.id)
        return

    content_meta = None
    content_bytes = b""
    if uploaded_file:
        file_content_type = uploaded_file.content_type
        file_size = uploaded_file.size
        file_name = uploaded_file.filename
        # relate_path = f"{type_}/{session_id}/{datetime_string()}_{shortuuid.uuid()}{get_file_extension(file_name)}"
        # local_path, s3_path = file_service.upload(uploaded_file.file.read(), relate_path)
        content_meta = {
            "type": type_,
            "content_type": file_content_type,
            "size": file_size,
            "file_name": file_name,
            # "relate_path": relate_path,
            # "local_path": local_path,
            # "s3_path": s3_path,
        }
    # content包含链接??
    if type_ == "pic":
        # resize
        pixels = (512, 512)
        img = Image.open(uploaded_file.file)
        content_meta["resize_pixels"] = f"{pixels[0]}*{pixels[1]}"
        content_meta["real_pixels"] = f"{img.width}*{img.height}"
        bio = io.BytesIO()
        img.resize(pixels).save(bio, format="JPEG")
        content_bytes = bio.getvalue()
        bio.close()
    if type_ == "link":
        content_meta = {"link": content}
        # scratch text data
        response = requests.get(content)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, "html.parser")
            text = soup.get_text(separator="\n", strip=True)
            logger.info(f"scratch from url: {content}, data: {text}")
            content_bytes = text.encode("UTF-8")

    if content_meta and content_bytes:
        msg_extra = MessageExtra(
            message_id=messaged.id,
            content_meta=content_meta,
            content_bytes=content_bytes,
        )
        save_entity(msg_extra)

    message_receive_queue.send(session_id, messaged.id, delay={"pic": 15}.get(type_, 3))


def _decorate_message(
    type_, content, from_username, to_username, session_id, is_group
) -> Tuple[Message, "ReplyMessage"]:
    is_clear = False
    reply_msg = None

    if type_ == "text":
        type_ = "link" if content.startswith(("http://", "https://")) else type_
    if content == "remake":
        # 清除记忆
        type_ = "func"
        is_clear = True
        msg_storage.clear_messages(session_id)
        reply_msg = Message(
            type_=type_,
            content="done",
            from_=to_username,
            to=from_username,
            session_id=session_id,
            is_group=is_group,
            is_clear=is_clear,
            created_at=datetime.now(),
        )

    msg = Message(
        type_=type_,
        content=content,
        from_=from_username,
        to=to_username,
        session_id=session_id,
        is_group=is_group,
        is_clear=is_clear,
        created_at=datetime.now(),
    )

    save_entity(msg)
    if reply_msg:
        save_entity(reply_msg)

    return msg, reply_msg

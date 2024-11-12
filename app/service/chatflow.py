import requests

from base64 import b64encode
from datetime import datetime
from typing import List

from app.core import message_reply_queue
from app.logging_ import logger
from app.model import completion as completion_storage
from app.model import message as msg_storage
from app.database import save_entity, get_db
from app.model.message import Message
from app.service.net_search import web_search_pro, ai_consider
from app.service.llm import chat_completions, LlmMessage, SYSTEM_ROLE, USER_ROLE
from app.utils import (
    file_relative_path,
    current_timestamp,
    DATE_TIME_PATTERN,
)


with open(file_relative_path(__file__, "../prompts/system_prompt.txt"), "r") as file:
    system_prompt = file.read()

with open(
    file_relative_path(__file__, "../prompts/histories_compress_prompt.txt"), "r"
) as file:
    histories_compress_prompt = file.read()

with open(
    file_relative_path(__file__, "../prompts/question_rewrite_prompt.txt"), "r"
) as file:
    question_rewrite_prompt = file.read()

with open(
    file_relative_path(__file__, "../prompts/net_search_prompt.txt"), "r"
) as file:
    net_search_prompt = file.read()

with open(
    file_relative_path(__file__, "../prompts/net_search_context_prompt.txt"), "r"
) as file:
    net_search_context_prompt = file.read()

with open(file_relative_path(__file__, "../prompts/keyword_prompt.txt"), "r") as file:
    keyword_prompt = file.read()

with open(
    file_relative_path(__file__, "../prompts/pic_default_prompt.txt"), "r"
) as file:
    pic_default_prompt = file.read()

with open(
    file_relative_path(__file__, "../prompts/link_default_prompt.txt"), "r"
) as file:
    link_default_prompt = file.read()


def chat(message_ids: List[str]):
    """
    设定规则：
    包含session id一小时以前的context；
    链接信息只提取文字，不包括图片，因此效果不会好；
    图片、链接在队列里时，已经解析完整；
    * 多模态的消息列表，不会进行搜索

    列举情况：
    【1条消息，图片|链接|视频】：填充默认的user prompt；
    【n条消息，文字型】：判断llm是否需要搜索引擎获取答案；如需，搜索答案放入context；
    【n条消息，文字+图片】：拼接好上下文，并塞入图片调用llm；
    【n条消息，文字+链接】：链接解析获取内容，拼接好上下文；
    【n条消息，文字+视频】：暂不支持；

    """
    db = next(get_db())
    messages = msg_storage.list_messages(db, message_ids)
    session_id = messages[0].session_id

    # 历史记录跳过图片，只回忆30分钟前的
    histories = msg_storage.list_previous_messages(
        session_id,
        datetime.fromtimestamp((current_timestamp() - 30 * 60 * 1000) / 1000),
    )
    previous = [h for h in histories if h.type_ == "text" and h.id not in message_ids]
    histories_content = "\n".join(
        [
            f"#{p.created_at.strftime(DATE_TIME_PATTERN)} #{p.from_} #{p.content}"
            for p in previous
        ]
    )
    # 字数太多影响发挥，压缩一下
    if len(histories_content) > 300:
        histories_content = ai_consider(
            histories_compress_prompt.format(
                user=messages[0].from_,
                histories="\n".join(
                    [
                        f"#{p.created_at.strftime(DATE_TIME_PATTERN)} #{p.from_} #{p.content}"
                        for p in previous
                    ]
                ),
            )
        )

    llm_messages = [
        LlmMessage(
            role=SYSTEM_ROLE, content=system_prompt.format(histories=histories_content)
        )
    ]

    is_text_type = all([m.type_ == "text" for m in messages])
    if is_text_type:
        question = "\n".join([m.content for m in messages])
        # 结合历史问题重写
        question_rewrite = ai_consider(question_rewrite_prompt.format(histories=histories_content, content=question))
        logger.info(f"【{messages[0].from_}】question rewrite：{question}")

        is_net_search = ai_consider(net_search_prompt.format(content=question_rewrite))
        logger.info(f"【{messages[0].from_}】：{question}")
        logger.info(f"【{messages[0].from_}】问题是否搜索：{is_net_search}")

        if is_net_search == "是":
            intent, search_contexts, links = web_search_pro(question)
            logger.info(f"【{messages[0].from_}】搜索意图：{intent}")
            # todo 保存一下相关意图和问题，方便调整
            # 意图识别，可以直接返回微信的内置tag链接

            # 发一个过去让客户知道关联的链接
            link_content = '\n'.join(links[0:2])
            _build_and_send_reply_msg(f"挑了些链接。\n{link_content}", messages[0].to, messages[0].from_, session_id)

            llm_messages.append(
                LlmMessage(
                    role=USER_ROLE,
                    content=net_search_context_prompt.format(
                        net_content="\n".join(search_contexts[0:10]), question=question_rewrite
                    ),
                )
            )
        else:
            llm_messages.append(LlmMessage(role=USER_ROLE, content=question))

    else:
        question = "\n".join([m.content for m in messages if m.type_ == "text"])
        # todo voice
        links = [m for m in messages if m.type_ == "link"]
        pics = [m for m in messages if m.type_ == "pic"]

        content = question
        if links:
            # todo 因为没有链接总结，因此准确率很低
            net_content = ""
            for index, l in enumerate(links, start=1):
                net_content += (
                    f"{index}. {str(l.message_extra.content_bytes, encoding='UTF-8')}"
                )
            content = net_search_context_prompt.format(
                net_content=net_content, question=question
            )
        if pics:
            pic_contents = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{b64encode(p.message_extra.content_bytes).decode('UTF-8')}"
                    },
                }
                for p in pics
            ]
            content = [{"type": "text", "text": content or pic_default_prompt}] + pic_contents
        llm_messages.append(LlmMessage(role=USER_ROLE, content=content))

    # 汇总信息，获取最终llm信息
    begin_at = datetime.now()
    llm_result = chat_completions(llm_messages, "gpt-4o", temperature=0.1)
    db_completion = completion_storage.save_llm_result(
        [m.model_dump() for m in llm_messages], llm_result, begin_at, messages[0].from_
    )
    _build_and_send_reply_msg(db_completion.result, messages[0].to, messages[0].from_, session_id)


def _build_and_send_reply_msg(content, from_, to, session_id):
    reply_msg = Message(
        type_="text",
        content=content,
        from_=from_,
        to=to,
        session_id=session_id,
        created_at=datetime.now(),
    )
    save_entity(reply_msg)
    message_reply_queue.send(session_id, reply_msg.id)


def reply(message_id: str):
    db = next(get_db())
    message = msg_storage.list_messages(db, message_id)[0]

    resp = requests.post(
        "http://127.0.0.1:8080/callback",
        params={
            "session_id": message.session_id,
            "msg": message.content,
        },
    )
    logger.info(
        f"send to wechat. response state: {resp.status_code}, text: {resp.text}"
    )

from app.service import file
from app.utils import file_relative_path


def test_upload_file():
    file.fullpath_upload(file_relative_path(__file__, "../resources/test_upload.webp"), "pics/test_upload.webp")


def test_ddgs_chat():
    from duckduckgo_search import DDGS

    with DDGS() as ddgs:
        print(ddgs.chat("你是一名数据挖掘者，你擅长从长文本里获取到适用于搜索引擎的关键词。\n请阅读以下文本，获取关键词列表。\n'''\njellycat最近的营销手段是不是有病\n'''\n\n只需要输出关键词列表，不要输出无关的内容，使用空格分开输出。", model="gpt-4o-mini"))


def test_resize():
    from PIL import Image

    # 打开图像文件
    img = Image.open(file_relative_path(__file__, "../resources/test_upload.webp"))
    # img = Image.open("/Users/weijueye/Downloads/WechatIMG219.jpg")
    # 调整大小为 512x512
    img_resized = img.resize((512, 512))
    # 保存调整后的图片
    print(len(img_resized.tobytes()))
    img_resized.save(file_relative_path(__file__, "../resources/test_upload_resize.webp"))


def test_is_http():
    s = "htt://www.gamersky.com/news/202409/1812213.shtml"
    is_http = s.startswith(("http://", "https://"))
    print(is_http)


def test_llm():
    from app.service.llm import chat_completions, LlmMessage

    result = chat_completions([
        LlmMessage(**{
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": "请翻译文本为英文，用json返回。json key为translation。翻译文本为：“你好”"
                }
            ]
        })
    ])
    print(result.model_dump())


def test_zhipu_web_search():
    from app.service.net_search import web_search_pro

    dict_ = web_search_pro("杨度外传")
    print(dict_)

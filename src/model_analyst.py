import torch
from transformers import pipeline
from PIL import Image
from pathlib import Path


def analyze_image(image_path):

    try:
        # 验证图片路径
        image_path = Path(image_path)
        if not image_path.exists():
            return f"错误：找不到图片文件: {image_path}"

        pipe = pipeline(
            task="image-text-to-text",
            model = "deepseek-community/deepseek-vl-1.3b-chat",
            # model="Qwen/Qwen2.5-VL-7B-Instruct",
            device=0 if torch.cuda.is_available() else -1,
            dtype=torch.float16 if torch.cuda.is_available() else torch.float32
        )

        # 打开并处理图片
        try:
            code_image = Image.open(image_path).convert("RGB")
        except Exception as e:
            return f"错误：无法打开图片文件: {str(e)}"

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image", "image": code_image},
                    {"type": "text", "text": "请分析这张图片并详细描述其中的内容。"
                                             "请先判断图片类型，包括但不限于：代码示例，流程图，架构图，"
                                             "然后根据图片类型给出详细描述，"
                                             "如果是架构图详细描述各个组件的功能和操作人员和接入方式，"
                                             "如果是代码图详细描述逻辑与输入输出，异常情况，"
                                             "如果是流程图详细描述各个节点的作用与输入输出。"
                     }
                ]
            }
        ]
        result = pipe(
            text=messages,
            max_new_tokens=1000,
            return_full_text=False
        )

        return result[0]["generated_text"]

    except Exception as e:
        return f"分析失败：{str(e)}"


# 测试示例
if __name__ == "__main__":
    test_image_path = "bms image.png"
    print(analyze_image(test_image_path))

import torch
from transformers import pipeline
from PIL import Image
from pathlib import Path


def analyze_image_mock(image_path):
    return ("This image is a design document for a Booking Management System, which presents the overall architecture, components, and technology selection of the system from three aspects: system context, high-level description, and key design decisions. "
            "It clearly presents the core information of the system. The System Context section presents the interaction relationship between the system and various roles and modules, both external and internal, in the form of a framework. "
            "External Interaction: It interfaces with External Hotel Booking Systems and External Transport Booking Systems to automatically search for and book hotels and transportation services; "
            "Hotel suppliers can manually update available booking information, while transportation suppliers can manually update prices. "
            "Internal roles and modules: Cost Tracking Center: receives hotel and transport requirements and is able to review and update business trip costs; Employees: can review and accept bookings, interact with the Employees Portal; "
            "Travel Department: Responsible for managing hotel and transportation bookings, receiving alerts and notifications, maintaining configuration and rules, generating reports, and interacting with the Administration Portal; "
            "IT Support: Provide IT Support services and interact with the Admin and Support modules; The core modules of the system include the Employees Portal, Administration Portal, Suppliers Portal, and Admin and Support modules, "
            "which together form the booking management system and handle various booking related business logic and interactions. "
            "This section describes the composition of the system and explains that the solution includes the following key components: "
            "BMS Core Service: a microservices based backend (such as using Node.js or Spring Boot technology) responsible for search, prioritization, approval, and change management functions; "
            "Employees Portal: An intuitive user interface for employees to view reservations, confirm information, and provide feedback; Administration Portal: Used for configuration, reporting, and manual override operations; "
            "Integration Layer: It interfaces with CTC through APIs to obtain requirement updates, tracks with UPSA, uses SSO for identity authentication, and also interfaces with Uber to handle transportation services. "
            "Meanwhile, use scalable databases such as PostgreSQL for data storage to ensure system configurability and performance. "
            "The Key Design Decisions section presents the design decisions related to the Tech Stack in a table format: Background: the need for modern and scalable web technologies; Options: Choose between React and Angular for front-end technology, and between Node.js and Java for back-end technology; "
            "Pros/Cons: React: lightweight and fast; Angular: More structured; Node.js: Fast development; Final Decision: React is used for the front-end, and Node.js is used for the back-end; "
            "Date/Considerations: Determined on August 20, 2025, taking into account cost-effectiveness and the need for rapid iteration.")

def analyze_image(image_path):
    try:
        image_path = Path(image_path)

        pipe = pipeline(
            task="image-text-to-text",
            model="deepseek-community/deepseek-vl-1.3b-chat",
            # model="Qwen/Qwen2.5-VL-7B-Instruct",
            device=0,
            dtype=torch.float16
        )
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
    test_image_path = '/doc/pic/TDD EPAM BMS system_page6.jpeg'
    print(analyze_image(test_image_path))

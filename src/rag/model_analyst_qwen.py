import base64
import os

import openai

MODEL = "Qwen/Qwen2.5-Omni-7B"
DEPLOYMENT_LINK = "https://qwen2-vl-api.llm.lab.epam.com"


def process_path(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def analyze_image(url_or_path, file_name) -> str:
    # if it's a local file, base64 encode it
    if os.path.exists(url_or_path):
        url_or_path = process_path(url_or_path)
    base_url = f"{DEPLOYMENT_LINK}/v1"
    print(base_url)
    client = openai.Client(api_key="EMPTY", base_url=base_url)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a software architect"},
            {
                "role": "user",
                "content": [
                    {"type": "text",
                     "text": "Describe this image of file <" + file_name + ">, "
                             "please focus on describing the content of the drawing section, "
                             "which mainly includes software development related flowcharts, mind maps, "
                             "system architecture diagrams, deployment diagrams, sequence diagrams, etc. "
                             "Please provide a detailed description of the overall architecture and details."
                     },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": url_or_path
                        },
                    },
                ],
            },
        ],
        temperature=0,
        max_tokens=1000,
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    # to use with URL please change it to an existing URL
    # to use with a local file (checks if the file exists, if does, base64 encode it
    # url_or_path = "https://img-s-msn-com.akamaized.net/tenant/amp/entityid/AA1MbekQ.img"
    path = "/TDD EPAM BMS system_page6.jpeg"
    analyze_image(url_or_path=path)

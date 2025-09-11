import base64
import os

import openai
import requests

MODEL = "Qwen/Qwen2.5-Omni-7B"
DEPLOYMENT_LINK = "https://qwen2-vl-api.llm.lab.epam.com"


def construct_prompt(question):
    # please change this however you like. this is just an example. we need the <image> tag for model
    prompt = (f"A chat between a curious user and an artificial intelligence assistant. "
              f"The assistant gives helpful, detailed, and polite answers to the user's questions."
              f" USER: <image> {question}"
              f" ASSISTANT:")
    return prompt


def example_llava_request():
    # can use paths (not for deployed models since we don't provide access to filesystem, may implement on app level)
    path = "https://images.unsplash.com/photo-1608848461950-0fe51dfc41cb?q=80&w=3087&auto=format&fit=crop&ixlib=rb-4.0.3&ixid=M3wxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8fA%3D%3D"
    # can use links
    question = "what is this?"
    data = {
        "text": construct_prompt(question),
        "image_data": path,
        # for sampling params
        # https://github.com/sgl-project/sglang/blob/main/python/sglang/srt/sampling_params.py
        "sampling_params": {"max_new_tokens": 100,
                            "temperature": 1.0,
                            "top_p": 1.0,
                            "top_k": -1,
                            "frequency_penalty": 0.0,
                            "presence_penalty": 0.0,
                            }
    }
    headers = {'Content-Type': 'application/json'}
    response = requests.post(f'{DEPLOYMENT_LINK}/generate', json=data, headers=headers)
    print(response.json())


def process_path(image_path):
    with open(image_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"


def example_llava_openai_request(url_or_path):
    # if it's a local file, base64 encode it
    if os.path.exists(url_or_path):
        url_or_path = process_path(url_or_path)
    # mostly from sglang test page
    base_url = f"{DEPLOYMENT_LINK}/v1"
    print(base_url)
    client = openai.Client(api_key="EMPTY", base_url=base_url)
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant"},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Describe this image"},
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
    print(response.choices[0].message.content)


if __name__ == "__main__":
    # to use with URL please change it to an existing URL
    # to use with a local file (checks if the file exists, if does, base64 encode it
    # url_or_path = "https://img-s-msn-com.akamaized.net/tenant/amp/entityid/AA1MbekQ.img"
    url_or_path = "C://Users//Sean_Xiao//github-data//llam-google//TDD EPAM BMS system_page6.jpeg"
    example_llava_openai_request(url_or_path=url_or_path)

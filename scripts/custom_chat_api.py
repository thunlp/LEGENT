"""
Custom Chat API

By default, the toolkit always uses OpenAI's GPT-4 API for generating responses.
This script demonstrates the customization of the ChatAPI class to use other APIs.
For example, deploying a custom model or using a different API such as Gemini, Claude, Qwen, GLM.
By using @chat_api decorator, all LLM calls within the package can be routed through this custom implementation.

To interact with agent with the custom chat API, you can use the following command:
    python scripts/custom_chat_api.py
    legent launch --scene 0
And then you can chat with the agent.
"""

from legent.server.chat_server import serve_main
from legent.dataset.task import ChatAPI, chat_api
from openai import OpenAI


@chat_api()
class CustomChatAPI(ChatAPI):
    def __init__(self, api_key, base_url):
        # An example of using GLM for Chinese users
        self.client = OpenAI(api_key="Get an API key from https://open.bigmodel.cn/usercenter/apikeys", base_url="https://open.bigmodel.cn/api/paas/v4/")

    def send_chat(self, messages):
        response = self.client.chat.completions.create(
            model="glm-4",
            messages=messages,
            max_tokens=None,
            n=1,
            stop=None,
            temperature=0.7,
        )
        ret = response.choices[0].message.content
        return ret


serve_main()

# GPT calling
import os
import json
import openai
from retrying import retry

openai.api_base = ''
openai.api_key = ""

@retry(stop_max_attempt_number=5, wait_fixed=2000)  # 重试3次，每次间隔2秒
def call_gpt_3_5(user_content, sys_content):
    print("call gpt 3.5.", end=" ")
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content}
        ],
    )
    result = response.choices[0].message.content
    token_usage = response.usage
    return result, token_usage

@retry(stop_max_attempt_number=3, wait_fixed=2000)  # 重试3次，每次间隔2秒
def call_gpt_4(user_content, sys_content=""):
    print("call gpt 4.",end=" ")
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content}
        ],
    )
    # print("gpt4 response: ", response)
    result = response.choices[0].message.content
    token_usage = response.usage
    return result, token_usage


def call_gpt_4_1106(user_content, sys_content):
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": sys_content},
            {"role": "user", "content": user_content}
        ],
    )
    
    result = response.choices[0].message.content
    token_usage = response.usage

    return result, token_usage


if __name__ == "__main__":
    user_content = "Please generate 5 natural language queries based on the action list."
    sys_content = "You are a helpful assistant that generates queries."
    
    # Example action list for testing
    action_list = {"action_list": ["mark pie", "aggregate count"]}
    input_str = user_content + str(action_list)
    
    # Call GPT-3.5
    result_3_5, token_usage_3_5 = call_gpt_3_5(input_str, sys_content)
    print("GPT-3.5 Result:", result_3_5)
    
    # Call GPT-4
    result_4, token_usage_4 = call_gpt_4(input_str, sys_content)
    print("GPT-4 Result:", result_4)

import json
import openai
from openpyxl import Workbook , load_workbook
from tqdm import tqdm
import pandas as pd
import sys
import re
def generatePrompt(receptacle,objectName):
    prompt="\
    You are an AI assistant, and your task is is to determine whether a specific object can be placed on top of or inside a specific receptacle.\
    The user will give you a specific receptacle and some objects.You should assign a weight rw ∈ {0, 1, 2} corresponding to the likelihood of object being placed on the receptacle, where 0 indicates that in daily life the object is unlikely to be placed on the receptacle, with the lowest probability; while 2 indicates that the object is highly likely to be placed on the receptacle; while 1 indicates that the probability that this object is placed in this receptacle is between the two.\
    You should try to provide the correct answer based on your common sense knowledge and reasoning.\
    For example, if a user provides (receptacle: playground, object: basketball,football,desk,bed,book),based on common sense knowledge, it is known that a basketball and a football is highly likely to be placed on a playground,but desk、book is not very likely but can also be placed on a playground,and the bed is very unlikely to be placed on a playground,so the agent outputs {\"basketball\":2,\"football\":2,\"desk\":1,\"bed\":0,\"book\":1}.\
    If a user provides (receptacle: desk, object: playground,football,desk,water,bowl),based on common sense knowledge, it is known that a bowl is highly likely to be placed on a desk so marked as 2.Football can be placed on the table, but not often, so it is marked as 1. Water flows and cannot be placed alone on the table, so it is marked as 0. The playground is too big to be placed on the desk, so it is marked as 0. The desk cannot be placed on itself, marked as 0.,so the agent outputs {\"playground\":0,\"football\":1,\"desk\":0,\"water\":0,\"bowl\":2}\
    The specific annotation metrics and requirements are as follows:\n\
    usr:(receptacle: apple, object: bowl,pear,water,desk,book)\n\
    agent:{\"bowl\":0,\"pear\":0,\"water\":0,\"desk\":0,\"book\":0}\n\
    usr:(receptacle: desk, object: book,pear,television,cup,bottle)\n\
    agent:{\"book\":2,\"pear\":1,\"television\":1,\"cup\":1,\"bottle\":1}\n\
    usr:(receptacle: "
    prompt=f"{prompt}{receptacle}, object: {objectName[0]}"
    for i in range(len(objectName)-1):
        prompt=f"{prompt},{objectName[i+1]}"
    prompt=f"{prompt}\n agent:"
    return prompt

if len(sys.argv) > 2:
    arg1 = sys.argv[1]
    arg2 = sys.argv[2]
    print("Input file about object is a receptacle or not:", arg1)
    print("Output file about co-occurrence relationships in json format:", arg2)
    input_file=arg1
    json_file_path=arg2
    items_list=[]
    receptacle_list=[]
    error_items=[]
    data=pd.read_excel(input_file)
    for index,row in data.iterrows():
        if(row['isReceptacle']):
            receptacle_list.append(row['Object'])
        else:
            items_list.append(row['Object'])

    api_key = 'sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404'
    base_url = 'https://yeysai.com/v1'
    unlabeled_objects=items_list
    all_result={}
    receptacle_list=receptacle_list
    for i in tqdm(range(len(receptacle_list))):
        receptacle=receptacle_list[i]
        dict_result={}
        j=0
        while j < len(unlabeled_objects): 
            if(j+5<=len(unlabeled_objects)):
                objectType=unlabeled_objects[j:j+5]
            else:
                objectType=unlabeled_objects[j:]
            j+=5

            client = openai.OpenAI(api_key=api_key, base_url=base_url)
            messages = [
                {"role": "user", "content": generatePrompt(receptacle=receptacle,objectName=objectType)}
            ]
            # print(messages)
            response = client.chat.completions.create(
                model='gpt-4', # 'gpt-3.5-turbo', 'gpt-4', 'gpt-3.5-turbo-16k', 'gpt-4-32k'
                messages=messages
            )
            # print(response.choices[0].message.content)
            result=response.choices[0].message.content
            try:
                result = re.search(r'\{.*\}', result, re.DOTALL).group(0)
                result = json.loads(result)
                dict_result.update(result)
            except json.JSONDecodeError as e:
                print(f"JSON 解码异常: {e}")
                error_items.append(objectType)
                continue
        if(receptacle in all_result.keys()):
            all_result[receptacle].update(dict_result)
        else:
            all_result[receptacle]=dict_result

        with open(json_file_path, "w") as json_file:
            json.dump(all_result, json_file)
    if len(error_items)>0 and error_items is not None:
        with open('error_relation.txt', 'w') as f:
            for sublist in error_items:
                line = ' '.join(str(x) for x in sublist)
                f.write(f"{line}\n")

API_KEY = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
import openai

base_url = "https://yeysai.com/v1"
client = openai.OpenAI(api_key=API_KEY, base_url=base_url)
# messages = [{"role": "user", "content": "你好，你是谁？"}]

prompt = """
你是一个AI助手，你需要根据你的常识信息，对一些物体进行标注，主要涉及到物体在室内环境中如何摆放的问题，你的输出要使用json格式。
对每个物体，你需要标注如下几个字段：
1. 房间类型
inKitchens: 物体是否可以放在厨房中
inLivingRooms: 物体是否可以放在客厅中
inBedrooms: 物体是否可以放在卧室中
inBathrooms: 物体是否可以放在卫生间中
对上述字段，你需要从[0,1]中给出一个值，0代表不可以出现在这种房间类型，1代表可以出现。
以inKitchens为例，basketball，desk从不会出现在厨房中，所以inKitchens的值为0；egg，knife会出现在厨房中，所以inKitchens的值为1。
2. 放置位置
onFloors: 物体是否可以放在地面上
对上述字段，你需要从[0,1]中给出一个值，0代表不可以放在地面上，1代表可以放在地面上。
比如，egg，knife这些物体（小工具，食物等）不可以放在地面上，所以onFloors的值为0；table，desk，fridge这些大物体（家具，机器等）可以放在地面上，所以onFloors的值为1。
下面我会给你几个例子，你需要严格遵循这些例子的格式，去给一个物体进行标注，并输出一个单行的json格式的结果（只要json文本，不要输出任何涉及渲染的代码块的信息，比如```json等）。
例子1：
[物体]
basketball
[标注]
{"inKitchens": 0, "inLivingRooms": 1, "inBedrooms": 1, "inBathrooms": 0, "onFloor": 1}
例子2：
[物体]
apple
[标注]
{"inKitchens": 1, "inLivingRooms": 1, "inBedrooms": 1, "inBathrooms": 0, "onFloor": 0}
例子3：
[物体]
spoon
[标注]
{"inKitchens": 1, "inLivingRooms": 1, "inBedrooms": 1, "inBathrooms": 0, "onFloor": 0}
例子4：
[物体]
clothesdryer
[标注]
{"inKitchens": 0, "inLivingRooms": 1, "inBedrooms": 1, "inBathrooms": 1, "onFloor": 1}
例子5：
[物体]
scrubbrush
[标注]
{"inKitchens": 0, "inLivingRooms": 0, "inBedrooms": 0, "inBathrooms": 1, "onFloor": 0}
例子6：
[物体]
seasoning_jar
[标注]
{"inKitchens": 1, "inLivingRooms": 0, "inBedrooms": 0, "inBathrooms": 0, "onFloor": 0}
例子结束，现在请你给一个物体进行标注：
[物体]
---object---
[标注]
"""

import json

with open(
    r"D:\code\LEGENT\LEGENT\legent\scene_generation\data_annotation\new_data\categories.json",
    "r",
) as f:
    categories = json.load(f)

res = {}
with open("annotation.jsonl", "w", encoding="utf-8") as f:
    for i, object in enumerate(categories):
        messages = [{"role": "user", "content": prompt.replace("---object---", object)}]
        while True:
            try:
                response = client.chat.completions.create(
                    model="gpt-4",  # 'gpt-3.5-turbo', 'gpt-4', 'gpt-3.5-turbo-16k', 'gpt-4-32k'
                    messages=messages,
                )
                ann = response.choices[0].message.content
                print(i, object, ann)
                res[object] = ann
                print(json.dumps({"object": object, "annotation": ann}),file=f, flush=True)
                break
            except Exception as e:
                print(e)
                continue


# with open(r'D:\code\LEGENT\LEGENT\legent\scene_generation\data_annotation\new_data\annotations.json','w') as f:
#     json.dump(res,f,indent=4,ensure_ascii=False)

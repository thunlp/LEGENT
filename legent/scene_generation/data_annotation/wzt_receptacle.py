prompt = """
你是一个AI助手，你需要根据你的常识信息，对一些物体进行标注，主要涉及到物体在室内环境中如何摆放的问题。
首先我会给你提供一个物体列表，接下来我会指定某一个特定物体，你需要判断列表中有哪些物体可以放在这个物体的上面。
物体列表为：air_conditioner, apple, avocado, bacon, banana, beet, book, bottle, bowl, box, bread, broccoli, bun, burger, butter, cabbage, cake, candle, carrot, certificate, cezve, champagne, cheese, cherry, chicken, chili, chocolate, christmas_lollipop, clock, clothes, coffee_cup, coffee_machine, cola, cookie, corn, countertop, cucumber, cup, cupcake, cutting_board, donut, drainer, dress, dumbbell, egg, eggplant, fish, fork, frame, french_fries, game_console, gamepad, garlic, gift_box, globe, grape, hot_dog, jar, ketchup, kettle, keyboard, kitchen_hanger, kiwi, knife, kubik_rubik, lamp, laptop, lemon, lollipop, mirror, mouse_mat, mushroom, mustard, onion, orange, painting, pan, pancakes, pc, pc_mouse, pc_screen, pear, pen_holder, pendulum, pepper, photo_frame, pie, pillow, pineapple, pizza, plate, plumbing, pot_cover, potato, printer, pumpkin, sandwich, santizer, sausage, seasoning_jar, shelf, shoe, shorts, shower_gel, shrimp, slippers, soda, soy_sauce_bottle, soy_sauce_bowl, spatula, spoon, srub_sponge, steak, steam_pot, strawberry, sushi, t-shirt, taco, tangerin, teapot, toast, toaster, toilet_paper, tomato, toothbrush, toothbrush_cup, toothpaste, towel, towel_rail, toy, trophy, trousers, turnip, tv, tv_remote, ventilation, watermelon, wine, wineglass, wok, zucchini
可以摆放的物体需要和指定的物体有一些相关性，通常二者的使用场景需要相似（比如kitchen_table上会摆放很多厨房中会出现的物体，如水果蔬菜等等），我会给你提供一些例子。
[例子1]
物体：kitchen_table
可以摆放的物体：apple, avocado, bacon, banana, beet, bottle, bread, broccoli, bun, burger, butter, cabbage, cake, candle, carrot, cheese, cherry,chicken, chili, chocolate, cola, cookie, corn, cucumber, cup, cupcake, cutting_board, donut, egg, eggplant, fish, fork, french_fries, garlic, grape, hot_dog, jar, ketchup, kettle, kiwi, knife, lemon, mushroom, mustard, onion, orange, pancakes, pear, pepper, pie, pineapple, pizza, plate, potato, pumpkin, sandwich, sausage, seasoning_jar, shrimp, soda, soy_sauce_bottle, soy_sauce_bowl, spoon, steak, strawberry, sushi, taco, toast, tomato, watermelon, wine, zucchini
[例子2]
物体：sink
可以摆放的物体：bottle, mirror, santizer, shower_gel, scrub_sponge, toothbrush, toothbrush_cup, toothpaste, towel
例子结束，现在请你给一个物体标注（从物体列表中找出可以放在这个物体上的物体），返回一行字符串，格式为：物体1, 物体2, 物体3, ... 
若指定物体上面几乎不会摆放其他物体，你只需输出"空"即可。
注意，你必须只从"可以摆放的物体："后面开始输出，不许做任何解释。
可以摆放的物体只能从上述物体列表中选取，不可自行添加。
[标注]
物体：---object---
可以摆放的物体：
"""

API_KEY = "sk-qmu3GtIMZtNYCTMm743199219bD44791BfBcDbFd9d1b3404"
import openai

base_url = "https://yeysai.com/v1"
client = openai.OpenAI(api_key=API_KEY, base_url=base_url)

import json

with open(r'D:\code\LEGENT\LEGENT\legent\scene_generation\data_annotation\new_data\receptacle_objects.json','r',encoding='utf-8') as f:
    objects = json.load(f)

res = {}
with open(r"D:\code\LEGENT\LEGENT\legent\scene_generation\data_annotation\new_data\annotation_receptacle.jsonl", "w", encoding="utf-8") as f:
    for i, object in enumerate(objects):
        messages = [{"role": "user", "content": prompt.replace("---object---", object)}]
        # response = client.chat.completions.create(
        #     model="gpt-4",  # 'gpt-3.5-turbo', 'gpt-4', 'gpt-3.5-turbo-16k', 'gpt-4-32k'
        #     messages=messages,
        # )
        # ann = response.choices[0].message.content
        # print(i, object, ann)
        # res[object] = ann
        # print(json.dumps({"object": object, "annotation": ann}),file=f, flush=True)
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
            except KeyboardInterrupt:
                exit()
            except Exception as e:
                print(e)
                continue
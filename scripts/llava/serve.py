import os
import torch

from legent.model.llava.constants import (
    IMAGE_TOKEN_INDEX,
    DEFAULT_IMAGE_TOKEN,
    DEFAULT_IM_START_TOKEN,
    DEFAULT_IM_END_TOKEN,
    IMAGE_PLACEHOLDER,
)
from legent.model.llava.conversation import conv_templates, SeparatorStyle
from legent.model.llava.model.builder import load_pretrained_model
from legent.model.llava.utils import disable_torch_init
from legent.model.llava.mm_utils import (
    process_images,
    tokenizer_image_token,
    get_model_name_from_path,
    KeywordsStoppingCriteria,
)

from PIL import Image

import requests
from PIL import Image
from io import BytesIO
import re

from flask import Flask, jsonify, request
import requests

PORT_FOR_CLIENT = 50050
app = Flask(__name__)

model_path: str = os.environ['MODEL_PATH']
model_base: str = None
sep: str = ","
temperature: float = 0.2
top_p: float = None
num_beams: int = 1
max_new_tokens: int = 512

model_name = None
tokenizer, model, image_processor = None, None, None


FIXED_PROMPT = """You are a vision language assistant agent with high intelligence.
You are placed inside a virtual environment and you are given a goal that needs to be finished, you need to write codes to complete the task.
You can solve any complex tasks by decomposing them into subtasks and tackling them step by step, but you should only provide the action code for solving the very next subtask.
You need to call the following action apis to complete the tasks:
1. speak(text): reply to the questions.
2. move_forward(meters): move forward a certain distance.
3. rotate_right(degrees): rotate a certain degrees.
4. rotate_down(degrees)
5. grab()
6. release()
"""

# TODO: combine chat and action history
add_action_history = False
action_history = []
MAX_HISTORY_NUM = 10


def make_instruction_infer(task):
    global add_action_history, action_history
    if add_action_history:
        action_history = f"Previous Actions: {'; '.join(action_history)}\n" if action_history else ""
    else:
        action_history = ""
    return f"{FIXED_PROMPT}Your task: {task}\n{action_history}Please give your next action. The view you see: "


@app.route("/clear_history", methods=['GET'])
def clear_history():
    global action_history
    action_history = []
    return jsonify({})


@app.route("/get_action", methods=['POST'])
def get_action():
    file = request.files['image']
    text = request.form['text']
    file.save('temp.png')

    image_file = "https://llava-vl.github.io/static/images/view.jpg"
    query = "What are the things I should be cautious about when I visit here?"
    image_file = 'temp.png'
    query = text
    action = infer_model(image_file, make_instruction_infer(query))
    if add_action_history:
        action_history.append(action)
        action_history = action_history[-MAX_HISTORY_NUM:]
    response = {
        'action': action
    }
    return jsonify(response)


def image_parser(image_file):
    out = image_file.split(sep)
    return out


def load_image(image_file):
    if image_file.startswith("http") or image_file.startswith("https"):
        response = requests.get(image_file)
        image = Image.open(BytesIO(response.content)).convert("RGB")
    else:
        image = Image.open(image_file).convert("RGB")
    return image


def load_images(image_files):
    out = []
    for image_file in image_files:
        image = load_image(image_file)
        out.append(image)
    return out


def init_model():
    global model_name, tokenizer, model, image_processor
    # Model
    disable_torch_init()

    model_name = get_model_name_from_path(model_path)
    tokenizer, model, image_processor, context_len = load_pretrained_model(
        model_path, model_base, model_name
    )


def infer_model(image_file, query):
    global model_name, tokenizer, model, image_processor
    qs = query
    image_token_se = DEFAULT_IM_START_TOKEN + DEFAULT_IMAGE_TOKEN + DEFAULT_IM_END_TOKEN
    if IMAGE_PLACEHOLDER in qs:
        if model.config.mm_use_im_start_end:
            qs = re.sub(IMAGE_PLACEHOLDER, image_token_se, qs)
        else:
            qs = re.sub(IMAGE_PLACEHOLDER, DEFAULT_IMAGE_TOKEN, qs)
    else:
        if model.config.mm_use_im_start_end:
            qs = image_token_se + "\n" + qs
        else:
            qs = DEFAULT_IMAGE_TOKEN + "\n" + qs

    # assert "v1" in model_name.lower()
    conv_mode = "llava_v1"
    conv = conv_templates[conv_mode].copy()
    conv.append_message(conv.roles[0], qs)
    conv.append_message(conv.roles[1], None)
    prompt = conv.get_prompt()

    image_files = image_parser(image_file)
    images = load_images(image_files)
    images_tensor = process_images(
        images,
        image_processor,
        model.config
    ).to(model.device, dtype=torch.float16)

    input_ids = (
        tokenizer_image_token(prompt, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt")
        .unsqueeze(0)
        .cuda()
    )

    stop_str = conv.sep if conv.sep_style != SeparatorStyle.TWO else conv.sep2
    keywords = [stop_str]
    stopping_criteria = KeywordsStoppingCriteria(keywords, tokenizer, input_ids)

    with torch.inference_mode():
        # model: llava.model.language_model.llava_llama.LlavaLlamaForCausalLM
        # generate source code at PreTrainedModel - GenerationMixin
        # generate ->
        #   prepare_inputs_for_generation[override], put the image variable into **kwargs
        #   forward -> prepare_inputs_labels_for_multimodal, process the image variable into inputs
        output_ids = model.generate(
            input_ids,
            images=images_tensor,
            do_sample=True if temperature > 0 else False,
            temperature=temperature,
            top_p=top_p,
            num_beams=num_beams,
            max_new_tokens=max_new_tokens,
            use_cache=True,
            stopping_criteria=[stopping_criteria],
        )

    input_token_len = input_ids.shape[1]
    n_diff_input_output = (input_ids != output_ids[:, :input_token_len]).sum().item()
    if n_diff_input_output > 0:
        print(
            f"[Warning] {n_diff_input_output} output_ids are not the same as the input_ids"
        )
    outputs = tokenizer.batch_decode(
        output_ids[:, input_token_len:], skip_special_tokens=True
    )[0]
    outputs = outputs.strip()
    if outputs.endswith(stop_str):
        outputs = outputs[: -len(stop_str)]
    outputs = outputs.strip()
    print(outputs)
    return outputs


if __name__ == "__main__":
    image_file = "https://llava-vl.github.io/static/images/view.jpg"
    query = "What are the things I should be cautious about when I visit here?"

    init_model()
    infer_model(image_file, query)
    app.run(debug=True, use_reloader=False, port=PORT_FOR_CLIENT, host="0.0.0.0")

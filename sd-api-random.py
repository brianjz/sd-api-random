import base64
import io
import random
import argparse
import requests
from requests import ConnectionError, Timeout, HTTPError
import time
from datetime import datetime as dt
from PIL import Image, PngImagePlugin
from time import sleep
import os

DEFAULT_SD_URL = "http://127.0.0.1:7860"
DEFAULT_SAVE_PATH = "PATH_TO_SAVE_IMAGES"
DEFAULT_NEG_PROMPT = "UnrealisticDream, easynegative"
DEFAULT_MODELS_DIR = "PATH_TO_MODELS"

def configure(args):
    print("Configuring...")
    global config_sd_url
    global config_archive_path
    global config_neg_prompt
    global config_models_dir
    global config_num_imgs_to_generate

    config_sd_url = DEFAULT_SD_URL
    config_archive_path = DEFAULT_SAVE_PATH
    config_neg_prompt = DEFAULT_NEG_PROMPT
    config_num_imgs_to_generate = args.num
    config_models_dir = DEFAULT_MODELS_DIR

def read_random_line(file):
    file_path = file
    selected_line = ''

    with open(file_path, encoding='utf-8') as f:
            lines1 = [l for l in f]

    selected_line = random.choice(lines1)
    # replace sections that sometimes appear in prompts
    selected_line = selected_line.replace(' - ', '-').replace('4 k', '4k').replace('8 k', '8k').replace('!', '').replace('3 d', '3d')
    return selected_line.rstrip()

def get_models(folder_path):
    extensions = [".safetensors", ".ckpt"]

    model_list = []
    for root, _, files in os.walk(folder_path):
        for file_name in files:
            _, file_ext = os.path.splitext(file_name)

            # Check if the file extension matches the desired extensions
            if file_ext.lower() in extensions:
                model_list.append(file_name)

    return model_list

def get_current_checkpoint():
    resp = retry_request(url=f"{config_sd_url}/sdapi/v1/options", type="get")
    ckpt = resp.json()

    return ckpt['sd_model_checkpoint']

def retry_request(url, json={}, type="post"):
    print(f"Sending {type.upper()} request to: {url}")
    response = None
    max_attempts = 3
    attempts = max_attempts
    while attempts > 0:
        attempts -= 1
        retry_delay = pow(5, (max_attempts - attempts))
        try:
            if type == "post":
                response = requests.post(url=url, json=json, timeout=1200)
            else:
                response = requests.get(url=url, json=json, timeout=1200)
            response.raise_for_status()
            break
        except ConnectionError as e:
            if attempts <= 0:
                print(f"Connection Error => too may attempts")
                raise
            print(f"Connection Error in request. Pausing for {retry_delay} seconds and retrying... ({attempts} attempts left)")
            time.sleep(retry_delay)
        except HTTPError as e:
            if attempts <= 0:
                print(f"HTTP Error => too many attempts.")
                raise
            print(f"HTTP Error in request. Pausing for {retry_delay} seconds and retrying... ({attempts} attempts left)")
            time.sleep(retry_delay)
        except Timeout as e:
            print(f"Request timed out.")
            raise
    
    return response

def saveImage(img_json, save_path, model, args):
    img = img_json["images"][0]
    image = Image.open(io.BytesIO(base64.b64decode(img.split(",",1)[0])))

    finalprompt = img_json['info'].split('"infotexts": ["')[1].split("\\nNegative prompt:")[0]
    image_payload = {
        "image": "data:image/png;base64," + img
    }
    info_response = retry_request(url=f"{config_sd_url}/sdapi/v1/png-info", json=image_payload)

    pnginfo = PngImagePlugin.PngInfo()
    pnginfo.add_text("parameters", info_response.json().get("info"))

    now = dt.now()
    datetime_str = now.strftime("%Y%m%d%H%M%S")
    modelname = model.split(".")[0]
    img_filename = f"{save_path}RECV_{datetime_str}_{modelname}"
    print(f"===> Saving to {img_filename}")
    image.save(img_filename + ".png", pnginfo=pnginfo)
    if args.saveprompt:
        with open(img_filename + ".txt", 'w') as f:
            f.write(finalprompt)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--file', default='k:\\recv\\ai\\prompts.txt', help="Text file with list of prompts, one each line")
    parser.add_argument('-n', '--num', default=1, type=int, help="Number of images to generate per model")
    parser.add_argument('-r' ,'--repeat', default=1, type=int, help="Number of iterations of -num")
    parser.add_argument('-d', '--dimensions', default="512x768", help="Image dimensions WxH, defaults to 512x768")
    parser.add_argument('-s', '--steps', default=30, type=int, help="Number of steps, defaults to 30")
    parser.add_argument('-sp', '--sampler', default="Euler a", help="Sampler, defaults to Euler a")
    parser.add_argument('--saveprompt', action='store_true', help="Save the prompt to a separate text file in same directory")
    parser.add_argument('--keepmodel', action='store_true', help="Don't roll back to initial model after completed")
    parser.add_argument('--usecurrent', action='store_true', help="Use current loaded model, not random one")
    parser.add_argument('-noex', '--noextensions', action='store_true', help="Disable sending extension/scripts data [adetailer, etc]")
    args = parser.parse_args()

    configure(args)

    dimensions = args.dimensions.split('x')
    txt2img_payload = {
        "prompt": "",
        "negative_prompt": config_neg_prompt,
        "seed": -1,
        "sampler_name": args.sampler,
        "batch_size": 1,
        "steps": args.steps,
        "cfg_scale": 7,
        "width": dimensions[0],
        "height": dimensions[1],
        "save_images": True,
    }

    if not args.noextensions:
        txt2img_payload["alwayson_scripts"] = {
            "adetailer": {
                "args": [
                    True, { "ad_model": "face_yolov8n.pt" }
                ]
            }
        }

    all_models = get_models(config_models_dir)
    cur_ckpt = get_current_checkpoint()

    # print(txt2img_payload)
    for rep in range(args.repeat):
        if args.usecurrent:
            beg = cur_ckpt.find("\\")
            end = cur_ckpt.find("[")

            if end == -1: end = ""
            random_model = cur_ckpt[beg+1:end].strip()
            print(f"=> Using Model: {random_model}")
        else:
            random_model = random.choice(all_models)
            options_payload = {
                "sd_model_checkpoint": random_model,
            }

            print(f"=> Using Model: {random_model}")
            retry_request(url=f"{config_sd_url}/sdapi/v1/options", json=options_payload)

        # rednered_images = []
        for _ in range(config_num_imgs_to_generate):
            random_line = read_random_line(args.file)
            txt2img_payload["prompt"] = random_line
            print("Current prompt ==> ", txt2img_payload["prompt"])
            print("Sending txt2img request", _+1, "of", config_num_imgs_to_generate, "...")
            response = retry_request(url=f"{config_sd_url}/sdapi/v1/txt2img", json=txt2img_payload)
            img_json = response.json()
            saveImage(img_json, config_archive_path, random_model, args)
            print()
        if not rep + 1 == args.repeat:
            print("==> Finished iteration", rep+1, "of", args.repeat, "taking a pause...")
            sleep(15)
        print()

    if not args.keepmodel and not random_model in cur_ckpt:
        options_payload = {
            "sd_model_checkpoint": cur_ckpt,
        }
        print(f"Restoring previous SD checkpoint: {cur_ckpt}")
        retry_request(url=f"{config_sd_url}/sdapi/v1/options", json=options_payload)

if __name__ == "__main__":
    main()
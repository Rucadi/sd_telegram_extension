
import requests
import base64
import queue 
import threading
import json
import time
import extensions.sd_telegram_extension.tgbot.config as tgconfig

bot_needs_restart = False
queue_thread = None

joblist = queue.PriorityQueue()
telegram_channel_id = tgconfig.getSystemConfig().getBotLogChannel()
telegram_bot_api = tgconfig.getSystemConfig().getBotAPI()

command_list = ["ai", "lai", "dai", "fai", "rai", "frai", "tag", "512", "768",  "setmodel", "set", "steps", "explain", "negativetag", "listmodels"]
telegram_last_update = 0

print("TELEGRAM BOT API:", telegram_bot_api)

inline_keyboard = {
  "inline_keyboard": [
    [
      {
        "text": "hi",
        "callback_data": "hi"
      }
    ]
  ]
}

def telegram_api_url():
    global telegram_bot_api
    return f"https://api.telegram.org/bot{telegram_bot_api}"

def telegram_file_api_url():
    global telegram_bot_api
    return f"https://api.telegram.org/file/bot{telegram_bot_api}"


def getWithRetry(url, data=None, headers=None, timeout=10, retries=5):
    for i in range(retries):
        try:
            return requests.get(url, data=data, headers=headers, timeout=timeout)
        except Exception as ERR:
            print(ERR)
    return None


def postWithRetry(url, data=None, json=None, files=None, timeout=10, retries=5):
    for i in range(retries):
        try:
            return requests.post(url, data=data, files=files, json=json, timeout=timeout)
        except Exception as ERR:
            print(ERR)
    return None


def sd_generate_image(item):
    AI_API_URL="http://127.0.0.1:7860"
    endpointuri = '/sdapi/v1/txt2img'
    print(item)
    payload = {
        "init_images": [],
        "resize_mode": 0,
        "prompt": item['prompt'],
        "seed": -1,
        "sampler_name": "Euler a",
        "batch_size": 1,
        "n_iter": 1,
        "steps": 28,
        "cfg_scale": 12,
        "denoising_strength" : 0.75,
        "restore_faces": False,
        "width": 512,
        "height": 786,
        "negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, ",
        "override_settings": {},
        "sampler_index": "Euler",
        "include_init_images": False
    }
    print("TRYING POST")
    response = requests.post(url=f'{AI_API_URL}{endpointuri}', json=payload)
    print(response)
    return base64.b64decode(response.json()["images"][0])

def telegram_task_image_generation(item):
    getWithRetry(telegram_api_url()+"/sendMessage", data={'chat_id': telegram_channel_id, 'text': item["raw_message"]},  timeout=10)
    getWithRetry(telegram_api_url()+"/sendMessage", data={'chat_id': telegram_channel_id, 'text': item["raw"]},  timeout=10)
    if item["img"] != None:
        postWithRetry(telegram_api_url()+'/sendPhoto',
                    files={'photo': ("img", item["img"])},
                    data={'chat_id': telegram_channel_id, 'caption': "Base image for next prompt" },  timeout=10)
                    
    generated_image = sd_generate_image(item)
    postWithRetry(telegram_api_url()+'/sendPhoto',
                  files={'photo': ("img", generated_image)},
                  data={'chat_id': telegram_channel_id, 'caption': item["prompt"]},  timeout=10)

def telegram_task_image_explain(item):
    pass


def get_queue_item():
    global joblist
    try:
        item = joblist.get_nowait()
        return item
    except:
        time.sleep(0.3)
        return None

def processQueueThread():
    global joblist
    global bot_needs_restart
    while not bot_needs_restart:
        item = get_queue_item()
        if item == None:
            continue
        try:
            if item["command"] == "explain":
                telegram_task_image_explain(item)
            else:
                telegram_task_image_generation(item)
                
        except Exception as ERR:
            print(ERR)
            joblist.task_done()




def telegram_download_image(fileId):
    try:
        fr = getWithRetry(telegram_api_url()+'/getFile?file_id='+fileId, timeout=10).json()["result"]["file_path"]
        URI = f"{telegram_file_api_url()}/{fr}"
        cnt = getWithRetry(URI, timeout=30).content 
        return cnt
    except Exception as ERR:
        print(ERR)
        return None




def telegram_get_reply_image(data):
    try:
        return telegram_download_image(data['message']['reply_to_message']['photo'][-1]["file_id"])
    except:
        return None




def telegram_filter_commands(text):
    global command_list
    for command in command_list:
        text = text.replace('/'+command,"").replace('/'+command+" ","")
    return text.strip()



def telegram_get_command(message):
    global command_list
    for command in command_list:
        if message.startswith('/'+command):
            return command, telegram_filter_commands(message)
    return None, None

def telegram_msg_get_negative_tags(message):
    return None, message
    #negative_tags = []
    #for tag in message.split(" "):
    #    if tag.startswith("-"):
    #        negative_tags.append(tag[1:])
    #        message.replace(tag, "")
    #return negative_tags, message



def telegram_msg_get_prompt(message):
    return message



def telegram_parse_update(data):
    try:
        data['message']['text']
    except:
        return None

    command, message = telegram_get_command(data['message']['text'])
    
    if command is None:
        return None

    img = telegram_get_reply_image(data)
    raw =  json.dumps(data['message'])
    raw_message = telegram_filter_commands(data['message']['text'])
    negative_tags, message = telegram_msg_get_negative_tags(message)
    prompt = raw_message #temporary
    chat_id = data['message']['chat']['id']
    reply_id = data['message']['message_id']
    update_message_id = None
    user_id = data['message']['from']['id']
    return {
        "img": img,
        "command": command,
        "message": message,
        "raw": raw,
        "raw_message": raw_message,
        "negative_tags": negative_tags,
        "prompt": prompt,
        "chat_id": chat_id,
        "reply_id": reply_id,
        "update_message_id": update_message_id,
        "user_id": user_id
    }

    

def telegram_get_updates(botApi, lastUpdate):
    try:
        print(telegram_api_url()+'/getUpdates')
        return requests.get(telegram_api_url()+'/getUpdates', data={'offset': lastUpdate}, headers={'Accept': 'application/json'},  timeout=2).json()['result']
    except Exception as ERR:
        print(ERR)
        return None 


def telegram_working_loop():
    global telegram_last_update
    global joblist
    print(joblist)

    updates =  telegram_get_updates(telegram_bot_api, telegram_last_update)
    print(updates)
    if updates is None or len(updates) == 0:
        return False
    # set lastupdate to the update_id of the last update

    telegram_last_update = updates[-1]['update_id'] + 1
    print(telegram_last_update)

    for data in updates:
        parsed_command = telegram_parse_update(data)
        if(parsed_command is None):
            continue
        try:
            joblist.put(parsed_command)
        except Exception as ERR:
            print(ERR)
            pass
        
    

def polling_callback():
    telegram_working_loop()


def app_start(a,b):
    global queue_thread
    global bot_needs_restart
    bot_needs_restart = False
    queue_thread = threading.Thread(target=processQueueThread)
    queue_thread.start()
    print(queue_thread)

def on_before_reload():
    global queue_thread
    global bot_needs_restart
    bot_needs_restart = True
    queue_thread.join()

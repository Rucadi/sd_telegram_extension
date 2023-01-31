
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
command_list = tgconfig.getCommandConfig().getCommands()
#["ai", "lai", "dai", "fai", "rai", "frai", "tag", "512", "768",  "setmodel", "set", "steps", "explain", "negativetag", "listmodels"]
telegram_last_update = 0

generation_command_list = tgconfig.getCommandConfig().getGenerationCommands()


def getArrayOfArraysFromList(list, size):
    return [list[i:i + size] for i in range(0, len(list), size)]


def getBaseInlineKeyboard():
    return  {"inline_keyboard": []}

model_selection_kb = getBaseInlineKeyboard()
sampler_selection_kb = getBaseInlineKeyboard()
img_resolution_selection_kb = getBaseInlineKeyboard()
cfg_configration_kb = getBaseInlineKeyboard()
num_steps_kb = getBaseInlineKeyboard()


empty_list = []
for model in tgconfig.getModelConfig().getAllowList():
    empty_list.append({
        "text": model,
        "callback_data": f"setmodel,{model}"
      })

model_selection_kb["inline_keyboard"] = getArrayOfArraysFromList(empty_list, 3)


empty_list = []

for sampler in tgconfig.Utils.getSamplers():
    empty_list.append({
        "text": sampler,
        "callback_data": f"setsampler,{sampler}"
      })

sampler_selection_kb["inline_keyboard"] = getArrayOfArraysFromList(empty_list, 3)

empty_list = []
for entry in tgconfig.getGenerationConfig().getImageSizes():
    xval = entry['x']
    yval = entry['y']
    empty_list.append({
        "text": f"{xval}x{yval}",
        "callback_data": f"setresolution,{xval},{yval}"
      })

img_resolution_selection_kb["inline_keyboard"] = getArrayOfArraysFromList(empty_list, 3)


empty_list = []
for entry in range(6,13):
    empty_list.append({
        "text": f"{entry}",
        "callback_data": f"setcfg,{entry}"
      })

cfg_configration_kb["inline_keyboard"] = getArrayOfArraysFromList(empty_list, 3)


empty_list = []
for entry in [4,8,12,16,20,24,28,32,36,40,46,50]:
    if not tgconfig.getGenerationConfig().getAllowUserCfgSteps():
        break
    if entry > tgconfig.getGenerationConfig().getUserMaxSteps():
        break
    empty_list.append({
        "text": f"{entry}",
        "callback_data": f"setsteps,{entry}"
      })

num_steps_kb["inline_keyboard"] = getArrayOfArraysFromList(empty_list, 3)


print(model_selection_kb)
print("TELEGRAM BOT API:", telegram_bot_api)



cmd_text_info = ""

for cmd in tgconfig.getCommandConfig().getCustomCommands():
    cmd_text_info  = cmd_text_info + f"/{cmd} - {tgconfig.getCommandConfig().getCommand(cmd)['desc']}\n"
    


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


# load jpg image loading.jpg from disk
anyaLoading = None
with open("extensions/sd_telegram_extension/tgbot/loading.jpg", "rb") as image_file:
    anyaLoading = image_file.read()

def sendMessageReplyAndGetId(chatId, messageId):
    responseFromChannel = postWithRetry(telegram_api_url()+'/sendPhoto',
                  files={'photo': ("img", anyaLoading)},
                  data={'chat_id': chatId,  'reply_to_message_id': messageId, 'caption': f"OkiDoki! Generating Image :D, current queue: {joblist.qsize()} " }, timeout=10)
    return responseFromChannel.json()["result"]["message_id"]



def sd_generate_image(item):
    AI_API_URL="http://127.0.0.1:7860"
    endpointuri = '/sdapi/v1/txt2img'
    print(item)
    try:
        user_id = str(item['user_id'])
        cfg_scale = tgconfig.getUserConfig().getUserCfgScale(user_id)
        user_model = tgconfig.getUserConfig().getUserModel(user_id)
        step_num = tgconfig.getUserConfig().getUserStepNum(user_id) if tgconfig.getGenerationConfig().getAllowUserCfgSteps() else tgconfig.getGenerationConfig().getDefaultSteps()
        resolution = tgconfig.getUserConfig().getUserResolution(user_id)
        sampler = tgconfig.getUserConfig().getUserSampler(user_id)
    except Exception as ERR:
        return None
        


    print("GOT ALL CONFIGS", cfg_scale, user_model, step_num, resolution, sampler)
    try: 
        response = requests.post(url=f'{AI_API_URL}/sdapi/v1/options', json={"sd_model_checkpoint": user_model})
    except:
        return None
    negative_prompt = tgconfig.getSystemConfig().getBotDefaultNegativePrompt()


    prompt_to_add = tgconfig.getSystemConfig().getBotDefaultPrompt()

    if item['command'] !=  'ai':
        cmdinfo = tgconfig.getCommandConfig().getCommand(item['command'])
        prompt_to_add = prompt_to_add + cmdinfo['pos']
        negative_prompt = negative_prompt + cmdinfo['neg']
        
    prompt_to_add = prompt_to_add + item['prompt']

    payload = {
        "prompt": prompt_to_add,
        "sampler_name": sampler,
        "steps": step_num,
        "cfg_scale": cfg_scale,
        "denoising_strength" : 0.75,
        "width": resolution['x'],
        "height": resolution['y'],
        "negative_prompt": negative_prompt,
        "include_init_images": False
    }

    print("payload: ", payload)
    if item["img"] != None:
        payload["include_init_images"] = True
        payload["init_images"] = [ base64.b64encode(item["img"]).decode("ascii")]
        endpointuri = '/sdapi/v1/img2img'

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
                    

    user_id = str(item['user_id'])
    user_model = tgconfig.getUserConfig().getUserModel(user_id)
    print( str(tgconfig.getUserConfig().getUserModel(user_id)), "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@", user_id, user_model)
    generated_image = sd_generate_image(item)
    responseFromChannel = postWithRetry(telegram_api_url()+'/sendPhoto',
                  files={'photo': ("img", generated_image)},
                  data={'chat_id': telegram_channel_id, 'caption': user_model+': \n'+item["prompt"]},  timeout=10)


    fileId = responseFromChannel.json()["result"]['photo'][-1]["file_id"]
    #send UPDATE IMAGE in the chat
    r = postWithRetry(telegram_api_url()+'/editMessageMedia',
                  data={'chat_id': item["chat_id"], 'message_id': item["updateMessageId"], 'media': json.dumps({"type":"photo", "media":fileId, "caption": user_model+':\n '+item["prompt"]})},  timeout=10)

def telegram_task_image_explain(item):
        AI_API_URL="http://127.0.0.1:7860"
        if item["img"] != None:
            payload = {
                    "image": base64.b64encode(item["img"]).decode("ascii"),
                    "model": "deepdanbooru"
                    }
            response = requests.post(url=f'{AI_API_URL}/sdapi/v1/interrogate', json=payload)
            postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': item["chat_id"],  'reply_to_message_id':  item["reply_id"], 'text': response.json()["caption"]},  timeout=60)
    


def get_queue_item():
    global joblist
    try:
        item = joblist.get_nowait()
        return item
    except:
        time.sleep(0.3)
        return None


def processCallbacks(item):
    uid = str(item['user_id'])
    print("CALLBACK HERE!!",  item)
    try:
        print("CMDVALUE0", item['cmdvalue'][0])
        if item['subcommand'] == "setmodel":
                tgconfig.getUserConfig().setUserModel(uid, item['cmdvalue'][0])
                postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': item['chat_id'], 'text': "Model set to " + item['cmdvalue'][0]},  timeout=10)
        elif item['subcommand'] == "setresolution":
            tgconfig.getUserConfig().setUserResolution(uid ,int(item['cmdvalue'][0]), int(item['cmdvalue'][1]))
            postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': item['chat_id'], 'text': "Image resolution set to " + item['cmdvalue'][0] + "x" + item['cmdvalue'][1]},  timeout=10)
        elif item['subcommand'] == "setcfg":
            tgconfig.getUserConfig().setUserCfgScale(uid, int(item['cmdvalue'][0]))
            postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': item['chat_id'], 'text': "CFG scale set to " + item['cmdvalue'][0]},  timeout=10)
        elif item['subcommand'] == "setsteps":
            print("setting steps")
            tgconfig.getUserConfig().setUserStepNum(uid, int(item['cmdvalue'][0]))
            print("AFTER STEPS")
            postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': item['chat_id'], 'text': "Steps set to " + item['cmdvalue'][0]},  timeout=10)
            print("AFTER POIST")
        elif item['subcommand'] == "setsampler":
            tgconfig.getUserConfig().setUserSampler(uid, item['cmdvalue'][0])
            postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': item['chat_id'], 'text': "Sampler set to " + item['cmdvalue'][0]},  timeout=10)
    except Exception as ERR:
        print(ERR)



def processQueueThread():
    global joblist
    global bot_needs_restart
    while not bot_needs_restart or not joblist.empty():
        item = get_queue_item()
        if item == None:
            continue
        try:
            print("PROCESSING QUEUE ITEM", item)
   
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
        test = data['message']['text']
    except:
        try:
            if 'callback_query' in data:
                print("SPLITTED QUERY IN DATA!!!")
                print(data)
                splitted = data['callback_query']['data'].split(",")
                val =  {
                    "command": "callback_query",
                    "subcommand": splitted[0],
                    "cmdvalue": splitted[1:],
                    "chat_id": data['callback_query']['from']['id'],
                    "user_id" : data['callback_query']['from']['id'],
                }
                print(val)
                return val
        except Exception as ERR:
            print(ERR)
            return None
    #check if data contains key callback_query
    print(data)
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
        return requests.get(telegram_api_url()+'/getUpdates', data={'offset': lastUpdate}, headers={'Accept': 'application/json'},  timeout=2).json()['result']
    except Exception as ERR:
        return None 


last_command_per_user = {}

def telegram_working_loop():
    global bot_needs_restart
    global last_command_per_user
    if(bot_needs_restart):
        return False
    global telegram_last_update
    global joblist

    updates =  telegram_get_updates(telegram_bot_api, telegram_last_update)
    if updates is None or len(updates) == 0:
        return False
    # set lastupdate to the update_id of the last update

    telegram_last_update = updates[-1]['update_id'] + 1

    for data in updates:
        parsed_command = telegram_parse_update(data)
        if(parsed_command is None):
            continue
        try:
            if parsed_command['command'] == "commands":
                getWithRetry(telegram_api_url()+"/sendMessage", data={'chat_id': parsed_command["chat_id"], 'text': cmd_text_info},  timeout=10)
            elif parsed_command["command"] == "explain":
                telegram_task_image_explain(parsed_command)
            elif parsed_command["command"] == "tag":
                pass
            elif parsed_command["command"] == "start":
                postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': parsed_command['chat_id'], 'text': tgconfig.getSystemConfig().getBotStartMsg()},  timeout=10)
            elif parsed_command['command'] == "config":
                print("CONFIG!!!!!")
                #send model list with inline keyboard using requests
                postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': parsed_command['chat_id'], 'text': "Select the model to use", 'reply_markup': json.dumps(model_selection_kb)},  timeout=10)
                postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': parsed_command['chat_id'], 'text': "Select the sampler", 'reply_markup': json.dumps(sampler_selection_kb)},  timeout=10)
                postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': parsed_command['chat_id'], 'text': "Select the resolution", 'reply_markup': json.dumps(img_resolution_selection_kb)},  timeout=10)
                postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': parsed_command['chat_id'], 'text': "Select the CFG Scale", 'reply_markup': json.dumps(cfg_configration_kb)},  timeout=10)
                postWithRetry(telegram_api_url()+'/sendMessage', data={'chat_id': parsed_command['chat_id'], 'text': "Select the number of steps", 'reply_markup': json.dumps(num_steps_kb)},  timeout=10)
            elif parsed_command['command'] == "callback_query":
                processCallbacks(parsed_command)

                #telegram_task_image_tag(parsed_command)
            elif  parsed_command['command'] in generation_command_list:
                parsed_command["updateMessageId"] = sendMessageReplyAndGetId(parsed_command["chat_id"], parsed_command["reply_id"])
                if parsed_command["prompt"] == "":
                    cmd = parsed_command["command"]
                    upmid =  parsed_command["updateMessageId"] 
                    parsed_command = last_command_per_user[parsed_command["user_id"]]
                    parsed_command["command"] = cmd
                    parsed_command["updateMessageId"] = upmid
                last_command_per_user[parsed_command["user_id"]] = parsed_command.copy()
                if parsed_command["command"] == "dai":
                    parsed_command["command"] = "ai"
                    laicommand = parsed_command.copy()
                    laicommand["command"] = "lai"
                    laicommand["updateMessageId"] = sendMessageReplyAndGetId(parsed_command["chat_id"], parsed_command["reply_id"])
                    joblist.put(laicommand)
                joblist.put(parsed_command)
        except Exception as ERR:
            print(ERR)
            continue
        
    

def polling_callback():
    telegram_working_loop()


def app_start(a,b):
    global queue_thread
    global bot_needs_restart
    bot_needs_restart = False
    queue_thread = threading.Thread(target=processQueueThread)
    queue_thread.start()

def on_before_reload():
    global queue_thread
    global bot_needs_restart
    bot_needs_restart = True
    queue_thread.join()

from modules import script_callbacks, sd_models, shared
import json


class  Utils():
    def getModels():
        return shared.list_checkpoint_tiles()

class UserConfig():
    pass



class ModelConfig():
    config_name = "model_config"

    tgbot_config = {}
    tgbot_default_config = {
            "default_model": "",
            "model_allow_list": [],
        }

    def addToAllowList(self, model):
        #IF ALREADY EXISTS RETURN
        if model in self.tgbot_config["model_allow_list"]:
            return

        self.tgbot_config["model_allow_list"].append(model)

    def removeFromAllowList(self, model):
        #if model not in list, return
        if model not in self.tgbot_config["model_allow_list"]:
            return

        self.tgbot_config["model_allow_list"].remove(model)

    def getAllowList(self):
        return self.tgbot_config["model_allow_list"]

    def getDefaultModel(self):
        return self.tgbot_config["default_model"]
    
    def setDefaultModel(self, default_model):
        self.tgbot_config["default_model"] = default_model

    def save(self):
        json.dump(self.tgbot_config, open(f"extensions/sd_telegram_extension/tgbot/{self.config_name}.json", "w"))

    def initConfig(self):
        self.tgbot_config = self.tgbot_default_config
        self.save()

    def load(self):
        #load from file as json
        try:
            self.tgbot_config = json.load(open(f"extensions/sd_telegram_extension/tgbot/{self.config_name}.json", "r"))
            # if key of tgbot_config is not in tgbot_default_config, add it 
            for key in self.tgbot_default_config:
                if key not in self.tgbot_config:
                    self.tgbot_config[key] = self.tgbot_default_config[key]
        except:
            self.initConfig()




class GenerationConfig():
    config_name = "generation_config"

    tgbot_config = {}
    tgbot_default_config = {
        "default_steps": 28,
        "default_images" : 1,
        "max_steps": 28,
        "user_max_steps": 28,
        "user_max_images": 1,
        "steps_allow_cfg": False,
        "images_allow_cfg": False,
        "allowed_image_sizes": [
            {"x": 256, "y": 256, "allow": True},
            {"x": 512, "y": 256, "allow": True},
            {"x": 256, "y": 512, "allow": True},
            {"x": 768, "y": 512, "allow": True},
            {"x": 512, "y": 768, "allow": True},
            {"x": 1024, "y": 768, "allow": False},
            {"x": 768, "y": 1024, "allow": False},
        ]
    }
    

    def getDefaultSteps(self):
        return self.tgbot_config["default_steps"]
    
    def setDefaultSteps(self, default_steps):
        self.tgbot_config["default_steps"] = default_steps

    def getDefaultImages(self):
        return self.tgbot_config["default_images"]

    def setDefaultImages(self, default_images):
        self.tgbot_config["default_images"] = default_images


    def setStepsAllowCfg(self, allow):
        self.tgbot_config["steps_allow_cfg"] = allow
   
    def getAllowUserCfgSteps(self):
     return self.tgbot_config["steps_allow_cfg"]
    

    def setImageAllowCfg(self, allow):
        self.tgbot_config["images_allow_cfg"] = allow

    def getAllowUserCfgImages(self):
        return self.tgbot_config["images_allow_cfg"]

    def setUserMaxSteps(self, max_steps):
        self.tgbot_config["user_max_steps"] = max_steps

    def setUserMaxImages(self, max_images):
        self.tgbot_config["user_max_images"] = max_images

    def getUserMaxSteps(self):
        return self.tgbot_config["user_max_steps"]

    def getUserMaxImages(self):
        return self.tgbot_config["user_max_images"]

 
    def toggle(self, x, y):
        for size in self.tgbot_config["allowed_image_sizes"]:
            if size["x"] == x and size["y"] == y:
                size["allow"] = not size["allow"]
                return size["allow"] 

    def getImageSizes(self):
        return self.tgbot_config["allowed_image_sizes"]

    def save(self):
        json.dump(self.tgbot_config, open(f"extensions/sd_telegram_extension/tgbot/{self.config_name}.json", "w"))

    def initConfig(self):
        self.tgbot_config = self.tgbot_default_config
        self.save()

    def load(self):
        #load from file as json
        try:
            self.tgbot_config = json.load(open(f"extensions/sd_telegram_extension/tgbot/{self.config_name}.json", "r"))
            # if key of tgbot_config is not in tgbot_default_config, add it 
            for key in self.tgbot_default_config:
                if key not in self.tgbot_config:
                    self.tgbot_config[key] = self.tgbot_default_config[key]
        except:
            self.initConfig()


class CommandConfig():
    config_name = "command_config"

    tgbot_config = {}
    tgbot_default_config = {}
    
    def getCommands(self):
        #return tgbot_config keys as a list of strings
        ret = []
        for key in self.tgbot_config:
            ret.append(str(key))
        return ret

    def addCommand(self, cmd, desc, pos, neg):
        self.tgbot_config[cmd] = {"desc": desc, "pos": pos, "neg": neg}

    def removeCommand(self, cmd):
        for command in self.getCommands():
            if cmd in command:
                del self.tgbot_config[cmd]

    def getCommand(self, cmd):
        return self.tgbot_config[cmd]

    def save(self):
        json.dump(self.tgbot_config, open(f"extensions/sd_telegram_extension/tgbot/{self.config_name}.json", "w"))

    def initConfig(self):
        self.tgbot_config = self.tgbot_default_config
        self.save()

    def load(self):
        #load from file as json
        try:
            self.tgbot_config = json.load(open(f"extensions/sd_telegram_extension/tgbot/{self.config_name}.json", "r"))
            # if key of tgbot_config is not in tgbot_default_config, add it 
            for key in self.tgbot_default_config:
                if key not in self.tgbot_config:
                    self.tgbot_config[key] = self.tgbot_default_config[key]
        except:
            self.initConfig()

class SystemConfig():
    config_name = "config"

    tgbot_config = {}
    tgbot_default_config = {
            "bot_stopped": False,
            "bot_name": "SD Telegram Bot",
            "bot_api": "",
            "bot_log_channel": "",
            "bot_default_prompt": "masterpiece, best quality, ",
            "bot_default_negative_prompt": "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, ",
            "default_model": "",
            "start_message": "Welcome to the SD Telegram Bot! This bot is a work in progress, so please be patient with it. If you have any questions, please ask in https://github.com/Rucadi/sd_telegram_extension. Thank you!",
        }


    def toggleBotRunning(self):
        self.tgbot_config["bot_stopped"] = not self.tgbot_config["bot_stopped"]

    def isBotRunning(self):
        return not self.tgbot_config["bot_stopped"]
                
    def getBotName(self):
        return self.tgbot_config["bot_name"]

    def setBotName(self, bot_name):
        self.tgbot_config["bot_name"] = bot_name

    def getBotAPI(self):
        return self.tgbot_config["bot_api"]

    def setBotAPI(self, bot_api):
        self.tgbot_config["bot_api"] = bot_api

    def getBotLogChannel(self):
        return self.tgbot_config["bot_log_channel"]

    def setBotLogChannel(self, bot_log_channel):
        self.tgbot_config["bot_log_channel"] = bot_log_channel

    def getBotDefaultPrompt(self):
        return self.tgbot_config["bot_default_prompt"]

    def setBotDefaultPrompt(self, bot_default_prompt):
        self.tgbot_config["bot_default_prompt"] = bot_default_prompt

    def getBotDefaultNegativePrompt(self):
        return self.tgbot_config["bot_default_negative_prompt"]

    def setBotDefaultNegativePrompt(self, bot_default_negative_prompt):
        self.tgbot_config["bot_default_negative_prompt"] = bot_default_negative_prompt

    def getBotStartMsg(self):
        return self.tgbot_config["start_message"]

    def setBotStartMsg(self, start_message):
        self.tgbot_config["start_message"] = start_message

    def save(self):
        json.dump(self.tgbot_config, open(f"extensions/sd_telegram_extension/tgbot/{self.config_name}.json", "w"))

    def initConfig(self):
        self.tgbot_config = self.tgbot_default_config
        self.save()

    def load(self):
        #load from file as json
        try:
            self.tgbot_config = json.load(open(f"extensions/sd_telegram_extension/tgbot/{self.config_name}.json", "r"))
            # if key of tgbot_config is not in tgbot_default_config, add it 
            for key in self.tgbot_default_config:
                if key not in self.tgbot_config:
                    self.tgbot_config[key] = self.tgbot_default_config[key]
        except:
            self.initConfig()


config = SystemConfig()
config.load()

model_config = ModelConfig()
model_config.load()

command_config = CommandConfig()
command_config.load()

generation_config = GenerationConfig()
generation_config.load()


def getModelConfig():
    global model_config
    return model_config
    
def getSystemConfig():
    global config
    return config

def getCommandConfig():
    global command_config
    return command_config

def getGenerationConfig():
    global generation_config
    return generation_config
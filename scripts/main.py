import gradio as gr
import requests
import base64
import queue 
import threading
import json
import extensions.sd_telegram_extension.tgbot.telegram as tgbot
import extensions.sd_telegram_extension.tgbot.config as tgconfig


from modules import script_callbacks, sd_models, shared
from modules.ui import setup_progressbar, gr_show, wrap_gradio_call, create_refresh_button
from webui import wrap_gradio_gpu_call



def on_ui_tabs():
    tgconfig.getSystemConfig().load()

    def get_bot_running_string():
        if tgbot.tgconfig.getSystemConfig().isBotRunning():
            return "[BOT RUNNING] Stop BOT"
        else:
            return "Start BOT"

    with gr.Blocks() as telegram_interface:
        with gr.Row(equal_height=True):
            db_bot_started = gr.Button(value=get_bot_running_string(), elem_id="db_save_config")

        with gr.Row().style(equal_height=False):
            with gr.Column(variant="panel"):

                with gr.Tab("Bot Basic Config"):
                    db_bot_name = gr.Textbox(label="Name", value=tgconfig.getSystemConfig().getBotName())
                    db_bot_api =  gr.Textbox(label="Bot API", value=tgconfig.getSystemConfig().getBotAPI())
                    db_bot_log_channel = gr.Textbox(label="Log Channel", value=tgconfig.getSystemConfig().getBotLogChannel())
                    db_bot_default_prompt =  gr.Textbox(label="[Default] Appended prompt to all requests", value=tgconfig.getSystemConfig().getBotDefaultPrompt())
                    db_bot_default_negative_prompt = gr.Textbox(label="[Default] Appended Negative prompt to all requests", value=tgconfig.getSystemConfig().getBotDefaultNegativePrompt())
                    db_bot_start_msg = gr.Textbox(label="/start message", value=tgconfig.getSystemConfig().getBotStartMsg())
                    basic_config_save = gr.Button(value="Save", elem_id="basic_config_save")

                with gr.Tab("Bot Command Config"):
                    with gr.Group():

                        with gr.Row():
                            print("DEFAULT MODEL:", tgconfig.getModelConfig().getDefaultModel())
                            db_bot_default_model = gr.components.Dropdown(label="Default Model", choices=tgconfig.Utils.getModels(), value=tgconfig.getModelConfig().getDefaultModel()) 
                            db_set_default_model = gr.components.Button(value="Set Default")

                        with gr.Row():
                            db_models_al  = gr.components.Dropdown(label="Models", choices=tgconfig.Utils.getModels())
                            #add button to add to allowlist if not in allowlist
                            db_add_to_al  = gr.components.Button(value="Add to allowlist")
                            print("ALLOWE LIST:", tgconfig.getModelConfig().getAllowList())
                            db_allow_list = gr.components.Dropdown(label="AllowList", choices=tgconfig.getModelConfig().getAllowList())
                            db_rem_of_al  = gr.components.Button(value="Remove from allowlist")

                    with gr.Group():
                        with gr.Row():
                            db_cmd_command = gr.Textbox(label="Custom command", placeholder="fai")
                            db_cmd_desc = gr.Textbox(label="Description", placeholder="Using this command appends prompts that helps on generating furry images")
                        with gr.Row():
                            db_cmd_positive_prompt = gr.Textbox(label="Positive prompt", placeholder="furry, paws, big eyes, fur on body")
                            db_cmd_negative_prompt = gr.Textbox(label="Negative prompt", placeholder="no fur on face, no fur on hands, no fur on feet")
                        with gr.Row():
                            db_cmd_add = gr.components.Button(value="Add command")


                    with gr.Group():
                        with gr.Row():
                            db_cmd_custom_command_list = gr.components.Dropdown(label="Command to Remove", choices=tgconfig.getCommandConfig().getCustomCommands(), interactive=True)
                            db_cmd_remove_command = gr.components.Button(value="Remove command")
                        with gr.Row():
                            db_cmd_to_del_definition = gr.Textbox(label="Description of the Command", interactive=False)
                            db_cmd_to_del_positive = gr.Textbox(label="Positive prompt", interactive=False)
                            db_cmd_to_del_negative = gr.Textbox(label="Negative prompt", interactive=False)
                                    

                with gr.Tab("Default Generation Params"):
                    with gr.Row():
                        db_steps_number = gr.components.Slider(label="Number Of Steps", minimum=1, maximum=50, step=1, value=tgconfig.getGenerationConfig().getDefaultSteps(), interactive=True)
                        db_user_steps_number = gr.components.Slider(label="[BOT USER CONFIG] MAX Number Of Steps", minimum=1, maximum=50, step=1, value=tgconfig.getGenerationConfig().getUserMaxSteps(), interactive=True)
                        db_allow_step_user_config = gr.components.Checkbox(label="Allow Bot User Config", value=tgconfig.getGenerationConfig().getAllowUserCfgSteps())
                    #with gr.Row():
                       #db_img_num = gr.components.Slider(label="Number Of Images", minimum=1, maximum=10, step=1, value=tgconfig.getGenerationConfig().getDefaultImages(), interactive=True)
                       #db_user_img_num = gr.components.Slider(label="[BOT USER CONFIG] MAX Number Of Images", min=1, max=10, value=tgconfig.getGenerationConfig().getUserMaxImages(),interactive=True)
                       #db_allow_user_img_num = gr.components.Checkbox(label="Allow Bot User Config", value=tgconfig.getGenerationConfig().getAllowUserCfgImages())
                
                    with gr.Row():
                        gr.HTML(value="<p>Allowed Image Sizes</p>")

                        for entry in tgconfig.getGenerationConfig().getImageSizes():
                            xval = entry['x']
                            yval = entry['y']
                            cb = gr.Checkbox(label=f"{xval}x{yval}", value=entry['allow'], interactive=True)
                            def allow_unallow_image_size(xval, yval, cbb):
                                val = tgconfig.getGenerationConfig().toggle(xval, yval)
                                tgconfig.getGenerationConfig().save()
                                return cbb.update(value=val)
                            a = lambda ccb = cb: ccb.change(fn=lambda xv = xval, yv=yval, cbb=ccb: allow_unallow_image_size(xv, yv, cbb),outputs=[ccb]) 
                            a()#capture values in lambda


        def save_config(*args):
            tgconfig.getSystemConfig().setBotName(args[0])
            tgconfig.getSystemConfig().setBotAPI(args[1])
            tgconfig.getSystemConfig().setBotLogChannel(args[2])
            tgconfig.getSystemConfig().setBotDefaultPrompt(args[3])
            tgconfig.getSystemConfig().setBotDefaultNegativePrompt(args[4])
            tgconfig.getSystemConfig().setBotStartMsg(args[5])
            tgconfig.getSystemConfig().save()

        basic_config_save.click(fn=save_config, inputs=[db_bot_name, db_bot_api, db_bot_log_channel, db_bot_default_prompt, db_bot_default_negative_prompt, db_bot_start_msg])

        def save_default_model(*args):
            tgconfig.getModelConfig().setDefaultModel(args[0])
            tgconfig.getModelConfig().addToAllowList(args[0])
            tgconfig.getModelConfig().save()
            return db_allow_list.update(choices = tgconfig.getModelConfig().getAllowList())

        db_set_default_model.click(fn=save_default_model, inputs=[db_bot_default_model], outputs=[db_allow_list]) 

        def add_to_allowlist(*args):
            tgconfig.getModelConfig().addToAllowList(args[0])
            tgconfig.getModelConfig().save()
            return db_allow_list.update(choices = tgconfig.getModelConfig().getAllowList())


        db_add_to_al.click(fn=add_to_allowlist, inputs=[db_models_al], outputs=[db_allow_list])

        def remove_from_allowlist(*args):
            tgconfig.getModelConfig().removeFromAllowList(args[0])
            tgconfig.getModelConfig().save()
            return db_allow_list.update(choices = tgconfig.getModelConfig().getAllowList())
        
        db_rem_of_al.click(fn=remove_from_allowlist, inputs=[db_allow_list], outputs=[db_allow_list])

        def add_custom_command(*args):
            tgconfig.getCommandConfig().addCommand(args[0], args[1], args[2], args[3])
            tgconfig.getCommandConfig().save()
            return db_cmd_custom_command_list.update(choices=tgconfig.getCommandConfig().getCommands())

        db_cmd_add.click(
            fn=add_custom_command, 
            inputs=[db_cmd_command, db_cmd_desc, db_cmd_positive_prompt, db_cmd_negative_prompt],
            outputs=[db_cmd_custom_command_list])

        def on_select_command_to_del(*args):
            cmd = tgconfig.getCommandConfig().getCommand(args[0])
            return [db_cmd_to_del_definition.update(value=cmd["desc"]), db_cmd_to_del_positive.update(value=cmd["pos"]), db_cmd_to_del_negative.update(value=cmd["neg"])]

        db_cmd_custom_command_list.change(fn=on_select_command_to_del, inputs=[db_cmd_custom_command_list], outputs=[db_cmd_to_del_definition, db_cmd_to_del_positive, db_cmd_to_del_negative])

        def on_remove_command(*args):
            tgconfig.getCommandConfig().removeCommand(args[0])
            tgconfig.getCommandConfig().save()
            return [db_cmd_custom_command_list.update(choices=tgconfig.getCommandConfig().getCommands())  ,db_cmd_to_del_definition.update(value=""), db_cmd_to_del_positive.update(value=""), db_cmd_to_del_negative.update(value="")]

        db_cmd_remove_command.click(fn=on_remove_command,  inputs=[db_cmd_custom_command_list], outputs=[db_cmd_custom_command_list, db_cmd_to_del_definition, db_cmd_to_del_positive, db_cmd_to_del_negative])

        def on_def_steps_number(*args):
            tgconfig.getGenerationConfig().setDefaultSteps(args[0])
            tgconfig.getGenerationConfig().save()
            return db_steps_number.update(value=args[0])

        db_steps_number.change(fn=on_def_steps_number, inputs=[db_steps_number], outputs=[db_steps_number])

        def on_def_user_steps_number(*args):
            tgconfig.getGenerationConfig().setUserMaxSteps(args[0])
            tgconfig.getGenerationConfig().save()
            return db_user_steps_number.update(value=args[0])

        db_user_steps_number.change(fn=on_def_user_steps_number, inputs=[db_user_steps_number], outputs=[db_user_steps_number])

        def on_def_allow_user_steps_number(*args):
            tgconfig.getGenerationConfig().setStepsAllowCfg(args[0])
            tgconfig.getGenerationConfig().save()
            return db_allow_step_user_config.update(value=args[0])

        db_allow_step_user_config.change(fn=on_def_allow_user_steps_number, inputs=[db_allow_step_user_config], outputs=[db_allow_step_user_config])

        #def on_def_img_number(*args):
        #    tgconfig.getGenerationConfig().setDefaultImages(args[0])
        #    tgconfig.getGenerationConfig().save()
        #    return db_img_num.update(value=args[0])

        #db_img_num.change(fn=on_def_img_number, inputs=[db_img_num], outputs=[db_img_num])

        #def on_def_user_img_number(*args):
        #    tgconfig.getGenerationConfig().setUserMaxImages(args[0])
        #    tgconfig.getGenerationConfig().save()
        #    return db_user_img_num.update(value=args[0])
        #db_user_img_num.change(fn=on_def_user_img_number, inputs=[db_user_img_num], outputs=[db_user_img_num])

        #def on_def_allow_user_img_number(*args):
        #    tgconfig.getGenerationConfig().setImageAllowCfg(args[0])
        #    tgconfig.getGenerationConfig().save()
        #    return db_allow_user_img_num.update(value=args[0])
        #db_allow_user_img_num.change(fn=on_def_allow_user_img_number, inputs=[db_allow_user_img_num], outputs=[db_allow_user_img_num])


        def on_bot_status_click(*args):
            tgconfig.getSystemConfig().toggleBotRunning()
            tgconfig.getSystemConfig().save()
            return db_bot_started.update(value=get_bot_running_string())

        db_bot_started.click(fn=on_bot_status_click, inputs=[db_bot_started], outputs=[db_bot_started])
    return (telegram_interface, "Telegram Bot", "telegram_interface"),



def polling_callback():
    if tgconfig.getSystemConfig().isBotRunning():
        tgbot.polling_callback()

def reload_callback():
    from importlib import reload  # Python 3.4+
    reload(tgconfig)
    reload(tgbot)
    #reimport(tgbot)


script_callbacks.on_polling(polling_callback)

script_callbacks.on_ui_tabs(on_ui_tabs)

script_callbacks.on_app_started(tgbot.app_start)
script_callbacks.on_before_reload(reload_callback)

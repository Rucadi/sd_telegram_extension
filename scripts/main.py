import gradio as gr


from modules import script_callbacks, sd_models, shared
from modules.ui import setup_progressbar, gr_show, wrap_gradio_call, create_refresh_button
from webui import wrap_gradio_gpu_call



def on_ui_tabs():
    show_lora = False
    try:
        show_lora = shared.cmd_opts.test_lora
    except:
        pass

    with gr.Blocks() as telegram_interface:
        with gr.Row(equal_height=True):
            db_save_params = gr.Button(value="Save Params", elem_id="db_save_config")
            db_load_params = gr.Button(value='Load Params')
            db_generate_checkpoint = gr.Button(value="Generate Ckpt")
            db_interrupt_training = gr.Button(value="Cancel")
            db_train_model = gr.Button(value="Train", variant='primary')

        with gr.Row().style(equal_height=False):

            default_prompt = "masterpiece, best quality, "
            default_negative_prompt = "lowres, bad anatomy, bad hands, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, blurry, "
            with gr.Column(variant="panel"):

                with gr.Tab("Bot Basic Config"):
                    db_bot_name = gr.Textbox(label="Name")
                    db_bot_api =  gr.Textbox(label="Bot API")
                    db_bot_log_channel = gr.Textbox(label="Log Channel")
                    db_bot_default_prompt =  gr.Textbox(label="[Default] Appended prompt to all requests", placeholder=default_prompt, default=default_prompt)
                    db_bot_default_negative_prompt = gr.Textbox(label="[Default] Appended Negative prompt to all requests", placeholder=default_negative_prompt, default=default_negative_prompt)

                with gr.Tab("Bot Command Config"):
                    with gr.Group():

                        with gr.Row():
                            gr.components.Dropdown(label="Default Model", choices=["ONE", "TWO"])

                        with gr.Row():
                            gr.components.Dropdown(label="Models", choices=["ONE", "TWO"])
                            #add button to add to allowlist if not in allowlist
                            gr.components.Button(value="Add to allowlist")
                            gr.components.Dropdown(label="AllowList", choices=["ONE", "TWO"])
                            gr.components.Button(value="Remove from allowlist")
                            
                    with gr.Group():
                        with gr.Row():
                            gr.Textbox(label="Custom command")
                            gr.Textbox(label="Description")
                        with gr.Row():
                            gr.Textbox(label="Positive prompt")
                            gr.Textbox(label="Negative prompt")
                        with gr.Row():
                            gr.components.Button(value="Add command")

                    with gr.Group():
                        with gr.Row():
                            gr.components.Dropdown(label="Custom Command", choices=["ONE", "TWO"])
                            gr.components.Button(value="Remove command")
                        with gr.Row():
                            gr.Textbox(label="Command Definition", interactive=False)

                with gr.Tab("Default Generation Params"):
                    with gr.Row():
                        gr.components.Slider(label="Number Of Steps", minimum=1, maximum=50, step=1, value=28, interactive=True)
                        gr.components.Slider(label="[BOT USER CONFIG] MAX Number Of Steps", minimum=1, maximum=50, step=1, value=28, interactive=True)
                        gr.components.Checkbox(label="Allow Bot User Config")
                    with gr.Row():
                        gr.components.Slider(label="Number Of Images", minimum=1, maximum=50, step=1, value=1, interactive=True)
                        gr.components.Slider(label="[BOT USER CONFIG] MAX Number Of Images", min=1, max=50, value=1,interactive=True)
                        gr.components.Checkbox(label="Allow Bot User Config")
                
                    with gr.Row():
                        gr.HTML(value="<p>Allowed Image Sizes</p>")
                        gr.Checkbox(label="256x256")

                        gr.Checkbox(label="512x256")
                        gr.Checkbox(label="256x512")

                        gr.Checkbox(label="512x512")

                        gr.Checkbox(label="768x512")
                        gr.Checkbox(label="512x768")
                    



    return (telegram_interface, "Telegram Bot", "telegram_interface"),


def polling_callback():
    print("POLLING CALLBACK!!!")


script_callbacks.on_polling(polling_callback)

script_callbacks.on_ui_tabs(on_ui_tabs)

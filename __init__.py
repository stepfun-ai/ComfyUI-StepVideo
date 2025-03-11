import os
import torch
from torchvision.io import read_video
from PIL import Image


def save_hwc_tensor_as_png(tensor, filename):
    # 确保张量在CPU且无梯度，并转换为HWC格式的NumPy数组
    np_array = tensor.detach().cpu().numpy()
    # 缩放值域并转换为uint8
    np_array = (np_array * 255).astype('uint8')
    # 使用PIL保存图像
    Image.fromarray(np_array).save(filename)


class TI2V:
    CATEGORY = "StepVideo"
    
    @classmethod    
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_input": ("IMAGE",),
                "remote_server_url": ("STRING", {
                    "multiline": False,
                    "default": "127.0.0.1",
                    "lazy": True
                }),
                "model_dir": ("STRING", {
                    "multiline": False,
                    "default": "models/diffusion_models",
                    "lazy": True
                }),
                "infer_steps": ("INT", {
                    "default": 15, 
                    "min": 0, #Minimum value
                    "max": 50, #Maximum value
                    "step": 1, #Slider's step
                    "display": "number", # Cosmetic only: display as "number" or "slider"
                    # "lazy": True # Will only be evaluated if check_lazy_status requires it
                }),
                "cfg_scale": ("FLOAT", {
                    "default": 5.0,
                    "min": 0.0,
                    "max": 20.0,
                    "step": 0.1,
                    # "round": 0.001, #The value representing the precision to round to, will be set to the step value by default. Can be set to False to disable rounding.
                    "display": "number",
                    # "lazy": True
                }),
                "time_shift": ("FLOAT", {
                    "default": 17.0,
                    "min": 0.0,
                    "max": 50.0,
                    "step": 0.1,
                    # "round": 0.001, #The value representing the precision to round to, will be set to the step value by default. Can be set to False to disable rounding.
                    "display": "number",
                    # "lazy": True
                }),
                "num_frames": ("INT", {
                    "default": 51, 
                    "min": 0, #Minimum value
                    "max": 100, #Maximum value
                    "step": 1, #Slider's step
                    "display": "number", # Cosmetic only: display as "number" or "slider"
                    # "lazy": True # Will only be evaluated if check_lazy_status requires it
                }),
                "text_prompt": ("STRING", {
                    "multiline": True,
                    "default": "笑起来",
                    "lazy": True
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "ti2v"

    def ti2v(self, image_input, remote_server_url, model_dir, infer_steps, cfg_scale, time_shift, num_frames, text_prompt):
        script_dir = 'custom_nodes/ComfyUI-StepVideo/Step-Video-TI2V'
        os.makedirs(f'{script_dir}/results', exist_ok=True)
        
        task_name = text_prompt[:50]
        save_hwc_tensor_as_png(image_input[0], f'{script_dir}/results/{task_name}_img.png')

        parallel = 4 #

        command = f'cd {script_dir} && torchrun --nproc_per_node {parallel} run_parallel.py --model_dir {model_dir} --vae_url {remote_server_url} --caption_url {remote_server_url}  --ulysses_degree {parallel} --first_image_path results/{task_name}_img.png --prompt "{text_prompt}" --infer_steps {infer_steps}  --cfg_scale {cfg_scale} --time_shift {time_shift} --num_frames {num_frames} --output_file_name {task_name}_vid'
        os.system(command)

        video_path = f'{script_dir}/results/{task_name}_vid-comfyui.mp4'
        # 读取视频文件，返回形状为 (T, H, W, C) 的uint8张量
        video, _, _ = read_video(video_path, pts_unit="sec")  # 默认output_format="THWC"
        # 转换为浮点张量并归一化到0~1范围
        video_tensor = video.to(torch.float32) / 255.0

        return (video_tensor,)


NODE_CLASS_MAPPINGS = {
    "TI2V" : TI2V,
}

# Optionally, you can rename the node in the `NODE_DISPLAY_NAME_MAPPINGS` dictionary.
NODE_DISPLAY_NAME_MAPPINGS = {
    "TI2V": "TI2V",
}
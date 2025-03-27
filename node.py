import os
import torch
import time
import json
from torchvision.io import read_video
from PIL import Image
import requests
import base64
from tqdm import tqdm


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
                    "default": "",
                    "lazy": True
                }),
                "script_dir": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "lazy": True
                }),
                "infer_steps": ("INT", {
                    "default": 50, 
                    "min": 0, #Minimum value
                    "max": 100, #Maximum value
                    "step": 1, #Slider's step
                    "display": "number", # Cosmetic only: display as "number" or "slider"
                    # "lazy": True # Will only be evaluated if check_lazy_status requires it
                }),
                "cfg_scale": ("FLOAT", {
                    "default": 9,
                    "min": 0.0,
                    "max": 50.0,
                    "step": 0.1,
                    # "round": 0.001, #The value representing the precision to round to, will be set to the step value by default. Can be set to False to disable rounding.
                    "display": "number",
                    # "lazy": True
                }),
                "time_shift": ("FLOAT", {
                    "default": 13.0,
                    "min": 0.0,
                    "max": 50.0,
                    "step": 0.1,
                    # "round": 0.001, #The value representing the precision to round to, will be set to the step value by default. Can be set to False to disable rounding.
                    "display": "number",
                    # "lazy": True
                }),
                "num_frames": ("INT", {
                    "default": 102, 
                    "min": 0, #Minimum value
                    "max": 204, #Maximum value
                    "step": 1, #Slider's step
                    "display": "number", # Cosmetic only: display as "number" or "slider"
                    # "lazy": True # Will only be evaluated if check_lazy_status requires it
                }),
                "motion_score": ("FLOAT", {
                    "default": 5,
                    "min": 0.0,
                    "max": 50.0,
                    "step": 0.1,
                    # "round": 0.001, #The value representing the precision to round to, will be set to the step value by default. Can be set to False to disable rounding.
                    "display": "number",
                    # "lazy": True
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

    def ti2v(self, image_input, remote_server_url, model_dir, script_dir, infer_steps, cfg_scale, time_shift, num_frames, motion_score, text_prompt):
        os.makedirs(f'{script_dir}/results', exist_ok=True)
        
        task_name = text_prompt[:50]
        save_hwc_tensor_as_png(image_input[0], f'{script_dir}/results/{task_name}_img.png')

        parallel = 1 # or parallel = 8

        command = f'cd {script_dir} && torchrun --nproc_per_node {parallel} run_parallel.py --model_dir {model_dir} --vae_url {remote_server_url} --caption_url {remote_server_url}  --ulysses_degree {parallel} --first_image_path results/{task_name}_img.png --prompt "{text_prompt}" --infer_steps {infer_steps}  --cfg_scale {cfg_scale} --time_shift {time_shift} --num_frames {num_frames} --output_file_name {task_name}_vid --motion_score {motion_score} --name_suffix comfyui'
        os.system(command)

        video_path = f'{script_dir}/results/{task_name}_vid-comfyui.mp4'
        # 读取视频文件，返回形状为 (T, H, W, C) 的uint8张量
        video, _, _ = read_video(video_path, pts_unit="sec")  # 默认output_format="THWC"
        # 转换为浮点张量并归一化到0~1范围
        video_tensor = video.to(torch.float32) / 255.0

        return (video_tensor,)


class TI2V_API:
    CATEGORY = "StepVideo"
    
    @classmethod    
    def INPUT_TYPES(s):
        return {
            "required": {
                "image_input": ("IMAGE",),
                "api_url": ("STRING", {
                    "multiline": False,
                    "default": "https://api.stepfun.com/v1/video/generations",
                    "lazy": True
                }),
                "api_key": ("STRING", {
                    "multiline": False,
                    "default": "",
                    "lazy": True
                }),
                "video_size": (['960x540', '544x992', '768x768'], {"default": '960x540'}),
                "text_prompt": ("STRING", {
                    "multiline": True,
                    "default": "笑起来",
                    "lazy": True
                }),
            }
        }
    
    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "ti2v"


    def download_video(self, url, save_path=None, chunk_size=1024):
        """
        下载视频文件到本地
        
        参数:
        url (str): 视频URL
        save_path (str): 保存路径（可选）
        chunk_size (int): 下载块大小（默认1024字节）
        
        返回:
        str: 最终保存路径
        """
        try:
            # 设置默认保存路径
            if not save_path:
                filename = url.split("/")[-1].split("?")[0]  # 从URL提取文件名
                save_path = os.path.join(os.getcwd(), filename)

            # 创建请求头（模拟浏览器）
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }

            # 发起带流式传输的GET请求
            response = requests.get(url, headers=headers, stream=True)
            response.raise_for_status()  # 检查HTTP错误

            # 获取文件总大小（字节）
            total_size = int(response.headers.get('content-length', 0))

            # 创建进度条
            progress = tqdm(
                total=total_size, 
                unit='B', 
                unit_scale=True,
                desc=f"Downloading {os.path.basename(save_path)}"
            )

            # 写入文件
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # 过滤保持连接的空白块
                        f.write(chunk)
                        progress.update(len(chunk))
            progress.close()

            # 验证文件大小
            if total_size != 0 and progress.n != total_size:
                raise RuntimeError("下载不完整，请重试")

            return save_path

        except requests.exceptions.RequestException as e:
            print(f"下载失败: {str(e)}")
            if os.path.exists(save_path):
                os.remove(save_path)  # 删除不完整文件
            return None
        except Exception as e:
            print(f"发生未知错误: {str(e)}")
            return None


    def ti2v(self, image_input, api_url, api_key, video_size, text_prompt):
        task_dir = 'output'
        os.makedirs(f'{task_dir}', exist_ok=True)
        
        # 准备图片
        task_name = text_prompt[:50]
        img_path = f'{task_dir}/{task_name}_img.png'
        save_hwc_tensor_as_png(image_input[0], img_path)

        # 请求内容
        with open(img_path, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode('utf-8')
            image_b64 = f"data:image/png;base64,{encoded}"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "step-video",
            "image_b64": image_b64,
            "prompt": text_prompt,
            'size': video_size,
        }

        # 上传请求
        response_post = requests.post(
            api_url,
            headers=headers,
            json=payload,
        )
        print(f'{response_post.content=}')


        # 获取生成任务 task_id
        response = json.loads(response_post.content)
        if response['status'] == 'fail':
            raise Exception('generation failed')
        else:
            task_id = response['task_id']

        # 等待视频生成
        while True:
            response_get = requests.get(
                f"{api_url}/{task_id}",
                headers=headers,
            )
            print(f'{response_get.content=}')
            response = json.loads(response_get.content)
            
            if response['status'] == 'fail':
                raise Exception('generation failed')
            elif response['status'] == 'success':
                url = response['video']['url']
                break
            else:
                time.sleep(10)
        
        # 下载视频
        video_path = f'{task_dir}/{task_name}_vid.mp4'
        self.download_video(url, save_path=video_path)

        # 读取视频文件，返回形状为 (T, H, W, C) 的uint8张量
        video, _, _ = read_video(video_path, pts_unit="sec")  # 默认output_format="THWC"
        # 转换为浮点张量并归一化到0~1范围
        video_tensor = video.to(torch.float32) / 255.0

        return (video_tensor,)


NODE_CLASS_MAPPINGS = {
    "TI2V" : TI2V,
    "TI2V_API" : TI2V_API,
}

# Optionally, you can rename the node in the `NODE_DISPLAY_NAME_MAPPINGS` dictionary.
NODE_DISPLAY_NAME_MAPPINGS = {
    "TI2V": "TI2V",
    "TI2V_API": "TI2V_API",
}
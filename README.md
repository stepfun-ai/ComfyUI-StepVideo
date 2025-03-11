# ComfyUI-StepVideo

## TI2V
### Model Weights
Download the model weights from [this link](https://huggingface.co/stepfun-ai/stepvideo-ti2v).

### Install
```bash
cd ComfyUI/custom_nodes
git clone https://github.com/stepfun-ai/ComfyUI-StepVideo.git 
```

```bash
cd ComfyUI/custom_nodes/ComfyUI-StepVideo/Step-Video-TI2V
conda create -n stepvideo python=3.10
conda activate stepvideo
pip install -e .
```

### Inference
```bash
cd ComfyUI/custom_nodes/ComfyUI-StepVideo/Step-Video-TI2V
python api/call_remote_server.py --model_dir where_you_download_dir &  ## We assume you have more than 4 GPUs available. This command will return the URL for both the caption API and the VAE API. Please use the returned URL as "remote_server_url" parameter in the "TI2V" node.
```

```bash
cd ComfyUI
python main.py
```

## Todo
- [x] TI2V node
- [ ] T2V node
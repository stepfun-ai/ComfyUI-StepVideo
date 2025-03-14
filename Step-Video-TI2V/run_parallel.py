from stepvideo.diffusion.video_pipeline import StepVideoPipeline
import torch.distributed as dist
import torch
from stepvideo.config import parse_args
from stepvideo.parallel import initialize_parall_group, get_parallel_group
from stepvideo.utils import setup_seed


if __name__ == "__main__":
    args = parse_args()
    initialize_parall_group(ring_degree=args.ring_degree, ulysses_degree=args.ulysses_degree)
    
    local_rank = get_parallel_group().local_rank
    device = torch.device(f"cuda:{local_rank}")
    
    setup_seed(args.seed)
        
    pipeline = StepVideoPipeline.from_pretrained(args.model_dir).to(dtype=torch.bfloat16, device="cpu")

    pipeline.transformer = pipeline.transformer.to(device)
    pipeline.setup_pipeline(args)
    
    
    prompt = args.prompt
    videos = pipeline(
        prompt=prompt, 
        first_image=args.first_image_path,
        num_frames=args.num_frames, 
        height=args.height, 
        width=args.width,
        num_inference_steps = args.infer_steps,
        guidance_scale=args.cfg_scale,
        time_shift=args.time_shift,
        pos_magic=args.pos_magic,
        neg_magic=args.neg_magic,
        output_file_name=args.output_file_name,
        motion_score=args.motion_score
    )
    
    dist.destroy_process_group()
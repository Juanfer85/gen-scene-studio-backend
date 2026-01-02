"""
Kie.ai Unified Video Client
Supports multiple AI video generation models with configurable options.
"""
import os
import asyncio
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

log = logging.getLogger(__name__)
API_KEY = os.getenv("KIE_API_KEY", "")


class VideoModel(Enum):
    """Available video generation models"""
    # Tier 1: Premium Quality
    VEO_3 = "veo3"
    SORA_2_PRO = "sora-2-pro-text-to-video"
    
    # Tier 2: High Quality
    RUNWAY_GEN3 = "runway-gen3"
    KLING_V21_PRO = "kling/v2-1-pro"
    
    # Tier 3: Good Quality / Economical
    HAILUO_I2V = "hailuo/2-3-image-to-video-pro"
    BYTEDANCE_V1 = "bytedance/v1-pro-text-to-video"
    WAN_TURBO = "wan/2-2-a14b-text-to-video-turbo"
    WAN_26 = "wan/2-6-text-to-video"  # Most economic option that works!


@dataclass
class ModelConfig:
    """Configuration for each video model"""
    name: str
    display_name: str
    api_endpoint: str
    max_duration: int  # seconds
    resolutions: List[str]
    aspect_ratios: List[str]
    supports_image_to_video: bool
    supports_video_extension: bool
    credits_per_5s: int  # Estimated credits
    tier: int  # 1=Premium, 2=High, 3=Economy


# Model configurations
MODEL_CONFIGS: Dict[str, ModelConfig] = {
    VideoModel.VEO_3.value: ModelConfig(
        name="veo3",
        display_name="Google Veo 3.1",
        api_endpoint="/api/v1/veo/generate",
        max_duration=8,
        resolutions=["720p", "1080p"],
        aspect_ratios=["16:9", "9:16", "1:1"],
        supports_image_to_video=True,
        supports_video_extension=False,
        credits_per_5s=350,
        tier=1
    ),
    VideoModel.SORA_2_PRO.value: ModelConfig(
        name="sora-2-pro-text-to-video",
        display_name="OpenAI Sora 2 Pro",
        api_endpoint="/api/v1/jobs/createTask",
        max_duration=20,
        resolutions=["low", "medium", "high"],
        aspect_ratios=["landscape", "portrait", "square"],
        supports_image_to_video=False,
        supports_video_extension=False,
        credits_per_5s=400,
        tier=1
    ),
    VideoModel.RUNWAY_GEN3.value: ModelConfig(
        name="runway-gen3",
        display_name="Runway Gen-3 Alpha",
        api_endpoint="/api/v1/runway/generate",
        max_duration=10,
        resolutions=["720p", "1080p"],
        aspect_ratios=["16:9", "9:16", "1:1", "4:3", "3:4"],
        supports_image_to_video=True,
        supports_video_extension=True,
        credits_per_5s=200,
        tier=2
    ),
    VideoModel.KLING_V21_PRO.value: ModelConfig(
        name="kling/v2-1-pro",
        display_name="Kling v2.1 Pro",
        api_endpoint="/api/v1/jobs/createTask",
        max_duration=10,
        resolutions=["720p", "1080p"],
        aspect_ratios=["16:9", "9:16", "1:1"],
        supports_image_to_video=True,
        supports_video_extension=False,
        credits_per_5s=250,
        tier=2
    ),
    VideoModel.HAILUO_I2V.value: ModelConfig(
        name="hailuo/2-3-image-to-video-pro",
        display_name="Hailuo Image-to-Video",
        api_endpoint="/api/v1/jobs/createTask",
        max_duration=6,
        resolutions=["768P"],
        aspect_ratios=["16:9", "9:16"],
        supports_image_to_video=True,
        supports_video_extension=False,
        credits_per_5s=180,
        tier=3
    ),
    VideoModel.BYTEDANCE_V1.value: ModelConfig(
        name="bytedance/v1-pro-text-to-video",
        display_name="Bytedance (TikTok)",
        api_endpoint="/api/v1/jobs/createTask",
        max_duration=5,
        resolutions=["720p"],
        aspect_ratios=["16:9", "9:16"],
        supports_image_to_video=False,
        supports_video_extension=False,
        credits_per_5s=150,
        tier=3
    ),
    VideoModel.WAN_TURBO.value: ModelConfig(
        name="wan/2-2-a14b-text-to-video-turbo",
        display_name="Wan Turbo (Alibaba)",
        api_endpoint="/api/v1/jobs/createTask",
        max_duration=5,
        resolutions=["720p"],
        aspect_ratios=["16:9", "9:16"],
        supports_image_to_video=False,
        supports_video_extension=False,
        credits_per_5s=120,
        tier=3
    ),
    VideoModel.WAN_26.value: ModelConfig(
        name="wan/2-6-text-to-video",
        display_name="Wan 2.6 (Best Value)",
        api_endpoint="/api/v1/jobs/createTask",
        max_duration=10,
        resolutions=["720p", "1080p"],
        aspect_ratios=["16:9", "9:16", "1:1"],
        supports_image_to_video=True,
        supports_video_extension=False,
        credits_per_5s=60,  # ~12 credits/second
        tier=3
    ),
}


def get_model_config(model: str) -> ModelConfig:
    """Get configuration for a model"""
    if model in MODEL_CONFIGS:
        return MODEL_CONFIGS[model]
    # Default to Runway if unknown
    return MODEL_CONFIGS[VideoModel.RUNWAY_GEN3.value]


def estimate_credits(model: str, duration_seconds: int) -> int:
    """Estimate credits needed for video generation"""
    config = get_model_config(model)
    # Calculate based on 5-second increments
    segments = (duration_seconds + 4) // 5  # Round up
    return config.credits_per_5s * segments


def get_available_models() -> List[Dict[str, Any]]:
    """Get list of available models with their info"""
    models = []
    for model_enum in VideoModel:
        config = MODEL_CONFIGS.get(model_enum.value)
        if config:
            models.append({
                "id": model_enum.value,
                "name": config.display_name,
                "max_duration": config.max_duration,
                "resolutions": config.resolutions,
                "aspect_ratios": config.aspect_ratios,
                "supports_image_to_video": config.supports_image_to_video,
                "supports_video_extension": config.supports_video_extension,
                "credits_per_5s": config.credits_per_5s,
                "tier": config.tier
            })
    return sorted(models, key=lambda x: (x["tier"], x["credits_per_5s"]))


async def generate_video(
    *,
    prompt: str,
    model: str = VideoModel.RUNWAY_GEN3.value,
    duration: int = 5,
    quality: str = "720p",
    aspect_ratio: str = "9:16",  # Default to vertical for TikTok/Reels/Shorts
    image_url: Optional[str] = None,
    negative_prompt: str = "",
    seed: Optional[int] = None
) -> Optional[str]:
    """
    Generate video using specified model.
    
    Args:
        prompt: Text description of the video
        model: Model identifier (use VideoModel enum values)
        duration: Video duration in seconds
        quality: Video quality/resolution
        aspect_ratio: Video aspect ratio
        image_url: Optional image URL for image-to-video
        negative_prompt: What to avoid in the video
        seed: Random seed for reproducibility
    
    Returns:
        URL of the generated video, or None if failed
    """
    if not API_KEY or len(API_KEY) < 10:
        log.warning("⚠️ KIE_API_KEY not configured")
        return None
    
    config = get_model_config(model)
    log.info(f"🎬 Generating video with {config.display_name}")
    log.info(f"   Prompt: {prompt[:80]}...")
    log.info(f"   Duration: {duration}s, Quality: {quality}, Aspect: {aspect_ratio}")
    
    try:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Build payload based on model type
        payload = _build_payload(model, config, prompt, duration, quality, aspect_ratio, image_url, negative_prompt, seed)
        
        timeout = aiohttp.ClientTimeout(total=600)  # 10 min max
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            # Create task
            api_url = f"https://api.kie.ai{config.api_endpoint}"
            log.info(f"   Calling: {api_url}")
            
            async with session.post(api_url, headers=headers, json=payload) as response:
                if response.status != 200:
                    error_text = await response.text()
                    log.error(f"❌ API error: {response.status} - {error_text}")
                    return None
                
                data = await response.json()
                task_id = data.get("data", {}).get("taskId")
                
                if not task_id:
                    log.error("❌ No taskId in response")
                    return None
                
                log.info(f"⏳ Task created: {task_id}")
                
                # Poll for result
                result_url = await _poll_for_result(session, headers, model, config, task_id)
                return result_url
                
    except Exception as e:
        log.error(f"❌ Video generation error: {e}")
        return None


def _build_payload(
    model: str,
    config: ModelConfig,
    prompt: str,
    duration: int,
    quality: str,
    aspect_ratio: str,
    image_url: Optional[str],
    negative_prompt: str,
    seed: Optional[int]
) -> Dict[str, Any]:
    """Build API payload based on model type"""
    
    # Runway uses different API structure
    if model == VideoModel.RUNWAY_GEN3.value:
        payload = {
            "prompt": prompt,
            "duration": min(duration, 10),
            "quality": quality,
            "aspectRatio": aspect_ratio,
            "waterMark": ""
        }
        if image_url:
            payload["imageUrl"] = image_url
        return payload
    
    # Veo uses different structure
    if model == VideoModel.VEO_3.value:
        payload = {
            "prompt": prompt,
            "model": "veo3",
            "aspectRatio": aspect_ratio
        }
        if image_url:
            payload["imageUrls"] = [image_url]
        return payload
    
    # Market API models (Kling, Sora, Hailuo, Bytedance, Wan)
    # Use unified structure
    input_data: Dict[str, Any] = {"prompt": prompt}
    
    if model == VideoModel.SORA_2_PRO.value:
        # Map aspect ratio
        ar_map = {"16:9": "landscape", "9:16": "portrait", "1:1": "square"}
        input_data["aspect_ratio"] = ar_map.get(aspect_ratio, "landscape")
        input_data["n_frames"] = str(min(duration * 2, 20))  # Approximate
        input_data["size"] = "high" if quality in ["1080p", "high"] else "medium"
        input_data["remove_watermark"] = True
        
    elif model == VideoModel.KLING_V21_PRO.value:
        input_data["duration"] = str(min(duration, 10))
        if negative_prompt:
            input_data["negative_prompt"] = negative_prompt
        input_data["cfg_scale"] = 0.5
        if image_url:
            input_data["image_url"] = image_url
            
    elif model == VideoModel.HAILUO_I2V.value:
        input_data["duration"] = str(min(duration, 6))
        input_data["resolution"] = "768P"
        if image_url:
            input_data["image_url"] = image_url
        else:
            log.warning("Hailuo requires image_url for image-to-video")
            
    elif model == VideoModel.BYTEDANCE_V1.value:
        input_data["duration"] = str(min(duration, 5))
        input_data["resolution"] = quality
        input_data["aspect_ratio"] = aspect_ratio
        input_data["camera_fixed"] = False
        if seed:
            input_data["seed"] = seed
            
    elif model == VideoModel.WAN_TURBO.value:
        input_data["resolution"] = quality
        input_data["aspect_ratio"] = aspect_ratio
        input_data["enable_prompt_expansion"] = False
        if seed:
            input_data["seed"] = seed
            
    elif model == VideoModel.WAN_26.value:
        input_data["duration"] = str(min(duration, 10))
        input_data["resolution"] = quality
        input_data["aspect_ratio"] = aspect_ratio
        if image_url:
            input_data["image_url"] = image_url
        if seed:
            input_data["seed"] = seed
    
    return {
        "model": config.name,
        "input": input_data
    }


async def _poll_for_result(
    session,
    headers: Dict[str, str],
    model: str,
    config: ModelConfig,
    task_id: str
) -> Optional[str]:
    """Poll for video generation result"""
    
    # Determine polling endpoint based on model
    if model == VideoModel.RUNWAY_GEN3.value:
        poll_url = f"https://api.kie.ai/api/v1/runway/record-detail"
        params = {"taskId": task_id}
    elif model == VideoModel.VEO_3.value:
        poll_url = f"https://api.kie.ai/api/v1/veo/record-info"
        params = {"taskId": task_id}
    else:
        # Market API uses recordInfo endpoint (NOT getTask which returns 404)
        poll_url = f"https://api.kie.ai/api/v1/jobs/recordInfo"
        params = {"taskId": task_id}
    
    max_attempts = 60  # 10 minutes max
    wait_time = 10
    
    for attempt in range(max_attempts):
        await asyncio.sleep(wait_time)
        log.info(f"   Polling {attempt + 1}/{max_attempts}...")
        
        try:
            async with session.get(poll_url, headers=headers, params=params) as response:
                if response.status != 200:
                    log.warning(f"   Poll status: {response.status}")
                    continue
                    
                data = await response.json()
                result = _extract_video_url(model, data)
                
                if result == "pending":
                    continue
                elif result == "failed":
                    log.error("❌ Video generation failed")
                    return None
                elif result:
                    log.info(f"✅ Video generated: {result}")
                    return result
                    
        except Exception as e:
            log.warning(f"   Poll error: {e}")
            continue
    
    log.warning("⚠️ Video generation timed out")
    return None


def _extract_video_url(model: str, data: Dict[str, Any]) -> Optional[str]:
    """Extract video URL from API response"""
    
    if model == VideoModel.RUNWAY_GEN3.value:
        data_obj = data.get("data", {})
        state = data_obj.get("state", "")
        if state == "success":
            video_info = data_obj.get("videoInfo", {})
            return video_info.get("videoUrl")
        elif state in ["pending", "processing", "generating", "queueing", "wait", ""]:
            return "pending"
        elif state == "fail":
            return "failed"
            
    elif model == VideoModel.VEO_3.value:
        data_obj = data.get("data", {})
        status = data_obj.get("status", "")
        if status == "SUCCESS":
            return data_obj.get("response", {}).get("videoUrl")
        elif status in ["QUEUED", "PROCESSING", "PENDING", ""]:
            return "pending"
        elif status == "FAILED":
            return "failed"
            
    else:
        # Market API response (Bytedance, Wan, Kling, etc.)
        data_obj = data.get("data", {})
        state = data_obj.get("state", "")
        if state == "success":
            # Market API returns URL in resultJson field as JSON string
            result_json_str = data_obj.get("resultJson", "")
            if result_json_str:
                import json
                try:
                    result_json = json.loads(result_json_str)
                    result_urls = result_json.get("resultUrls", [])
                    if result_urls:
                        return result_urls[0]
                except:
                    pass
            # Fallback to output field
            output = data_obj.get("output", {})
            video_url = output.get("video_url") or output.get("videoUrl")
            if video_url:
                return video_url
            videos = output.get("videos", [])
            if videos:
                return videos[0].get("url")
        elif state in ["pending", "processing", "queued", "generating", ""]:
            return "pending"
        elif state in ["failed", "fail"]:
            return "failed"
    
    return "pending"


async def extend_video(
    *,
    task_id: str,
    prompt: str,
    quality: str = "720p"
) -> Optional[str]:
    """
    Extend a previously generated Runway video.
    Only works with Runway Gen-3 model.
    
    Args:
        task_id: Original video's task ID
        prompt: Description of what happens next
        quality: Video quality
    
    Returns:
        URL of the extended video, or None if failed
    """
    if not API_KEY:
        return None
    
    try:
        import aiohttp
        
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "taskId": task_id,
            "prompt": prompt,
            "quality": quality
        }
        
        timeout = aiohttp.ClientTimeout(total=600)
        
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.post(
                "https://api.kie.ai/api/v1/runway/extend",
                headers=headers,
                json=payload
            ) as response:
                if response.status != 200:
                    return None
                    
                data = await response.json()
                new_task_id = data.get("data", {}).get("taskId")
                
                if new_task_id:
                    config = get_model_config(VideoModel.RUNWAY_GEN3.value)
                    return await _poll_for_result(
                        session, headers, VideoModel.RUNWAY_GEN3.value, config, new_task_id
                    )
                    
    except Exception as e:
        log.error(f"Video extension error: {e}")
    
    return None

import os, asyncio, random
from tenacity import retry, wait_exponential, stop_after_attempt

API_KEY = os.getenv("KIE_API_KEY", "")

@retry(wait=wait_exponential(multiplier=0.5, min=0.5, max=4), stop=stop_after_attempt(2))
async def generate_image(*, prompt:str, negative:str, seed:int, aspect_ratio:str, quality:str, model:str) -> str:
    """Generate image using KIE AI API with fallback to Picsum"""

    # Si no hay API key válida, usar fallback
    if not API_KEY or len(API_KEY) < 10:
        await asyncio.sleep(random.uniform(0.2, 0.6))
        return f"https://picsum.photos/1080/1920?random={seed}"

    try:
        import aiohttp

        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        payload = {
            "prompt": prompt
        }

        timeout = aiohttp.ClientTimeout(total=15)  # Shorter timeout
        async with aiohttp.ClientSession(timeout=timeout) as session:
            print(f"🎨 Generating image with KIE AI: {prompt[:50]}...")

            async with session.post(
                f"https://api.kie.ai/api/v1/gpt4o-image/generate",
                headers=headers,
                json=payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    task_id = data.get("data", {}).get("taskId")

                    if task_id:
                        # Wait a short time and check if immediately ready
                        await asyncio.sleep(3)
                        async with session.get(
                            f"https://api.kie.ai/api/v1/gpt4o-image/result/{task_id}",
                            headers=headers
                        ) as result_response:
                            if result_response.status == 200:
                                result_data = await result_response.json()
                                image_url = result_data.get("data", {}).get("imageUrl")
                                if image_url:
                                    print(f"✅ KIE AI image generated: {image_url}")
                                    return image_url

                # If we get here, KIE AI failed or is slow
                print(f"⚠️ KIE AI slow/failed (status: {response.status}), using fallback")
                await asyncio.sleep(random.uniform(0.2, 0.6))
                return f"https://picsum.photos/1080/1920?random={seed}"

    except Exception as e:
        print(f"❌ KIE AI exception: {str(e)}, using fallback")
        await asyncio.sleep(random.uniform(0.2, 0.6))
        return f"https://picsum.photos/1080/1920?random={seed}"
import json
import asyncio
from typing import AsyncGenerator, List, Dict, Any
from google import genai
from google.genai import types
from loguru import logger
from app.config import settings

class LLMService:
    def __init__(self):
        if settings.GOOGLE_API_KEY:
            self.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
            self.model_name = "gemma-4-26b-a4b-it"  # Using Gemma 4 26B via Gemini API
            self.system_instruction = (
                "You are a computational drug discovery assistant "
                "for neglected tropical diseases in ASEAN.\n"
                "Respond in clear language accessible to graduate researchers.\n"
                "Never make clinical claims. Always note computational limitations."
            )
        else:
            self.client = None
            logger.warning("GOOGLE_API_KEY not set. LLM synthesis will be unavailable.")

    async def generate_insight(self, ctx: Dict[str, Any]) -> str:
        if not self.client:
            return "Error: LLM Service not configured (Missing API Key)."
            
        prompt = f"""You are a drug discovery assistant for ASEAN NTD research.

Given this data:
{ctx.get('explanation_from_csv', 'N/A')}

Additional context:
- Lipinski status: {ctx.get('lipinski_status', 'N/A')}
- Ligand efficiency: {ctx.get('ligand_eff', 'N/A')}  
- Disease burden: {ctx.get('burden_description', 'N/A')}

Write a clear, 3-paragraph scientific explanation for a graduate researcher:
1. Why {ctx.get('target_name', 'this target')} matters as a drug target
2. Why this compound is promising (or its limitations)
3. Recommended next steps

Do not invent data. Only use what is provided above."""

        try:
            response = await self.client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    temperature=0.7,
    max_output_tokens=1024,
                )
            )
            return response.text
        except Exception as e:
            logger.error(f"LLM Insight Error: {e}")
            return f"Error generating insight: {str(e)}"

    async def generate_narrative_stream(
        self, target: Dict[str, Any], compounds: List[Dict[str, Any]]
    ) -> AsyncGenerator[str, None]:
        if not self.client:
            yield "data: [ERROR] LLM Service not configured (Missing API Key)\n\n"
            return

        prompt = self._build_prompt(target, compounds)
        
        try:
            # We must run the synchronous client generation inside asyncio.to_thread 
            # Or use async client if available, but to_thread is safer for this SDK wrapper prototype
            response_stream = await asyncio.to_thread(
                self.client.models.generate_content_stream,
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    thinking_config=types.ThinkingConfig(thinking_budget=-1)
                )
            )
            
            # The synchronous generator returned from to_thread can be tricky to iterate async.
            # Instead, we will exhaust the chunk stream in the thread, or better yet, 
            # since generate_content_stream returns an iterable generator, we can loop over it natively if the SDK supports it.
            # Usually `generate_content_stream` returns an iterator blocking object.
            # To iterate it asynchronously without blocking the event loop:
            
            def get_chunks():
                return list(self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=self.system_instruction,
                        thinking_config=types.ThinkingConfig(thinking_budget=-1)
                    )
                ))

            # Since streaming is usually expected to yield over time but the synchronous SDK generator 
            # blocks the event loop if we use `for chunk in iterator`, we can fetch chunks in pieces, 
            # but for simplification with asyncio.to_thread, we'll iterate with a non-blocking queue pattern or 
            # simply use the built-in async interface if available: `client.aio.models.generate_content_stream`.
            # Note: The new SDK officially has `.aio` for asyncio! Let's use it.
            
            response = await self.client.aio.models.generate_content_stream(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    system_instruction=self.system_instruction,
                    thinking_config=types.ThinkingConfig(thinking_budget=-1)
                )
            )

            async for chunk in response:
                if chunk.text:
                    # Strip any potential tags generated by the thought process if desired, or stream directly
                    yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"LLM Generation Error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

llm_service = LLMService()

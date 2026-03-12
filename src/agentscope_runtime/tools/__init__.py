# -*- coding: utf-8 -*-
from typing import Dict, Type, List

from pydantic import BaseModel, Field

from .base import Tool
from .generations.qwen_image_edit import (
    QwenImageEdit,
)
from .generations.qwen_image_generation import (
    QwenImageGen,
)
from .generations.qwen_text_to_speech import (
    QwenTextToSpeech,
)
from .generations.text_to_video import TextToVideo
from .generations.image_to_video import (
    ImageToVideo,
)
from .generations.speech_to_video import (
    SpeechToVideo,
)
from .searches.modelstudio_search_lite import (
    ModelstudioSearchLite,
)
from .generations.image_generation import (
    ImageGeneration,
)
from .generations.image_edit import ImageEdit
from .generations.image_style_repaint import (
    ImageStyleRepaint,
)
from .generations.speech_to_text import (
    SpeechToText,
)

from .generations.async_text_to_video import (
    TextToVideoSubmit,
    TextToVideoFetch,
)
from .generations.async_image_to_video import (
    ImageToVideoSubmit,
    ImageToVideoFetch,
)
from .generations.async_speech_to_video import (
    SpeechToVideoSubmit,
    SpeechToVideoFetch,
)
from .generations.async_image_to_video_wan25 import (
    ImageToVideoWan25Fetch,
    ImageToVideoWan25Submit,
)
from .generations.async_text_to_video_wan25 import (
    TextToVideoWan25Submit,
    TextToVideoWan25Fetch,
)
from .generations.image_edit_wan25 import (
    ImageEditWan25,
)
from .generations.image_generation_wan25 import (
    ImageGenerationWan25,
)


class McpServerMeta(BaseModel):
    instructions: str = Field(
        ...,
        description="Service description",
    )
    components: List[Type[Tool]] = Field(
        ...,
        description="Component list",
    )


mcp_server_metas: Dict[str, McpServerMeta] = {
    "modelstudio_wan_image": McpServerMeta(
        instructions="Intelligent image generation service based on Wanxiang, providing high-quality image processing and editing",
        components=[ImageGeneration, ImageEdit, ImageStyleRepaint],
    ),
    "modelstudio_wan_video": McpServerMeta(
        instructions="AI video generation service based on Wanxiang, supporting text-to-video, image-to-video, and speech-to-video multimodal generation",
        components=[
            TextToVideoSubmit,
            TextToVideoFetch,
            ImageToVideoSubmit,
            ImageToVideoFetch,
            SpeechToVideoSubmit,
            SpeechToVideoFetch,
        ],
    ),
    "modelstudio_wan25_media": McpServerMeta(
        instructions="Image and video generation service based on Wanxiang 2.5",
        components=[
            ImageGenerationWan25,
            ImageEditWan25,
            TextToVideoWan25Submit,
            TextToVideoWan25Fetch,
            ImageToVideoWan25Submit,
            ImageToVideoWan25Fetch,
        ],
    ),
    "modelstudio_qwen_image": McpServerMeta(
        instructions="Intelligent image generation service based on Qwen, providing high-quality image processing and editing",
        components=[QwenImageGen, QwenImageEdit],
    ),
    "modelstudio_web_search": McpServerMeta(
        instructions="Real-time internet search service providing accurate and timely information retrieval",
        components=[ModelstudioSearchLite],
    ),
    "modelstudio_speech_to_text": McpServerMeta(
        instructions="Speech recognition service for audio files, supporting speech-to-text for multiple audio formats",
        components=[SpeechToText],
    ),
    "modelstudio_qwen_text_to_speech": McpServerMeta(
        instructions="Text-to-speech synthesis service based on Qwen, supporting multilingual speech synthesis",
        components=[QwenTextToSpeech],
    ),
}

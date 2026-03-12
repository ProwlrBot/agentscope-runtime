# -*- coding: utf-8 -*-
# pylint:disable=abstract-method, deprecated-module, wrong-import-order

import os
import uuid
from http import HTTPStatus
from typing import Any, Optional

from dashscope.aigc.video_synthesis import AioVideoSynthesis
from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field

from ..base import Tool
from ..utils.api_key_util import get_api_key, ApiNames
from ...engine.tracing import trace, TracingUtil


class TextToVideoSubmitInput(BaseModel):
    """
    Text to video generation input model
    """

    prompt: str = Field(
        ...,
        description="Positive prompt describing the desired elements and visual features in the generated video; automatically truncated beyond 800 characters",
    )
    negative_prompt: Optional[str] = Field(
        default=None,
        description="Negative prompt describing unwanted content in the video to constrain generation; automatically truncated beyond 500 characters",
    )
    size: Optional[str] = Field(
        default=None,
        description="Video resolution; not set by default",
    )
    duration: Optional[int] = Field(
        default=None,
        description="Video generation duration in seconds",
    )
    prompt_extend: Optional[bool] = Field(
        default=None,
        description="Whether to enable smart prompt rewriting; when enabled, a large model rewrites the input prompt",
    )
    watermark: Optional[bool] = Field(
        default=None,
        description="Whether to add a watermark; not set by default",
    )
    ctx: Optional[Context] = Field(
        default=None,
        description="HTTP request context containing headers for mcp only, "
        "don't generate it",
    )


class TextToVideoSubmitOutput(BaseModel):
    """
    Text to video generation output model
    """

    task_id: str = Field(
        title="Task ID",
        description="Video generation task ID",
    )

    task_status: str = Field(
        title="Task Status",
        description="Video generation task status. PENDING: task queued, RUNNING: task processing, SUCCEEDED: task completed successfully, "
        "FAILED: task failed, CANCELED: task canceled, UNKNOWN: task does not exist or status unknown",
    )

    request_id: Optional[str] = Field(
        default=None,
        title="Request ID",
        description="Request ID",
    )


class TextToVideoSubmit(
    Tool[TextToVideoSubmitInput, TextToVideoSubmitOutput],
):
    """
    Text to video generation service that converts text into videos
    using DashScope's VideoSynthesis API.
    """

    name: str = "modelstudio_text_to_video_submit_task"
    description: str = (
        "Wanxiang text-to-video async task submission tool. Generates 5-second silent videos from text, supporting 480P, 720P, and 1080P resolutions "
        "with multiple size options per tier to accommodate different use cases."
    )

    @trace(trace_type="AIGC", trace_name="text_to_video_submit")
    async def arun(
        self,
        args: TextToVideoSubmitInput,
        **kwargs: Any,
    ) -> TextToVideoSubmitOutput:
        """
        Generate video from text prompt using DashScope VideoSynthesis

        This method wraps DashScope's VideoSynthesis service to generate videos
        based on text descriptions. It uses async call pattern for better
        performance and supports polling for task completion.

        Args:
            args: TextToVideoInput containing optional parameters
            **kwargs: Additional keyword arguments including:
                - request_id: Optional request ID for tracking
                - model_name: Model name to use (defaults to wan2.2-t2v-plus)
                - api_key: DashScope API key for authentication

        Returns:
            TextToVideoOutput containing the generated video URL and request ID

        Raises:
            ValueError: If DASHSCOPE_API_KEY is not set or invalid
            TimeoutError: If video generation takes too long
            RuntimeError: If video generation fails
        """
        trace_event = kwargs.pop("trace_event", None)
        request_id = TracingUtil.get_request_id()

        try:
            api_key = get_api_key(ApiNames.dashscope_api_key, **kwargs)
        except AssertionError as e:
            raise ValueError("Please set valid DASHSCOPE_API_KEY!") from e

        model_name = kwargs.get(
            "model_name",
            os.getenv("TEXT_TO_VIDEO_MODEL_NAME", "wan2.2-t2v-plus"),
        )

        parameters = {}
        if args.prompt_extend is not None:
            parameters["prompt_extend"] = args.prompt_extend
        if args.size:
            parameters["size"] = args.size
        if args.duration is not None:
            parameters["duration"] = args.duration
        if args.watermark is not None:
            parameters["watermark"] = args.watermark

        # Create AioVideoSynthesis instance
        aio_video_synthesis = AioVideoSynthesis()

        # Submit async task
        response = await aio_video_synthesis.async_call(
            model=model_name,
            api_key=api_key,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            **parameters,
        )
        # Log trace event if provided
        if trace_event:
            trace_event.on_log(
                "",
                **{
                    "step_suffix": "results",
                    "payload": {
                        "request_id": request_id,
                        "submit_task": response,
                    },
                },
            )

        if (
            response.status_code != HTTPStatus.OK
            or not response.output
            or response.output.task_status in ["FAILED", "CANCELED"]
        ):
            raise RuntimeError(f"Failed to submit task: {response}")

        if not request_id:
            request_id = (
                response.request_id
                if response.request_id
                else str(uuid.uuid4())
            )

        result = TextToVideoSubmitOutput(
            request_id=request_id,
            task_id=response.output.task_id,
            task_status=response.output.task_status,
        )
        return result


class TextToVideoFetchInput(BaseModel):
    """
    Text to video fetch task input model
    """

    task_id: str = Field(
        title="Task ID",
        description="Video generation task ID",
    )
    ctx: Optional[Context] = Field(
        default=None,
        description="HTTP request context containing headers for mcp only, "
        "don't generate it",
    )


class TextToVideoFetchOutput(BaseModel):
    """
    Text to video fetch task output model
    """

    video_url: str = Field(
        title="Video URL",
        description="Output video URL",
    )

    task_id: str = Field(
        title="Task ID",
        description="Video generation task ID",
    )

    task_status: str = Field(
        title="Task Status",
        description="Video generation task status. PENDING: task queued, RUNNING: task processing, SUCCEEDED: task completed successfully, "
        "FAILED: task failed, CANCELED: task canceled, UNKNOWN: task does not exist or status unknown",
    )

    request_id: Optional[str] = Field(
        default=None,
        title="Request ID",
        description="Request ID",
    )


class TextToVideoFetch(
    Tool[TextToVideoFetchInput, TextToVideoFetchOutput],
):
    """
    Text to video fetch service that retrieves video generation results
    using DashScope's VideoSynthesis API.
    """

    name: str = "modelstudio_text_to_video_fetch_result"
    description: str = "Wanxiang text-to-video async task result query tool; retrieves task results by Task ID."

    @trace(trace_type="AIGC", trace_name="text_to_video_fetch")
    async def arun(
        self,
        args: TextToVideoFetchInput,
        **kwargs: Any,
    ) -> TextToVideoFetchOutput:
        """
        Fetch video generation result using DashScope VideoSynthesis

        This method wraps DashScope's VideoSynthesis fetch service to retrieve
        video generation results based on task ID. It uses async call pattern
        for better performance.

        Args:
            args: TextToVideoFetchInput containing task_id parameter
            **kwargs: Additional keyword arguments including:
                - api_key: DashScope API key for authentication

        Returns:
            TextToVideoFetchOutput containing the video URL, task status and
            request ID

        Raises:
            ValueError: If DASHSCOPE_API_KEY is not set or invalid
            RuntimeError: If video fetch fails or response status is not OK
        """
        trace_event = kwargs.pop("trace_event", None)
        request_id = TracingUtil.get_request_id()

        try:
            api_key = get_api_key(ApiNames.dashscope_api_key, **kwargs)
        except AssertionError as e:
            raise ValueError("Please set valid DASHSCOPE_API_KEY!") from e

        # Create AioVideoSynthesis instance
        aio_video_synthesis = AioVideoSynthesis()

        response = await aio_video_synthesis.fetch(
            api_key=api_key,
            task=args.task_id,
        )

        # Log trace event if provided
        if trace_event:
            trace_event.on_log(
                "",
                **{
                    "step_suffix": "results",
                    "payload": {
                        "request_id": response.request_id,
                        "fetch_result": response,
                    },
                },
            )

        if (
            response.status_code != HTTPStatus.OK
            or not response.output
            or response.output.task_status in ["FAILED", "CANCELED"]
        ):
            raise RuntimeError(f"Failed to fetch result: {response}")

        # Handle request ID
        if not request_id:
            request_id = (
                response.request_id
                if response.request_id
                else str(uuid.uuid4())
            )

        result = TextToVideoFetchOutput(
            video_url=response.output.video_url,
            task_id=response.output.task_id,
            task_status=response.output.task_status,
            request_id=request_id,
        )

        return result

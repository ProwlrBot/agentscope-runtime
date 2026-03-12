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


class ImageToVideoSubmitInput(BaseModel):
    """
    Input model for image-to-video generation submission.

    This model defines the input parameters required for submitting an
    image-to-video generation task to the DashScope API.
    """

    image_url: str = Field(
        ...,
        description="Input image; supports public URL, Base64 encoding, or local file path",
    )
    prompt: Optional[str] = Field(
        default=None,
        description="Positive prompt describing the desired elements and visual features in the generated video",
    )
    negative_prompt: Optional[str] = Field(
        default=None,
        description="Negative prompt describing unwanted content in the video to constrain generation",
    )
    template: Optional[str] = Field(
        default=None,
        description="Video effect template. Options: squish, flying (magic floating), carousel (time carousel), etc.",
    )
    resolution: Optional[str] = Field(
        default=None,
        description="Video resolution; not set by default",
    )
    duration: Optional[int] = Field(
        default=None,
        description="Video generation duration in seconds, typically 5 seconds",
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


class ImageToVideoSubmitOutput(BaseModel):
    """
    Output model for image-to-video generation submission.

    This model contains the response data after successfully submitting
    an image-to-video generation task.
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


class ImageToVideoSubmit(
    Tool[ImageToVideoSubmitInput, ImageToVideoSubmitOutput],
):
    """
    Service for submitting image-to-video generation tasks.

    This Tool provides functionality to submit asynchronous
    image-to-video generation tasks using DashScope's VideoSynthesis API.
    It supports various video effects and customization options.
    """

    name: str = "modelstudio_image_to_video_submit_task"
    description: str = (
        “Wanxiang image-to-video async task submission tool. Generates 5-second silent videos from a first-frame image and text prompt. “
        “Supports effect templates such as magic floating and balloon inflation, suitable for creative video production and entertainment effects.”
    )

    @trace(trace_type="AIGC", trace_name="image_to_video_submit")
    async def arun(
        self,
        args: ImageToVideoSubmitInput,
        **kwargs: Any,
    ) -> ImageToVideoSubmitOutput:
        """
        Submit an image-to-video generation task using DashScope API.

        This method asynchronously submits an image-to-video generation task
        to DashScope's VideoSynthesis service. It supports various video
        effects, resolution settings, and prompt enhancements.

        Args:
            args: ImageToVideoSubmitInput containing required image_url and
                  optional parameters for video generation
            **kwargs: Additional keyword arguments including:
                - request_id: Optional request ID for tracking
                - model_name: Model name (defaults to wan2.2-i2v-flash)
                - api_key: DashScope API key for authentication

        Returns:
            ImageToVideoSubmitOutput containing the task ID, current status,
            and request ID for tracking the submission

        Raises:
            ValueError: If DASHSCOPE_API_KEY is not set or invalid
            RuntimeError: If video generation submission fails
        """
        trace_event = kwargs.pop("trace_event", None)
        request_id = TracingUtil.get_request_id()

        try:
            api_key = get_api_key(ApiNames.dashscope_api_key, **kwargs)
        except AssertionError as e:
            raise ValueError("Please set valid DASHSCOPE_API_KEY!") from e

        model_name = kwargs.get(
            "model_name",
            os.getenv("IMAGE_TO_VIDEO_MODEL_NAME", "wan2.2-i2v-flash"),
        )

        parameters = {}
        if args.resolution:
            parameters["resolution"] = args.resolution
        if args.duration is not None:
            parameters["duration"] = args.duration
        if args.prompt_extend is not None:
            parameters["prompt_extend"] = args.prompt_extend
        if args.watermark is not None:
            parameters["watermark"] = args.watermark

        # Create AioVideoSynthesis instance
        aio_video_synthesis = AioVideoSynthesis()

        # Submit async task
        response = await aio_video_synthesis.async_call(
            model=model_name,
            api_key=api_key,
            img_url=args.image_url,
            prompt=args.prompt,
            negative_prompt=args.negative_prompt,
            template=args.template,
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

        result = ImageToVideoSubmitOutput(
            request_id=request_id,
            task_id=response.output.task_id,
            task_status=response.output.task_status,
        )
        return result


class ImageToVideoFetchInput(BaseModel):
    """
    Input model for fetching image-to-video generation results.

    This model defines the input parameters required for retrieving
    the status and results of a previously submitted video generation task.
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


class ImageToVideoFetchOutput(BaseModel):
    """
    Output model for fetching image-to-video generation results.

    This model contains the response data including video URL, task status,
    and other metadata after fetching a video generation task result.
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


class ImageToVideoFetch(
    Tool[ImageToVideoFetchInput, ImageToVideoFetchOutput],
):
    """
    Service for fetching image-to-video generation results.

    This Tool provides functionality to retrieve the status and
    results of asynchronous image-to-video generation tasks using
    DashScope's VideoSynthesis API.
    """

    name: str = "modelstudio_image_to_video_fetch_result"
    description: str = "Wanxiang image-to-video async task result query tool; retrieves task results by Task ID."

    @trace(trace_type="AIGC", trace_name="image_to_video_fetch")
    async def arun(
        self,
        args: ImageToVideoFetchInput,
        **kwargs: Any,
    ) -> ImageToVideoFetchOutput:
        """
        Fetch the results of an image-to-video generation task.

        This method asynchronously retrieves the status and results of a
        previously submitted image-to-video generation task using the
        task ID returned from the submission.

        Args:
            args: ImageToVideoFetchInput containing the task_id parameter
            **kwargs: Additional keyword arguments including:
                - api_key: DashScope API key for authentication

        Returns:
            ImageToVideoFetchOutput containing the video URL, current task
            status, and request ID

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

        result = ImageToVideoFetchOutput(
            video_url=response.output.video_url,
            task_id=response.output.task_id,
            task_status=response.output.task_status,
            request_id=request_id,
        )

        return result

# -*- coding: utf-8 -*-
# pylint:disable=abstract-method, deprecated-module, wrong-import-order
# pylint:disable=redefined-builtin

import asyncio
import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import Any, Optional

from dashscope.client.base_api import BaseAsyncApi
from dashscope.utils.oss_utils import check_and_upload_local
from mcp.server.fastmcp import Context
from pydantic import BaseModel, Field

from ..base import Tool
from ..utils.api_key_util import get_api_key, ApiNames
from ...engine.tracing import trace, TracingUtil


class ImageStyleRepaintInput(BaseModel):
    """
    Portrait Style Repaint Input
    """

    image_url: str = Field(
        ...,
        description="URL of the input image.",
    )

    style_index: int = Field(
        ...,
        description="Portrait style type index. Supported styles: -1: reference uploaded image style, "
        "0: retro comic, 1: 3D fairy tale, 2: anime, 3: fresh, 4: futuristic tech, "
        "5: Chinese ink painting, 6: warrior general, 7: colorful cartoon, 8: elegant Chinese style, 9: New Year celebration.",
    )

    style_ref_url: Optional[str] = Field(
        default=None,
        description="URL of the style reference image. Required when style_index is -1; " "not needed for other styles.",
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


class ImageStyleRepaintOutput(BaseModel):
    """
    Portrait Style Repaint Output
    """

    results: list[str] = Field(title="Results", description="List of output image URLs")
    request_id: Optional[str] = Field(
        default=None,
        title="Request ID",
        description="Request ID",
    )


class ImageStyleRepaint(
    Tool[ImageStyleRepaintInput, ImageStyleRepaintOutput],
):
    """
    Portrait Style Repaint
    """

    name: str = "modelstudio_image_style_repaint"
    description: str = "Portrait style repaint service. Input the original image and style data (index or reference image); returns the repainted image."

    def __init__(self, name: str = None, description: str = None):
        super().__init__(name=name, description=description)
        # Create thread pool to execute synchronous BaseAsyncApi calls
        self._executor = ThreadPoolExecutor(
            max_workers=10,
            thread_name_prefix="StyleRepaint",
        )

    @trace(trace_type="AIGC", trace_name="image_style_repaint")
    async def arun(
        self,
        args: ImageStyleRepaintInput,
        **kwargs: Any,
    ) -> ImageStyleRepaintOutput:
        """Modelstudio Image Style Repaint

        This method wrap DashScope's ImageStyleRepaint service to generate
        images based on image url and style index (or style reference image
        url).

        Args:
            args: ImageStyleRepaintInput containing the image_url,
                style_index, and style_ref_url.
            **kwargs: Additional keyword arguments including:
                - request_id: Optional request ID for tracking
                - trace_event: Optional trace event for logging
                - model_name: Model name to use (defaults to wanx2.1-t2i-turbo)
                - api_key: DashScope API key for authentication

        Returns:
            ImageStyleRepaintOutput containing the list of generated image
            URLs and request ID.

        Raises:
            ValueError: If DASHSCOPE_API_KEY is not set or invalid.
        """

        trace_event = kwargs.pop("trace_event", None)
        request_id = TracingUtil.get_request_id()

        try:
            api_key = get_api_key(ApiNames.dashscope_api_key, **kwargs)
        except AssertionError as e:
            raise ValueError("Please set valid DASHSCOPE_API_KEY!") from e

        model_name = kwargs.get(
            "model_name",
            os.getenv(
                "IMAGE_STYLE_REPAINT_MODEL_NAME",
                "wanx-style-repaint-v1",
            ),
        )

        has_uploaded = False

        image_url = args.image_url
        if args.image_url:
            uploaded, image_url, _ = check_and_upload_local(
                model=model_name,
                content=args.image_url,
                api_key=api_key,
            )
            has_uploaded = True if uploaded is True else has_uploaded

        style_ref_url = args.style_ref_url
        if args.style_ref_url:
            uploaded, style_ref_url = check_and_upload_local(
                model=model_name,
                content=args.style_ref_url,
                api_key=api_key,
            )
            has_uploaded = True if uploaded is True else has_uploaded

        kwargs = {}
        if has_uploaded is True:
            headers = {"X-DashScope-OssResourceResolve": "enable"}
            kwargs["headers"] = headers

        # 🔄 Put BaseAsyncApi.call into thread pool to avoid blocking
        # event loop
        def _sync_style_repaint_call() -> Any:
            input = {
                "image_url": image_url,
                "style_index": args.style_index,
                "style_ref_url": style_ref_url,
            }
            if args.watermark is not None:
                input["watermark"] = args.watermark
            return BaseAsyncApi.call(
                model=model_name,
                input=input,
                task_group="aigc",
                task="image-generation",
                function="generation",
                **kwargs,
            )

        # Execute synchronous calls asynchronously in thread pool
        res = await asyncio.get_event_loop().run_in_executor(
            self._executor,
            _sync_style_repaint_call,
        )

        if res.status_code != HTTPStatus.OK or not res.output:
            raise RuntimeError(f"Failed to generate image: {res}")

        if request_id == "":
            request_id = (
                res.request_id if res.request_id else str(uuid.uuid4())
            )

        if trace_event:
            trace_event.on_log(
                "",
                **{
                    "step_suffix": "results",
                    "payload": {
                        "request_id": request_id,
                        "image_query_result": res,
                    },
                },
            )

        results = []
        if res.status_code == HTTPStatus.OK:
            for result in res.output.get("results"):
                if result.get("url"):
                    results.append(result.get("url"))

        return ImageStyleRepaintOutput(results=results, request_id=request_id)

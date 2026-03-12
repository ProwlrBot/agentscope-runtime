# -*- coding: utf-8 -*-
# mypy: disable-error-code="no-redef"

import logging
from datetime import datetime
from typing import Any, Optional, Type

from pydantic import BaseModel, Field

from .base import (
    AP_RETURN_URL,
    AP_NOTIFY_URL,
    X_AGENT_CHANNEL,
    _create_alipay_client,
    AgentExtendParams,
)
from ..base import Tool

try:
    from alipay.aop.api.request.AlipayTradeWapPayRequest import (
        AlipayTradeWapPayRequest,
    )
    from alipay.aop.api.request.AlipayTradePagePayRequest import (
        AlipayTradePagePayRequest,
    )
    from alipay.aop.api.request.AlipayTradeQueryRequest import (
        AlipayTradeQueryRequest,
    )
    from alipay.aop.api.request.AlipayTradeRefundRequest import (
        AlipayTradeRefundRequest,
    )
    from alipay.aop.api.request.AlipayTradeFastpayRefundQueryRequest import (
        AlipayTradeFastpayRefundQueryRequest,
    )
    from alipay.aop.api.domain.AlipayTradePagePayModel import (
        AlipayTradePagePayModel,
    )
    from alipay.aop.api.domain.AlipayTradeWapPayModel import (
        AlipayTradeWapPayModel,
    )
    from alipay.aop.api.domain.AlipayTradeQueryModel import (
        AlipayTradeQueryModel,
    )
    from alipay.aop.api.domain.AlipayTradeRefundModel import (
        AlipayTradeRefundModel,
    )
    from alipay.aop.api.domain.AlipayTradeFastpayRefundQueryModel import (
        AlipayTradeFastpayRefundQueryModel,
    )
    from alipay.aop.api.response.AlipayTradeQueryResponse import (
        AlipayTradeQueryResponse,
    )
    from alipay.aop.api.response.AlipayTradeRefundResponse import (
        AlipayTradeRefundResponse,
    )
    from alipay.aop.api.response.AlipayTradeFastpayRefundQueryResponse import (
        AlipayTradeFastpayRefundQueryResponse,
    )

    ALIPAY_SDK_AVAILABLE = True
except ImportError:
    ALIPAY_SDK_AVAILABLE = False
    AlipayTradeWapPayRequest: Optional[Type[Any]] = None
    AlipayTradePagePayRequest: Optional[Type[Any]] = None
    AlipayTradeQueryRequest: Optional[Type[Any]] = None
    AlipayTradeRefundRequest: Optional[Type[Any]] = None
    AlipayTradeFastpayRefundQueryRequest: Optional[Type[Any]] = None
    AlipayTradePagePayModel: Optional[Type[Any]] = None
    AlipayTradeWapPayModel: Optional[Type[Any]] = None
    AlipayTradeQueryModel: Optional[Type[Any]] = None
    AlipayTradeRefundModel: Optional[Type[Any]] = None
    AlipayTradeFastpayRefundQueryModel: Optional[Type[Any]] = None
    AlipayTradeQueryResponse: Optional[Type[Any]] = None
    AlipayTradeRefundResponse: Optional[Type[Any]] = None
    AlipayTradeFastpayRefundQueryResponse: Optional[Type[Any]] = None


logger = logging.getLogger(__name__)


class MobilePaymentInput(BaseModel):
    """Mobile Alipay payment input schema."""

    out_trade_no: str = Field(
        ...,
        description="Order creation parameter - merchant order number",
    )
    order_title: str = Field(
        ...,
        description="Order title",
    )
    total_amount: float = Field(
        ...,
        gt=0,
        description="Payment amount in yuan",
    )


class WebPagePaymentInput(BaseModel):
    """Web page Alipay payment input schema."""

    out_trade_no: str = Field(
        ...,
        description="Order creation parameter - merchant order number",
    )
    order_title: str = Field(
        ...,
        description="Order title",
    )
    total_amount: float = Field(
        ...,
        gt=0,
        description="Payment amount in yuan",
    )


class PaymentQueryInput(BaseModel):
    """Payment query input schema."""

    out_trade_no: str = Field(
        ...,
        description="Merchant order number",
    )


class PaymentRefundInput(BaseModel):
    """Payment refund input schema."""

    out_trade_no: str = Field(
        ...,
        description="Merchant order number",
    )
    refund_amount: float = Field(
        ...,
        gt=0,
        description="Refund amount",
    )
    refund_reason: Optional[str] = Field(
        default=None,
        description="Refund reason",
    )
    out_request_no: Optional[str] = Field(
        default=None,
        description="Refund request number",
    )


class RefundQueryInput(BaseModel):
    """Refund query input schema."""

    out_trade_no: str = Field(
        ...,
        description="Merchant order number",
    )
    out_request_no: str = Field(
        ...,
        description="Refund request number",
    )


class PaymentOutput(BaseModel):
    """Payment operation output schema."""

    result: str = Field(
        ...,
        description="包含链接的 markdown 文本，" "你要将文本插入对话内容中。",
    )


class MobileAlipayPayment(Tool[MobilePaymentInput, PaymentOutput]):
    """
    Mobile Alipay Payment Component

    This component is used to create Alipay payment orders suitable for
    mobile clients. The generated payment link can be opened in a mobile
    browser to redirect users to the Alipay application for payment or
    complete payment directly in the browser.

    Key features:
    - Suitable for mobile websites and mobile applications
    - Supports in-app payment and in-browser payment via Alipay
    - Uses the QUICK_WAP_WAY product code
    - Returns a ready-to-use payment link

    Input type: MobilePaymentInput
    Output type: PaymentOutput

    Usage scenarios:
    - Mobile website payment
    - Embedded mobile App payment

"""

    name: str = "alipay_mobile_payment"
    description: str = (
        "创建一笔支付宝订单，返回带有支付链接的 Markdown 文本，"
        "该链接在手机浏览器中打开后可跳转到支付宝或直接在浏览器中支付。"
        "本工具适用于移动网站或移动 App。"
    )

    async def _arun(
        self,
        args: MobilePaymentInput,
        **kwargs: Any,
    ) -> PaymentOutput:
        """
        Create a mobile Alipay payment order.

        This method is used to create an Alipay payment order suitable for
        mobile browsers. The generated payment link can be opened in a
        mobile browser, and the user can complete the payment either in the
        Alipay app or within the browser.

        Args:
            args (MobilePaymentInput): Object containing payment parameters
                - out_trade_no: Merchant order number
                - order_title: Order title
                - total_amount: Payment amount (in yuan)
            **kwargs: Additional keyword arguments

        Returns:
            PaymentOutput: Markdown text output containing the payment link

        Raises:
            ValueError: If configuration parameters are incorrect
            ImportError: If Alipay SDK is not available
            Exception: For any other error during order creation

"""
        try:
            # Create an Alipay client instance
            alipay_client = _create_alipay_client()

            # Create the mobile payment model and set parameters
            model = AlipayTradeWapPayModel()
            model.out_trade_no = args.out_trade_no  # Merchant order number
            model.total_amount = str(args.total_amount)  # Amount as string
            model.subject = args.order_title  # Order title
            model.product_code = "QUICK_WAP_WAY"  # Fixed product code

            # Use custom extend parameters
            extend_params = AgentExtendParams()
            extend_params.request_channel_source = X_AGENT_CHANNEL
            model.extend_params = extend_params

            # Create the mobile payment request
            request = AlipayTradeWapPayRequest(biz_model=model)

            # Set callback URL if configured
            if AP_RETURN_URL:
                request.return_url = AP_RETURN_URL
            if AP_NOTIFY_URL:
                request.notify_url = AP_NOTIFY_URL

            # Execute the request to get the payment link
            response = alipay_client.page_execute(request, http_method="GET")
            return PaymentOutput(
                result=f"Payment link: [Click to complete payment]({response})",
            )

        except (ValueError, ImportError) as e:
            # Configuration or SDK error, raise directly
            logger.error(f"Mobile payment configuration or SDK error: {str(e)}")
            raise
        except Exception as e:
            # Other exceptions, wrap and raise
            error_msg = f"Failed to create mobile payment order: {str(e)}"
            logger.error(f"Mobile payment execution error: {error_msg}")
            raise RuntimeError(error_msg) from e


class WebPageAlipayPayment(Tool[WebPagePaymentInput, PaymentOutput]):
    """
    Desktop Web Page Alipay Payment Component

    This component creates Alipay payment orders for desktop browsers.
    The generated payment link displays a QR code for users to scan
    with the Alipay app.

    Key features:
    - Suitable for desktop websites and desktop clients
    - Supports QR code scan payment
    - Uses FAST_INSTANT_TRADE_PAY product code
    - Returns a ready-to-use payment link

    Input type: WebPagePaymentInput
    Output type: PaymentOutput
    """

    name: str = "alipay_webpage_payment"
    description: str = (
        "创建一笔支付宝订单，返回带有支付链接的 Markdown 文本，"
        "该链接在电脑浏览器中打开后会展示支付二维码，用户可扫码支付。"
        "本工具适用于桌面网站或电脑客户端。"
    )

    async def _arun(
        self,
        args: WebPagePaymentInput,
        **kwargs: Any,
    ) -> PaymentOutput:
        """
        Create a desktop web page Alipay payment order.

        This method creates an Alipay payment order for desktop browsers.
        The generated payment link displays a QR code for users to scan
        with the Alipay app.

        Args:
            args (WebPagePaymentInput): Object containing payment parameters
                - out_trade_no: Merchant order number
                - order_title: Order title
                - total_amount: Payment amount (in yuan)
            **kwargs: Additional keyword arguments

        Returns:
            PaymentOutput: Markdown text output containing the payment link

        Raises:
            ValueError: If configuration parameters are incorrect
            ImportError: If Alipay SDK is unavailable
            Exception: For any other error during order creation
        """
        try:
            # Create Alipay client instance
            alipay_client = _create_alipay_client()

            # Create desktop web payment model and set parameters
            model = AlipayTradePagePayModel()
            model.out_trade_no = args.out_trade_no  # Merchant order number
            model.total_amount = str(
                args.total_amount,
            )  # Payment amount (converted to string)
            model.subject = args.order_title  # Order title
            model.product_code = "FAST_INSTANT_TRADE_PAY"  # Product code, fixed value

            # Use custom extend parameters class
            extend_params = AgentExtendParams()
            extend_params.request_channel_source = X_AGENT_CHANNEL
            model.extend_params = extend_params

            # Create desktop web payment request
            request = AlipayTradePagePayRequest(biz_model=model)

            # Set callback URL (if configured)
            if AP_RETURN_URL:
                request.return_url = AP_RETURN_URL
            if AP_NOTIFY_URL:
                request.notify_url = AP_NOTIFY_URL

            # Execute request to get payment link
            response = alipay_client.page_execute(request, http_method="GET")
            return PaymentOutput(
                result=f"Web payment link: [Click to complete payment]({response})",
            )

        except (ValueError, ImportError) as e:
            # Configuration or SDK error
            logger.error(
                f"Mobile payment configuration or SDK error: {str(e)}",
            )
            raise
        except Exception as e:
            # Wrap and raise other exceptions
            error_msg = f"Failed to create mobile payment order: {str(e)}"
            logger.error(f"Mobile payment execution exception: {error_msg}")
            raise RuntimeError(error_msg) from e


class AlipayPaymentQuery(Tool[PaymentQueryInput, PaymentOutput]):
    """
    Alipay Transaction Query Component

    This component is used to query the current status of an existing
    Alipay transaction order. It can obtain the payment status, transaction
    amount, Alipay transaction number, and other details.

    Key features:
    - Supports querying by merchant order number
    - Returns detailed transaction status information
    - Supports real-time queries
    - Includes error handling and logging

    Input type: PaymentQueryInput
    Output type: PaymentOutput

    Usage scenarios:
    - Query payment status of an order
    - Verify payment results
    - Synchronize order status
    - Confirm status after payment failure

"""

    name: str = "alipay_query_payment"
    description: str = "Query an Alipay order and return text with order information."

    async def _arun(
        self,
        args: PaymentQueryInput,
        **kwargs: Any,
    ) -> PaymentOutput:
        """
        Query Alipay transaction order status.

        This method queries an existing Alipay order's current status,
        including payment status, amount, and Alipay transaction number.

        Args:
            args (PaymentQueryInput): Object containing query parameters
                - out_trade_no: Merchant order number
            **kwargs: Additional keyword arguments

        Returns:
            PaymentOutput: Text output containing query result information

        Raises:
            ValueError: If configuration parameters are incorrect
            ImportError: If Alipay SDK is unavailable
            Exception: For any other query errors

"""
        try:
            # Create an Alipay client instance
            alipay_client = _create_alipay_client()

            # Create transaction query model
            model = AlipayTradeQueryModel()
            model.out_trade_no = args.out_trade_no  # Merchant order number

            # Set custom extended parameters
            extend_params = AgentExtendParams()
            extend_params.request_channel_source = X_AGENT_CHANNEL
            model.extend_params = extend_params

            # Create transaction query request
            request = AlipayTradeQueryRequest(biz_model=model)

            # Execute query request
            response_content = alipay_client.execute(request)
            response = AlipayTradeQueryResponse()
            response.parse_response_content(response_content)

            # Handle response results
            if response.is_success():  # Query success
                result = (
                    f"Transaction status: {response.trade_status}, "
                    f"Transaction amount: {response.total_amount}, "
                    f"Alipay transaction no: {response.trade_no}"
                )
                return PaymentOutput(result=result)
            else:  # Query failed
                return PaymentOutput(
                    result=f"Transaction query failed. Error: {response.msg}",
                )

        except (ValueError, ImportError) as e:
            # Configuration or SDK error
            logger.error(f"Order query configuration or SDK error: {str(e)}")
            raise
        except Exception as e:
            # Other exceptions with wrapped error message
            error_msg = f"Order query failed: {str(e)}"
            logger.error(f"Order query execution exception: {error_msg}")
            raise RuntimeError(error_msg) from e


class AlipayPaymentRefund(Tool[PaymentRefundInput, PaymentOutput]):
    """
    Alipay Transaction Refund Component

    This component initiates a refund request for a successfully paid
    Alipay transaction. It supports full and partial refunds as well as
    custom refund reasons.

    Key features:
    - Supports full and partial refunds
    - Allows specifying refund reasons
    - Idempotent refund requests when repeated

    Input type: PaymentRefundInput
    Output type: PaymentOutput

    Usage scenarios:
    - Customer-initiated refund
    - Order cancellation refund
    - After-sales refund processing
    - System-initiated automatic refund

"""

    name: str = "alipay_refund_payment"
    description: str = "Initiate a refund for a transaction and return refund status and amount"

    async def _arun(
        self,
        args: PaymentRefundInput,
        **kwargs: Any,
    ) -> PaymentOutput:
        """
        Initiate a refund request for an Alipay transaction.

        This method initiates a refund request for an already paid Alipay
        order. It supports both partial and full refunds, allows specifying
        refund reason, and uses an idempotency key.

        Args:
            args (PaymentRefundInput): Object containing refund parameters
                - out_trade_no: Merchant order number
                - refund_amount: Refund amount (yuan)
                - refund_reason: Refund reason (optional)
                - out_request_no: Refund request number (optional;
                    generated if not provided)
            **kwargs: Additional keyword arguments

        Returns:
            PaymentOutput: Text output containing refund result

        Raises:
            ValueError: If configuration parameters are incorrect
            ImportError: If Alipay SDK is unavailable
            Exception: For any other refund errors

"""
        out_request_no = args.out_request_no
        if not out_request_no:
            timestamp = int(datetime.now().timestamp())
            out_request_no = f"{args.out_trade_no}_refund_{timestamp}"

        try:
            # Create an Alipay client instance
            alipay_client = _create_alipay_client()

            # Create refund model
            model = AlipayTradeRefundModel()
            model.out_trade_no = args.out_trade_no
            model.refund_amount = str(args.refund_amount)
            model.refund_reason = args.refund_reason
            model.out_request_no = out_request_no

            # Set custom extended parameters
            extend_params = AgentExtendParams()
            extend_params.request_channel_source = X_AGENT_CHANNEL
            model.extend_params = extend_params

            # Create refund request
            request = AlipayTradeRefundRequest(biz_model=model)

            # Execute refund request
            response_content = alipay_client.execute(request)
            response = AlipayTradeRefundResponse()
            response.parse_response_content(response_content)

            if response.is_success():
                if response.fund_change == "Y":
                    result = f"Refund result: refund successful, transaction: {response.trade_no}"
                else:
                    result = f"Refund result: idempotent duplicate refund succeeded, " f"transaction: {response.trade_no}"
                return PaymentOutput(result=result)
            else:
                return PaymentOutput(
                    result=f"Refund execution failed. Error: {response.msg}",
                )

        except (ValueError, ImportError) as e:
            # Configuration or SDK error
            logger.error(f"Refund configuration or SDK error: {str(e)}")
            raise
        except Exception as e:
            # Other exceptions with wrapped error message
            error_msg = f"Refund failed: {str(e)}"
            logger.error(f"Refund execution exception: {error_msg}")
            raise RuntimeError(error_msg) from e


class AlipayRefundQuery(Tool[RefundQueryInput, PaymentOutput]):
    """
    Alipay Refund Query Component

    This component queries the current status of a refund request that has
    been initiated. It can determine if the refund was successful, refund
    amount, and refund status.

    Key features:
    - Supports querying by merchant order number and refund request number
    - Returns detailed refund status information

    Input type: RefundQueryInput
    Output type: PaymentOutput

    Usage scenarios:
    - Query refund processing status
    - Verify refund results
    - Customer support inquiries

"""

    name: str = "alipay_query_refund"
    description: str = "Query an Alipay refund and return refund status and amount"

    async def _arun(
        self,
        args: RefundQueryInput,
        **kwargs: Any,
    ) -> PaymentOutput:
        """
        Query Alipay refund status.

        This method queries the current status of a refund request,
        including whether it was successful, the refunded amount,
        and refund status code.

        Args:
            args (RefundQueryInput): Object containing query parameters
                - out_trade_no: Merchant order number
                - out_request_no: Refund request number
            **kwargs: Additional keyword arguments

        Returns:
            PaymentOutput: Text output containing refund status result

        Raises:
            ValueError: If configuration parameters are incorrect
            ImportError: If Alipay SDK is unavailable
            Exception: For any other query errors

"""
        try:
            # Create an Alipay client instance
            alipay_client = _create_alipay_client()

            # Create fastpay refund query model
            model = AlipayTradeFastpayRefundQueryModel()
            model.out_trade_no = args.out_trade_no  # Merchant order number
            model.out_request_no = args.out_request_no  # Refund request number

            # Set custom extended parameters
            extend_params = AgentExtendParams()
            extend_params.request_channel_source = X_AGENT_CHANNEL
            model.extend_params = extend_params

            # Create refund query request
            request = AlipayTradeFastpayRefundQueryRequest(biz_model=model)

            # Execute refund query
            response_content = alipay_client.execute(request)
            response = AlipayTradeFastpayRefundQueryResponse()
            response.parse_response_content(response_content)

            # Process response
            if response.is_success():  # Query success
                if response.refund_status == "REFUND_SUCCESS":
                    # Refund succeeded
                    result = (
                        f"Refund found successful, transaction: {response.trade_no}, "
                        f"Refund amount: {response.refund_amount}, "
                        f"Refund status: {response.refund_status}"
                    )
                    return PaymentOutput(result=result)
                else:
                    # Refund not successful
                    return PaymentOutput(
                        result=(
                            f"未查询到退款成功. " f"Refund status: {response.refund_status}"
                        ),
                    )
            else:
                # Query failed
                return PaymentOutput(
                    result=f"Refund query failed. Error: {response.msg}",
                )

        except (ValueError, ImportError) as e:
            # Configuration or SDK error
            logger.error(f"Refund query configuration or SDK error: {str(e)}")
            raise
        except Exception as e:
            # Other exceptions with wrapped error message
            error_msg = f"Refund query failed: {str(e)}"
            logger.error(f"Refund query execution exception: {error_msg}")
            raise RuntimeError(error_msg) from e

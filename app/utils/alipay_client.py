# app/utils/alipay_client.py（修正版）
import logging
from alipay.aop.api.AlipayClientConfig import AlipayClientConfig
from alipay.aop.api.DefaultAlipayClient import DefaultAlipayClient
from alipay.aop.api.domain.AlipayTradePagePayModel import AlipayTradePagePayModel
from alipay.aop.api.request.AlipayTradePagePayRequest import AlipayTradePagePayRequest
from app.core.config import settings

logger = logging.getLogger(__name__)

# 全局客户端实例（懒加载）
_client = None
_client_config = None

def get_alipay_client() -> DefaultAlipayClient:
    global _client, _client_config
    if _client is None:
        _client_config = AlipayClientConfig()
        
        if settings.ALIPAY_DEBUG:
            _client_config.server_url = "https://openapi.alipaydev.com/gateway.do"
        else:
            _client_config.server_url = "https://openapi.alipay.com/gateway.do"
        
        _client_config.app_id = settings.ALIPAY_APP_ID
        _client_config.app_private_key = settings.ALIPAY_APP_PRIVATE_KEY
        _client_config.alipay_public_key = settings.ALIPAY_PUBLIC_KEY
        _client_config.sign_type = "RSA2"
        
        _client = DefaultAlipayClient(
            alipay_client_config=_client_config,
            logger=logger
        )
    return _client

def get_alipay_gateway() -> str:
    """获取当前环境的支付宝网关"""
    get_alipay_client()  # 确保客户端已初始化
    return _client_config.server_url

def create_alipay_order(
    out_trade_no: str,
    total_amount: float,
    subject: str,
) -> str:
    """
    创建支付宝订单，返回支付 URL
    
    Args:
        out_trade_no: 商户订单号（必须唯一）
        total_amount: 订单金额（元）
        subject: 订单标题
        
    Returns:
        完整的支付宝支付页面 URL
    """
    client = get_alipay_client()
    
    # 构造请求参数
    model = AlipayTradePagePayModel()
    model.out_trade_no = out_trade_no
    model.total_amount = str(total_amount)  # 必须转换为字符串
    model.subject = subject
    model.product_code = "FAST_INSTANT_TRADE_PAY"
    
    request = AlipayTradePagePayRequest(biz_model=model)
    request.return_url = settings.ALIPAY_RETURN_URL
    request.notify_url = settings.ALIPAY_NOTIFY_URL
    
    # 执行请求，返回 order_string（加密串）
    order_string = client.page_execute(request, http_method="GET")
    
    # 拼接完整支付 URL
    gateway = get_alipay_gateway()
    return f"{gateway}?{order_string}"

def verify_alipay_callback(data: dict) -> bool:
    """
    验签支付宝异步/同步回调
    
    Args:
        data: 支付宝回调的原始数据（包含 sign 字段）
        
    Returns:
        验签是否通过
    """
    client = get_alipay_client()
    signature = data.pop("sign", None)
    
    if not signature:
        logger.warning("支付宝回调缺少 sign 字段")
        return False
    
    # 使用 SDK 内置验签方法
    # verify 方法会使用配置的 alipay_public_key 对 data 进行验签
    success = client.verify(data, signature)
    
    if not success:
        logger.warning(f"支付宝回调验签失败, data: {data}")
    
    return success
# tests/unit/test_alipay_client.py
import pytest
from unittest.mock import MagicMock, patch
from app.utils.alipay_client import (
    create_alipay_order,
    verify_alipay_callback,
    get_alipay_client,
    get_alipay_gateway,
)
from app.core.config import settings


@pytest.fixture(autouse=True)
def reset_alipay_client():
    """每个测试前重置全局客户端单例"""
    import app.utils.alipay_client as alipay_module
    alipay_module._client = None
    alipay_module._client_config = None
    yield


def test_get_alipay_client_initializes():
    """测试首次调用创建客户端单例"""
    with patch("app.utils.alipay_client.DefaultAlipayClient") as MockClient:
        MockClient.return_value = MagicMock()
        client1 = get_alipay_client()
        client2 = get_alipay_client()
        assert client1 is client2
        MockClient.assert_called_once()


def test_get_alipay_gateway_returns_correct_url():
    """测试网关地址是否正确（沙箱/生产）"""
    import app.utils.alipay_client as alipay_module
    original_debug = settings.ALIPAY_DEBUG
    try:
        settings.ALIPAY_DEBUG = True
        alipay_module._client = None
        alipay_module._client_config = None
        assert get_alipay_gateway() == "https://openapi.alipaydev.com/gateway.do"
        
        settings.ALIPAY_DEBUG = False
        alipay_module._client = None
        alipay_module._client_config = None
        assert get_alipay_gateway() == "https://openapi.alipay.com/gateway.do"
    finally:
        settings.ALIPAY_DEBUG = original_debug
        # 可选：恢复全局单例状态，避免影响后续测试
        alipay_module._client = None
        alipay_module._client_config = None
        

def test_create_alipay_order_success():
    """测试创建订单成功，返回完整支付 URL"""
    with patch("app.utils.alipay_client.get_alipay_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.page_execute.return_value = "order_string=abc123"
        mock_get_client.return_value = mock_client

        with patch("app.utils.alipay_client.get_alipay_gateway", return_value="https://gateway.test"):
            result = create_alipay_order(
                out_trade_no="ORDER001",
                total_amount=99.99,
                subject="Test Product"
            )
            assert result == "https://gateway.test?order_string=abc123"
            # 验证 page_execute 调用参数
            mock_client.page_execute.assert_called_once()
            call_args = mock_client.page_execute.call_args
            request = call_args[0][0]  # 第一个参数是 request 对象
            assert request.biz_model.out_trade_no == "ORDER001"
            assert request.biz_model.total_amount == "99.99"
            assert request.biz_model.subject == "Test Product"


def test_create_alipay_order_client_raises_exception():
    """测试客户端调用异常时抛出原始异常"""
    with patch("app.utils.alipay_client.get_alipay_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.page_execute.side_effect = Exception("Network error")
        mock_get_client.return_value = mock_client

        with pytest.raises(Exception, match="Network error"):
            create_alipay_order("ORDER002", 10.0, "Test")


def test_verify_alipay_callback_success():
    """测试验签成功"""
    callback_data = {
        "trade_no": "123456",
        "out_trade_no": "ORDER001",
        "sign": "valid_signature",
    }
    with patch("app.utils.alipay_client.get_alipay_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.verify.return_value = True
        mock_get_client.return_value = mock_client

        result = verify_alipay_callback(callback_data.copy())
        assert result is True
        # verify 应被调用，且 sign 被移除
        mock_client.verify.assert_called_once()
        args = mock_client.verify.call_args[0]
        # 第一个参数应该是移除了 sign 的字典
        assert "sign" not in args[0]
        assert args[1] == "valid_signature"


def test_verify_alipay_callback_missing_sign():
    """测试回调数据缺少 sign 字段"""
    callback_data = {"trade_no": "123456", "out_trade_no": "ORDER001"}
    with patch("app.utils.alipay_client.get_alipay_client") as mock_get_client:
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client
        result = verify_alipay_callback(callback_data)
        assert result is False
        mock_client.verify.assert_not_called()


def test_verify_alipay_callback_invalid_signature():
    """测试验签失败"""
    callback_data = {
        "trade_no": "123456",
        "out_trade_no": "ORDER001",
        "sign": "invalid",
    }
    with patch("app.utils.alipay_client.get_alipay_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.verify.return_value = False
        mock_get_client.return_value = mock_client

        result = verify_alipay_callback(callback_data.copy())
        assert result is False
        mock_client.verify.assert_called_once()


def test_verify_alipay_callback_client_raises_exception():
    """测试验签过程中客户端抛出异常（如网络错误）"""
    callback_data = {"sign": "some", "key": "value"}
    with patch("app.utils.alipay_client.get_alipay_client") as mock_get_client:
        mock_client = MagicMock()
        mock_client.verify.side_effect = Exception("Verification error")
        mock_get_client.return_value = mock_client

        with pytest.raises(Exception, match="Verification error"):
            verify_alipay_callback(callback_data)
import pytest
import uuid
from unittest.mock import patch
from app.core.config import settings

pytestmark = pytest.mark.skip(reason="需要重构支付宝沙箱环境，暂时跳过")
def test_create_order_success(client, setup_database):
    response = client.post("/orders/create", params={"plan_id": 1})
    assert response.status_code == 201
    data = response.json()
    assert "trade_no" in data
    assert "pay_url" in data
    assert data["amount_cents"] == 100

def test_create_order_plan_inactive(client, setup_database):
    from app.db.session import SessionLocal
    from app.models.plan import Plan
    db = SessionLocal()
    plan = db.query(Plan).filter(Plan.id == 1).first()
    plan.is_active = False
    db.commit()
    db.close()
    
    response = client.post("/orders/create", params={"plan_id": 1})
    assert response.status_code == 404
    assert "not found or inactive" in response.text

def test_alipay_notify_success(client, setup_database):
    # 创建订单获取 trade_no
    create_resp = client.post("/orders/create", params={"plan_id": 1})
    assert create_resp.status_code == 201
    trade_no = create_resp.json()["trade_no"]
    
    settings.ALIPAY_APP_ID = "2021000123456789"
    
    with patch("app.routers.orders.verify_alipay_callback", return_value=True):
        callback_data = {
            "trade_no": "ALIPAY123",
            "out_trade_no": trade_no,
            "trade_status": "TRADE_SUCCESS",
            "app_id": "2021000123456789",
            "total_amount": "1.00"
        }
        response = client.post("/orders/alipay/notify", data=callback_data)
        assert response.text == "success"
        
        # 验证订单状态
        from app.db.session import SessionLocal
        from app.models.order import Order, OrderStatus
        db = SessionLocal()
        order = db.query(Order).filter(Order.trade_no == trade_no).first()
        assert order.status == OrderStatus.PAID
        db.close()

def test_alipay_notify_invalid_signature(client, setup_database):
    # 创建订单
    create_resp = client.post("/orders/create", params={"plan_id": 1})
    assert create_resp.status_code == 201
    trade_no = create_resp.json()["trade_no"]
    
    with patch("app.routers.orders.verify_alipay_callback", return_value=False):
        callback_data = {"out_trade_no": trade_no}
        response = client.post("/orders/alipay/notify", data=callback_data)
        assert response.text == "fail"
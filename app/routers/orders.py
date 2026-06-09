import logging
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.plan import Plan
from app.models.order import Order, OrderStatus
from app.utils.alipay_client import create_alipay_order, verify_alipay_callback
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/orders", tags=["orders"])


def generate_trade_no() -> str:
    """生成唯一商户订单号：时间戳 + 随机字符串"""
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    random_suffix = secrets.token_hex(8).upper()
    return f"ORDER{timestamp}{random_suffix}"


def upgrade_user_plan(db: Session, user_id: int, plan_id: int):
    """
    支付成功后为用户升级套餐/增加配额
    可根据业务逻辑设计：
    - 月付套餐：重置配额，设置过期时间
    - 永久加量：在原有剩余配额上累加
    """
    plan = db.query(Plan).filter(Plan.id == plan_id).first()
    user = db.query(User).filter(User.id == user_id).first()
    if not plan or not user:
        return

    # 示例：按次计费套餐，直接增加剩余配额（不重置）
    # 若需重置配额，可设置 user.quota_used = 0
    user.extra_tokens = user.extra_tokens + plan.quota
    # 可选：记录当前套餐代码
    # user.plan = plan.code
    db.commit()
    logger.info(f"User {user_id} upgraded to plan {plan.name}, added {plan.quota} quota")


@router.post("/create", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_order(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """创建订单并返回支付宝支付链接"""
    # 校验套餐
    plan = db.query(Plan).filter(Plan.id == plan_id, Plan.is_active == True).first()
    if not plan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Plan not found or inactive"
        )

    # 生成唯一订单号
    trade_no = generate_trade_no()
    while db.query(Order).filter(Order.trade_no == trade_no).first():
        trade_no = generate_trade_no()

    # 创建订单
    new_order = Order(
        user_id=current_user.id,
        plan_id=plan_id,
        amount_cents=plan.price_cents,
        status=OrderStatus.PENDING,
        trade_no=trade_no,
        created_at=datetime.utcnow(),
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # 获取支付宝支付链接
    pay_url = create_alipay_order(
        out_trade_no=trade_no,
        total_amount=plan.price_cents / 100,
        subject=f"购买 {plan.name} 套餐",
    )

    return {
        "id": new_order.id,
        "trade_no": trade_no,
        "amount_cents": plan.price_cents,
        "amount": f"{plan.price_cents / 100:.2f}",
        "currency": plan.currency,
        "pay_url": pay_url,
        "status": new_order.status.value,
        "plan_name": plan.name,
        "created_at": new_order.created_at.isoformat(),
    }


@router.post("/alipay/notify", response_class=PlainTextResponse)
async def alipay_notify(
    request: Request,
    db: Session = Depends(get_db),
):
    """支付宝异步通知回调"""
    # 获取表单数据
    form_data = await request.form()
    data = dict(form_data)

    # 1. 验签
    if not verify_alipay_callback(data):
        logger.warning(f"支付宝回调验签失败: {data}")
        return PlainTextResponse("fail")  # 支付宝要求200
    
    # 2. 提取关键参数
    trade_no = data.get("trade_no")
    out_trade_no = data.get("out_trade_no")
    trade_status = data.get("trade_status")
    app_id = data.get("app_id")
    total_amount = data.get("total_amount")
    notify_id = data.get("notify_id")   # 用于幂等

    # 3. 校验 app_id
    if app_id != settings.ALIPAY_APP_ID:
        logger.warning(f"App ID mismatch: {app_id}")
        return PlainTextResponse("fail")  # 支付宝要求200

    # 4. 查询订单
    order = db.query(Order).filter(Order.trade_no == out_trade_no).first()
    if not order:
        logger.warning(f"Order not found: {out_trade_no}")
        return PlainTextResponse("fail")  # 支付宝要求200

    # 5. 幂等性检查：如果订单已经是 PAID 状态，直接返回 success（避免重复处理）
    if order.status == OrderStatus.PAID:
        logger.info(f"Order {out_trade_no} already paid, skip processing.")
        return PlainTextResponse("success")

    # 6. 校验金额
    expected_amount = order.amount_cents / 100.0
    if abs(float(total_amount) - expected_amount) > 0.01:
        logger.warning(f"Amount mismatch: {total_amount} vs {expected_amount}")
        return PlainTextResponse("fail")  # 支付宝要求200

    # 7. 处理交易状态
    if trade_status == "TRADE_SUCCESS" or trade_status == "TRADE_FINISHED":
        # 支付成功
        order.status = OrderStatus.PAID
        # 可选：保存支付宝交易号
        # order.alipay_trade_no = trade_no
        db.commit()

        # 升级用户套餐
        upgrade_user_plan(db, order.user_id, order.plan_id)

        logger.info(f"Order {out_trade_no} paid successfully, trade_no: {trade_no}")
    elif trade_status == "TRADE_CLOSED":
        # 交易关闭（未支付超时或用户主动关闭）
        order.status = OrderStatus.CANCELLED
        db.commit()
        logger.info(f"Order {out_trade_no} closed, status: {trade_status}")
    else:
        # 其他状态（如 WAIT_BUYER_PAY）忽略
        logger.info(f"Order {out_trade_no} status: {trade_status}, no action")

    # 支付宝要求：收到通知后必须返回字符串 "success"
    return PlainTextResponse("success")
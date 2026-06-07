from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update, select
from app.models.user import User

async def check_and_deduct_quota(user_id: int, cost: int, db: AsyncSession) -> bool:
    # 先查询用户当前配额
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    available = (user.quota_limit - user.quota_used) + user.extra_tokens
    if available < cost:
        return False
    # 扣减策略：先扣 extra_tokens，再扣套餐内
    remaining_cost = cost
    if user.extra_tokens >= remaining_cost:
        await db.execute(
            update(User).where(User.id == user_id).values(extra_tokens=user.extra_tokens - remaining_cost)
        )
    else:
        new_extra = 0
        remaining_cost -= user.extra_tokens
        new_used = user.quota_used + remaining_cost
        await db.execute(
            update(User).where(User.id == user_id).values(extra_tokens=new_extra, quota_used=new_used)
        )
    await db.commit()
    return True

async def refund_quota(user_id: int, cost: int, db: AsyncSession):
    """回滚配额（当上游失败时）"""
    # 简单实现：按原路加回，但需区分 extra_tokens 和 quota_used
    # 实际生产需记录流水，这里简化
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one()
    # 假设最后一次扣减是从 extra_tokens 扣的（简化）
    await db.execute(
        update(User).where(User.id == user_id).values(extra_tokens=user.extra_tokens + cost)
    )
    await db.commit()
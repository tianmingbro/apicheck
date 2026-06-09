import pytest
from threading import Thread
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.models.user import User
from app.core.quota import check_and_deduct_quota
import uuid

def deduct_worker(user_id, cost, success_list):
    db = SessionLocal()
    try:
        result = check_and_deduct_quota(user_id, cost, db)
        success_list.append(result)
    finally:
        db.close()

def test_concurrent_deduction():
    unique_name = f"concurrency_{uuid.uuid4().hex[:8]}"
    db = SessionLocal()
    user = User(username=unique_name, hashed_password="fake", quota_limit=5, quota_used=0)
    db.add(user)
    db.commit()
    user_id = user.id
    db.close()

    results = []
    def worker():
        db_local = SessionLocal()
        try:
            result = check_and_deduct_quota(user_id, 1, db_local)
            results.append(result)
        finally:
            db_local.close()

    threads = [Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert sum(results) == 5

    # 清理
    db = SessionLocal()
    db.query(User).filter(User.id == user_id).delete()
    db.commit()
    db.close()
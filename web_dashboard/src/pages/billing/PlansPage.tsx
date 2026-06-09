// src/pages/billing/PlansPage.tsx
import { useQuery } from '@tanstack/react-query';
import { billingApi, type Plan } from '@/services/modules/billingApi';
import PlanCard from '@/components/billing/PlanCard';

// 模拟当前套餐 ID（实际应从 store 或 API 获取）
const CURRENT_PLAN_ID = 1; // 假设免费套餐 ID 为 1

export default function PlansPage() {
  // 获取套餐列表
  const { data: plansData, isLoading, error } = useQuery({
    queryKey: ['plans'],
    queryFn: billingApi.getPlans,
  });

  // 预留升级回调（暂只 console，后续可集成支付）
  const handleUpgrade = (planId: number) => {
    console.log('Upgrade to plan:', planId);
    // TODO: 跳转支付流程或弹窗确认
  };

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {[1, 2, 3].map((i) => (
          <div key={i} className="h-96 bg-neutral-100 dark:bg-neutral-800 rounded-xl animate-pulse" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-danger text-center p-6">
        加载失败：{(error as Error).message}
      </div>
    );
  }

  const plans = plansData?.data || [];

  if (plans.length === 0) {
    return (
      <div className="text-center text-neutral-500 dark:text-neutral-400 p-6">
        暂无可用的套餐
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="text-center">
        <h1 className="text-2xl font-bold">选择适合您的套餐</h1>
        <p className="text-neutral-600 dark:text-neutral-400 mt-2">
          灵活计费，按需升级，解锁更多调用额度
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {plans.map((plan: Plan) => (
          <PlanCard
            key={plan.id}
            plan={{
              id: plan.id,
              name: plan.name,
              price_cents: plan.price_cents,
              currency: plan.currency,
              quota: plan.quota,
              quota_unit: plan.quota_unit,
              features: plan.features,
            }}
            isCurrent={plan.id === CURRENT_PLAN_ID}
            onUpgrade={handleUpgrade}
          />
        ))}
      </div>
    </div>
  );
}
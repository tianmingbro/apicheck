// src/pages/billing/PlansPage.tsx
import { useQuery, useMutation } from '@tanstack/react-query';
import { billingApi, type Plan } from '@/services/modules/billingApi';
import PlanCard from '@/components/billing/PlanCard';
import apiClient from '@/services/apiClient';
import { useNavigate } from 'react-router-dom';

export default function PlansPage() {
  const navigate = useNavigate();

  // Fetch plans list
  const { data: plansData, isLoading, error } = useQuery({
    queryKey: ['plans'],
    queryFn: () => billingApi.getPlans().then((r) => r.data),
  });

  // Fetch current plan
  const { data: currentPlan } = useQuery({
    queryKey: ['current-plan'],
    queryFn: () => billingApi.getCurrentPlan().then((r) => r.data),
    retry: false,
  });

  const currentPlanId = currentPlan?.id || null;

  const upgradeMutation = useMutation({
    mutationFn: (planId: number) =>
      apiClient.post('/api/orders/create', null, { params: { plan_id: planId } }),
    onSuccess: (res) => {
      const payUrl = res.data?.pay_url;
      if (payUrl) {
        window.open(payUrl, '_blank');
      } else {
        alert('创建订单成功，请在我的订单中查看');
      }
      navigate('/billing');
    },
    onError: (err: any) => {
      alert(err?.response?.data?.detail || '创建订单失败，请稍后再试');
    },
  });

  const handleUpgrade = (planId: number) => {
    if (planId === currentPlanId) return;
    upgradeMutation.mutate(planId);
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

  const plans = plansData || [];

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
            isCurrent={plan.id === currentPlanId}
            onUpgrade={handleUpgrade}
            isLoading={upgradeMutation.isPending}
          />
        ))}
      </div>
    </div>
  );
}

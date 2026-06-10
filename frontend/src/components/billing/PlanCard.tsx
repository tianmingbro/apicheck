// src/components/billing/PlanCard.tsx
import { Check, Crown } from 'lucide-react';

interface PlanCardProps {
  plan: {
    id: number;
    name: string;
    price_cents: number;
    currency: string;
    quota: number;
    quota_unit: string;
    features: string[];
  };
  isCurrent?: boolean;
  onUpgrade?: (planId: number) => void;
  isLoading?: boolean;
}

export default function PlanCard({ plan, isCurrent = false, onUpgrade, isLoading = false }: PlanCardProps) {
  const price = (plan.price_cents / 100).toFixed(2);
  const priceDisplay = plan.price_cents === 0 ? '免费' : `${price} ${plan.currency}`;

  return (
    <div
      className={`
        relative flex flex-col h-full p-6 rounded-xl shadow-sm border-2 transition-all
        ${isCurrent
          ? 'border-primary bg-primary/5 dark:bg-primary/10'
          : 'border-neutral-200 dark:border-neutral-700 bg-white dark:bg-neutral-800 hover:shadow-md'
        }
      `}
    >
      {/* 当前套餐角标 */}
      {isCurrent && (
        <div className="absolute -top-3 -right-3 bg-primary text-white rounded-full p-1 shadow-md">
          <Crown className="w-5 h-5" />
        </div>
      )}

      {/* 套餐名称 */}
      <h3 className="text-xl font-bold text-neutral-900 dark:text-white mb-2">{plan.name}</h3>

      {/* 价格 */}
      <div className="mb-4">
        <span className="text-3xl font-extrabold text-neutral-900 dark:text-white">{priceDisplay}</span>
        {plan.price_cents > 0 && (
          <span className="text-sm text-neutral-500 dark:text-neutral-400"> / 月</span>
        )}
      </div>

      {/* 配额说明 */}
      <p className="text-sm text-neutral-600 dark:text-neutral-300 mb-4">
        {plan.quota.toLocaleString()} {plan.quota_unit} / 月
      </p>

      {/* 特性列表 */}
      <ul className="flex-1 space-y-2 mb-6">
        {plan.features.map((feature, idx) => (
          <li key={idx} className="flex items-center gap-2 text-sm text-neutral-700 dark:text-neutral-300">
            <Check className="w-4 h-4 text-primary flex-shrink-0" />
            <span>{feature}</span>
          </li>
        ))}
      </ul>

      {/* 操作按钮 */}
      <button
        onClick={() => onUpgrade?.(plan.id)}
        disabled={isCurrent || isLoading}
        className={`
          w-full py-2 rounded-md font-medium transition-colors
          ${isCurrent
            ? 'bg-neutral-100 dark:bg-neutral-700 text-neutral-500 cursor-not-allowed'
            : 'bg-primary text-white hover:bg-primary-dark focus:ring-2 focus:ring-primary focus:ring-offset-2'
          }
          ${isLoading ? 'opacity-50 cursor-wait' : ''}
        `}
        aria-label={`升级到${plan.name}套餐`}
      >
        {isCurrent ? '当前套餐' : '选择套餐'}
      </button>
    </div>
  );
}
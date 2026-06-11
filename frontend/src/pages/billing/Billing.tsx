export default function Billing() {
  return (
    <div>
      <h1 className="text-2xl font-bold text-neutral-900 dark:text-white mb-4">账单与套餐</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <PlanCard
          name="Free"
          price="¥0"
          quota="1,000 次/月"
          features={['基础 API Key 管理', '轮询负载均衡', '基础速率限制']}
          current
        />
        <PlanCard
          name="Pro"
          price="¥29/月"
          quota="10,000 次/月"
          features={['所有 Free 功能', '更高配额', '优先支持', '高级统计']}
          recommended
        />
        <PlanCard
          name="Enterprise"
          price="¥99/月"
          quota="100,000 次/月"
          features={['所有 Pro 功能', '无限配额选项', '专属支持', 'SLA 保障']}
        />
      </div>
    </div>
  );
}

function PlanCard({
  name, price, quota, features, current, recommended,
}: {
  name: string;
  price: string;
  quota: string;
  features: string[];
  current?: boolean;
  recommended?: boolean;
}) {
  return (
    <div
      className={`relative bg-white dark:bg-neutral-800 rounded-lg shadow border p-6 flex flex-col
        ${recommended ? 'border-primary-500 ring-2 ring-primary-500' : 'border-neutral-200 dark:border-neutral-700'}`}
    >
      {recommended && (
        <span className="absolute -top-3 left-1/2 -translate-x-1/2 bg-primary-500 text-white text-xs px-3 py-0.5 rounded-full">
          推荐
        </span>
      )}
      <h3 className="text-lg font-semibold text-neutral-900 dark:text-white">{name}</h3>
      <p className="text-3xl font-bold mt-2 text-neutral-900 dark:text-white">{price}</p>
      <p className="text-sm text-neutral-500 mt-1">{quota}</p>
      <ul className="mt-4 space-y-2 flex-1">
        {features.map((f) => (
          <li key={f} className="flex items-center text-sm text-neutral-600 dark:text-neutral-400">
            <span className="mr-2 text-success">✓</span> {f}
          </li>
        ))}
      </ul>
      <button
        disabled={current}
        className={`mt-6 w-full py-2 rounded-md font-medium transition-colors
          ${current
            ? 'bg-neutral-100 dark:bg-neutral-700 text-neutral-500 cursor-not-allowed'
            : 'bg-primary-500 text-white hover:bg-primary-600'}`}
      >
        {current ? '当前套餐' : '升级'}
      </button>
    </div>
  );
}

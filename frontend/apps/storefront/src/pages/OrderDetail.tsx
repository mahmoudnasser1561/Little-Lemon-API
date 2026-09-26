import { Link, useParams } from 'react-router-dom';
import { Badge, Card } from '@little-lemon/ui';
import { useOrder } from '../hooks/useOrders';

export function OrderDetail() {
  const { id } = useParams();
  const orderQuery = useOrder(Number(id));

  return (
    <div className="flex-grow py-16 flex items-center justify-center">
      <div className="w-[480px] flex flex-col gap-5">
        {orderQuery.isLoading && <p className="text-text-secondary text-center">Loading…</p>}
        {orderQuery.isError && <p className="text-danger text-center">Couldn't load this order.</p>}

        {orderQuery.data && (
          <Card className="p-10 flex flex-col gap-5">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h1 className="font-display text-[26px]">Order #{orderQuery.data.id}</h1>
                <p className="text-text-secondary text-sm mt-1">{orderQuery.data.date}</p>
              </div>
              <Badge tone={orderQuery.data.status ? 'olive' : 'amber'}>
                {orderQuery.data.status ? 'Delivered' : 'In progress'}
              </Badge>
            </div>

            <div className="h-px bg-border" />

            <div className="flex items-center justify-between font-semibold text-[18px]">
              <span>Total</span>
              <span className="tabular-nums">${orderQuery.data.total}</span>
            </div>

            <Card className="p-4 bg-surface-alt border-none flex gap-3">
              <svg
                width="18"
                height="18"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-text-secondary flex-shrink-0 mt-0.5"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="16" x2="12" y2="12" />
                <line x1="12" y1="8" x2="12.01" y2="8" />
              </svg>
              <p className="text-text-secondary text-sm">
                The API doesn't return individual line items for an order yet, so only the order total and status are
                shown here.
              </p>
            </Card>

            <Link to="/orders" className="text-sm text-text-secondary text-center">
              Back to my orders
            </Link>
          </Card>
        )}
      </div>
    </div>
  );
}

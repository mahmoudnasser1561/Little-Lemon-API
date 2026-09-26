import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Badge, Card, Pagination } from '@little-lemon/ui';
import { useOrders } from '../hooks/useOrders';

export function MyOrders() {
  const [page, setPage] = useState(1);
  const ordersQuery = useOrders(page);

  return (
    <div className="flex-grow">
      <div className="px-12 pt-12 pb-6">
        <h1 className="font-display text-[34px]">My orders</h1>
      </div>

      <div className="px-12 pb-16">
        {ordersQuery.isLoading && <p className="text-text-secondary">Loading…</p>}
        {ordersQuery.isError && <p className="text-danger">Couldn't load your orders. Is the API running?</p>}

        {ordersQuery.data && ordersQuery.data.results.length === 0 && (
          <Card className="flex flex-col items-center justify-center gap-3 py-16">
            <h3 className="font-display text-[19px]">No orders yet</h3>
            <p className="text-text-secondary text-sm">Your placed orders will show up here.</p>
          </Card>
        )}

        {ordersQuery.data && ordersQuery.data.results.length > 0 && (
          <>
            <Card className="p-2">
              {ordersQuery.data.results.map((order) => (
                <Link
                  key={order.id}
                  to={`/orders/${order.id}`}
                  className="flex items-center gap-5 px-5 py-5 border-b border-border last:border-b-0 hover:bg-surface-alt"
                >
                  <div className="flex-grow flex flex-col gap-1">
                    <span className="font-semibold text-[15px]">Order #{order.id}</span>
                    <span className="text-text-secondary text-sm">{order.date}</span>
                  </div>
                  <Badge tone={order.status ? 'olive' : 'amber'}>{order.status ? 'Delivered' : 'In progress'}</Badge>
                  <span className="price w-20 text-right font-semibold tabular-nums">${order.total}</span>
                </Link>
              ))}
            </Card>

            <div className="mt-8">
              <Pagination
                page={page}
                hasPrevious={Boolean(ordersQuery.data.previous)}
                hasNext={Boolean(ordersQuery.data.next)}
                onPrevious={() => setPage((p) => Math.max(1, p - 1))}
                onNext={() => setPage((p) => p + 1)}
                totalCount={ordersQuery.data.count}
              />
            </div>
          </>
        )}
      </div>
    </div>
  );
}

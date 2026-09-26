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

            <div className="flex flex-col gap-2">
              {orderQuery.data.orderitem.map((line, i) => (
                <div key={i} className="flex items-center justify-between text-sm">
                  <span className="text-text-secondary">
                    {line.title ?? 'Removed menu item'} × {line.quantity}
                  </span>
                  <span>${line.price}</span>
                </div>
              ))}
            </div>

            <div className="h-px bg-border" />

            <div className="flex items-center justify-between font-semibold text-[18px]">
              <span>Total</span>
              <span className="tabular-nums">${orderQuery.data.total}</span>
            </div>

            <Link to="/orders" className="text-sm text-text-secondary text-center">
              Back to my orders
            </Link>
          </Card>
        )}
      </div>
    </div>
  );
}

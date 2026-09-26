import { Link, useNavigate } from 'react-router-dom';
import { Button, Card } from '@little-lemon/ui';
import { useCart } from '../hooks/useCart';
import { useCreateOrder } from '../hooks/useOrders';

const today = new Date().toLocaleDateString(undefined, {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
});

export function Checkout() {
  const cartQuery = useCart();
  const createOrder = useCreateOrder();
  const navigate = useNavigate();

  async function handlePlaceOrder() {
    try {
      const order = await createOrder.mutateAsync();
      navigate(`/orders/${order.id}`);
    } catch {
      // surfaced below via createOrder.isError
    }
  }

  return (
    <div className="flex-grow flex items-center justify-center py-16">
      <div className="w-[480px] bg-surface border border-border rounded p-10 flex flex-col gap-5">
        <div>
          <h1 className="font-display text-[28px]">Review &amp; place order</h1>
          <p className="text-text-secondary text-sm mt-1.5">
            There's no separate payment step in this build — placing the order converts your cart directly.
          </p>
        </div>

        {cartQuery.isLoading && <p className="text-text-secondary">Loading…</p>}

        {cartQuery.data && cartQuery.data.items.length === 0 && (
          <div className="flex flex-col gap-3">
            <p className="text-text-secondary text-sm">Your cart is empty — there's nothing to check out.</p>
            <Link to="/">
              <Button size="sm">Browse the menu</Button>
            </Link>
          </div>
        )}

        {cartQuery.data && cartQuery.data.items.length > 0 && (
          <>
            <div className="flex flex-col gap-2">
              {cartQuery.data.items.map((line) => (
                <div key={line.menuitem} className="flex items-center justify-between text-sm">
                  <span className="text-text-secondary">
                    {line.title} × {line.quantity}
                  </span>
                  <span>${line.price}</span>
                </div>
              ))}
              <div className="h-px bg-border my-1.5" />
              <div className="flex items-center justify-between font-semibold text-[18px]">
                <span>Total</span>
                <span className="tabular-nums">${cartQuery.data.total}</span>
              </div>
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
                Placing your order today, {today}.
              </p>
            </Card>

            {createOrder.isError && (
              <p className="text-sm text-danger font-medium">Couldn't place your order. Please try again.</p>
            )}

            <Button className="w-full" onClick={handlePlaceOrder} disabled={createOrder.isPending}>
              {createOrder.isPending ? 'Placing order…' : `Place order — $${cartQuery.data.total}`}
            </Button>
            <Link to="/cart" className="text-sm text-text-secondary text-center">
              Back to cart
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

import { Link } from 'react-router-dom';
import { Button, Card, Stepper } from '@little-lemon/ui';
import { DishIcon } from '../components/icons';
import { useCart, useClearCart, useRemoveCartLine, useUpdateCartQuantity } from '../hooks/useCart';

export function Cart() {
  const cartQuery = useCart();
  const updateQuantity = useUpdateCartQuantity();
  const removeLine = useRemoveCartLine();
  const clearCart = useClearCart();

  return (
    <div className="flex-grow">
      <div className="px-12 pt-12 pb-6">
        <h1 className="font-display text-[34px]">Your cart</h1>
      </div>

      {cartQuery.isLoading && <p className="px-12 text-text-secondary">Loading…</p>}
      {cartQuery.isError && <p className="px-12 text-danger">Couldn't load your cart. Is the API running?</p>}

      {cartQuery.data && cartQuery.data.items.length === 0 && (
        <div className="px-12 pb-16">
          <Card className="flex flex-col items-center justify-center gap-3 py-16">
            <div className="text-text-tertiary">
              <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="9" cy="21" r="1" />
                <circle cx="20" cy="21" r="1" />
                <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
              </svg>
            </div>
            <h3 className="font-display text-[19px]">Your cart is empty</h3>
            <p className="text-text-secondary text-sm">Add a few dishes from the menu to get started.</p>
            <Link to="/" className="mt-2">
              <Button size="sm">Browse the menu</Button>
            </Link>
          </Card>
        </div>
      )}

      {cartQuery.data && cartQuery.data.items.length > 0 && (
        <div className="px-12 pb-16 grid grid-cols-[1fr_380px] gap-8 items-start">
          <Card className="p-2">
            {cartQuery.data.items.map((line) => (
              <div key={line.menuitem} className="flex items-center gap-5 px-5 py-5 border-b border-border last:border-b-0">
                <div className="w-16 h-16 rounded bg-accent-soft text-accent flex items-center justify-center flex-shrink-0">
                  <DishIcon />
                </div>
                <div className="flex-grow flex flex-col gap-1">
                  <span className="font-semibold text-[15px]">{line.title}</span>
                  <span className="text-text-secondary text-sm">${line.unit_price} each</span>
                </div>
                <Stepper
                  value={line.quantity}
                  onChange={(next) => updateQuantity.mutate({ menuitemId: line.menuitem, quantity: next })}
                />
                <span className="price w-20 text-right font-semibold tabular-nums">${line.price}</span>
                <button
                  type="button"
                  aria-label={`Remove ${line.title}`}
                  onClick={() => removeLine.mutate(line.menuitem)}
                  className="w-9 h-9 rounded-full flex items-center justify-center text-text-secondary hover:bg-surface-alt hover:text-danger"
                >
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                  </svg>
                </button>
              </div>
            ))}
          </Card>

          <Card className="p-6 flex flex-col gap-4 sticky top-6">
            <h3 className="font-display text-[17px]">Order summary</h3>
            <div className="flex items-center justify-between text-sm text-text-secondary">
              <span>Items</span>
              <span>${cartQuery.data.total}</span>
            </div>
            <div className="h-px bg-border" />
            <div className="flex items-center justify-between font-semibold text-[17px]">
              <span>Total</span>
              <span className="tabular-nums">${cartQuery.data.total}</span>
            </div>
            <Link to="/checkout">
              <Button className="w-full">Checkout</Button>
            </Link>
            <button
              type="button"
              onClick={() => clearCart.mutate()}
              disabled={clearCart.isPending}
              className="text-sm font-semibold text-text-secondary hover:text-danger"
            >
              Clear cart
            </button>
            <p className="text-xs text-text-tertiary">
              Prices are always read live from the menu, never stored — this total is computed the same way at checkout.
            </p>
          </Card>
        </div>
      )}
    </div>
  );
}

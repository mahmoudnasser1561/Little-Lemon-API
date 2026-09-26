import { Link, useNavigate } from 'react-router-dom';
import { useCurrentUser, useLogout } from '../hooks/useAuth';
import { useCart } from '../hooks/useCart';

/** Storefront-only chrome (not in @little-lemon/ui - the ops-console app will have its
 * own Sidebar instead, per frontend_plan.md's architecture split). */
export function NavBar() {
  const { data: user, isLoading } = useCurrentUser();
  const { data: cartData } = useCart();
  const logout = useLogout();
  const navigate = useNavigate();
  const cartCount = cartData?.items.reduce((sum, line) => sum + line.quantity, 0) ?? 0;

  async function handleLogout() {
    await logout.mutateAsync();
    navigate('/');
  }

  return (
    <div className="h-[76px] flex items-center justify-between px-12 border-b border-border bg-surface flex-shrink-0">
      <Link to="/" className="flex items-center gap-2.5 font-display text-[22px] font-bold text-text">
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="#B5482C" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="12" r="9" />
          <path d="M8 12a4 4 0 0 1 8 0" />
        </svg>
        Little Lemon
      </Link>
      <div className="flex items-center gap-8 text-sm font-semibold text-text-secondary">
        <Link to="/" className="text-text">
          Menu
        </Link>
        {!isLoading && user && (
          <Link to="/orders" className="text-text">
            My orders
          </Link>
        )}
      </div>
      <div className="flex items-center gap-4">
        <Link
          to="/cart"
          aria-label="Cart"
          className="relative w-[38px] h-[38px] rounded-full flex items-center justify-center text-text-secondary hover:bg-surface-alt hover:text-text"
        >
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <circle cx="9" cy="21" r="1" />
            <circle cx="20" cy="21" r="1" />
            <path d="M1 1h4l2.68 13.39a2 2 0 0 0 2 1.61h9.72a2 2 0 0 0 2-1.61L23 6H6" />
          </svg>
          {cartCount > 0 && (
            <span className="absolute -top-1 -right-1 min-w-[18px] h-[18px] px-1 rounded-full bg-accent text-white text-[10px] font-bold flex items-center justify-center">
              {cartCount}
            </span>
          )}
        </Link>

        {!isLoading && user && (
          <div className="flex items-center gap-3">
            <Link
              to="/profile"
              aria-label="Profile"
              className="w-9 h-9 rounded-full bg-text text-white flex items-center justify-center text-[13px] font-bold"
            >
              {user.username.charAt(0).toUpperCase()}
            </Link>
            <button
              type="button"
              onClick={handleLogout}
              disabled={logout.isPending}
              className="text-sm font-semibold text-text-secondary hover:text-text"
            >
              Log out
            </button>
          </div>
        )}
        {!isLoading && !user && (
          <>
            <Link to="/login" className="text-sm font-semibold text-text-secondary hover:text-text">
              Log in
            </Link>
            <Link
              to="/signup"
              className="inline-flex items-center justify-center h-9 px-3.5 rounded-sm text-[13px] font-semibold bg-accent text-white hover:bg-accent-hover"
            >
              Sign up
            </Link>
          </>
        )}
      </div>
    </div>
  );
}

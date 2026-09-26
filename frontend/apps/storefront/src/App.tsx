import { Route, Routes } from 'react-router-dom';
import { NavBar } from './components/NavBar';
import { RequireAuth } from './components/RequireAuth';
import { MenuBrowse } from './pages/MenuBrowse';
import { MenuItemDetail } from './pages/MenuItemDetail';
import { Login } from './pages/Login';
import { SignUp } from './pages/SignUp';
import { Profile } from './pages/Profile';
import { Cart } from './pages/Cart';
import { Checkout } from './pages/Checkout';
import { OrderDetail } from './pages/OrderDetail';

export default function App() {
  return (
    <div className="min-h-screen flex flex-col bg-bg">
      <NavBar />
      <Routes>
        <Route path="/" element={<MenuBrowse />} />
        <Route path="/menu/:id" element={<MenuItemDetail />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<SignUp />} />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <Profile />
            </RequireAuth>
          }
        />
        <Route
          path="/cart"
          element={
            <RequireAuth>
              <Cart />
            </RequireAuth>
          }
        />
        <Route
          path="/checkout"
          element={
            <RequireAuth>
              <Checkout />
            </RequireAuth>
          }
        />
        <Route
          path="/orders/:id"
          element={
            <RequireAuth>
              <OrderDetail />
            </RequireAuth>
          }
        />
        <Route path="*" element={<NotFound />} />
      </Routes>
    </div>
  );
}

function NotFound() {
  return (
    <div className="flex-grow flex items-center justify-center text-text-secondary">
      <p>Page not found.</p>
    </div>
  );
}

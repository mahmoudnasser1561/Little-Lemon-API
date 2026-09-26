import { request } from './http';
import type { Paginated } from './types';

export interface OrderLineItem {
  order: number;
  menuitem: number | null;
  title: string | null;
  quantity: number;
  price: string;
}

export interface Order {
  id: number;
  user: number;
  delivery_crew: number | null;
  status: boolean;
  date: string;
  total: string;
  orderitem: OrderLineItem[];
}

export const orders = {
  /** GET /api/orders - no trailing slash: a trailing-slash version of this URL does not
   * work on the API (B22, known, still open). */
  list(page?: number): Promise<Paginated<Order>> {
    const qs = page ? `?page=${page}` : '';
    return request(`/api/orders${qs}`);
  },
  get(id: number): Promise<Order> {
    return request(`/api/orders/${id}`);
  },
  /** POST /api/orders - converts the caller's own cart into an order and empties the
   * cart server-side. 400 with {"message": "cart is empty"} if there's nothing to check
   * out (verified against the real API, not assumed). */
  create(): Promise<Order> {
    return request('/api/orders', { method: 'POST', body: JSON.stringify({}) });
  },
};

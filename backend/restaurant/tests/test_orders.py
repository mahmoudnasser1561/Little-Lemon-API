from django.contrib.auth.models import Group
from django.utils import timezone
from rest_framework import status

from cart.models import Cart
from LittleLemonAPI.testing import BaseAPITestCase, known_bug
from restaurant.models import MenuItem, Order, OrderItem

CART = '/api/cart/menu-items'
ORDERS = '/api/orders'
MENU = '/api/menu-items/'


class OrderTestCase(BaseAPITestCase):
    def setUp(self):
        super().setUp()
        self.alice = self.make_customer('alice')
        self.bob = self.make_customer('bob')
        self.manager = self.make_manager()
        self.crew = self.make_crew('crew')
        self.other_crew = self.make_crew('other_crew')
        self.salad = self.make_menu_item('Greek Salad', '12.50')
        self.steak = self.make_menu_item('Steak', '20.00')

    def make_order(self, user, total='25.00', delivery_crew=None, date='2026-01-01'):
        return Order.objects.create(user=user, total=total, date=date, delivery_crew=delivery_crew)

    def add_to_cart(self, client, item, quantity=1):
        return client.post(CART, {'menuitem': item.id, 'quantity': quantity}, format='json')

    def check_out(self, client, **body):
        return client.post(ORDERS, body, format='json')

    def order_ids(self, user):
        return sorted(order['id'] for order in self.list_all(self.client_for(user), ORDERS))

    def snapshot(self, order):
        return Order.objects.values().get(pk=order.pk)


class CheckoutTests(OrderTestCase):
    def test_checkout_turns_the_cart_into_an_order(self):
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad, 2)
        self.add_to_cart(client, self.steak, 1)
        response = self.check_out(client)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total'], '45.00')
        self.assertEqual(response.data['user'], self.alice.id)
        self.assertEqual(response.data['date'], str(timezone.localdate()))
        self.assertIsNone(response.data['delivery_crew'])
        self.assertFalse(response.data['status'])

    def test_checkout_saves_the_ordered_products_at_menu_prices(self):
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad, 2)
        self.add_to_cart(client, self.steak, 1)
        order = Order.objects.get(pk=self.check_out(client).data['id'])
        lines = sorted((line.menuitem.title, line.quantity, str(line.unit_price), str(line.price)) for line in OrderItem.objects.filter(order=order))
        self.assertEqual(lines, [('Greek Salad', 2, '12.50', '25.00'), ('Steak', 1, '20.00', '20.00')])

    def test_checkout_empties_the_cart(self):
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad)
        self.check_out(client)
        self.assertFalse(Cart.objects.filter(user=self.alice).exists())

    def test_checkout_only_takes_the_callers_cart(self):
        self.add_to_cart(self.client_for(self.bob), self.steak)
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad)
        self.check_out(client)
        self.assertEqual(Cart.objects.filter(user=self.bob).count(), 1)
        self.assertEqual(Order.objects.get().user, self.alice)

    def test_anonymous_user_cannot_check_out(self):
        self.assertEqual(self.check_out(self.client_for()).status_code, status.HTTP_401_UNAUTHORIZED)

    def test_checking_out_an_empty_cart_is_a_client_error(self):
        response = self.check_out(self.client_for(self.alice))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)

    def test_a_client_supplied_date_is_ignored(self):
        """B9 and B19 together: the client cannot supply the date at all, so an invalid one is simply irrelevant."""
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad)
        response = self.check_out(client, date='not-a-date')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['date'], str(timezone.localdate()))

    def test_the_order_date_is_set_by_the_server(self):
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad)
        response = client.post(ORDERS, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['date'], str(timezone.localdate()))

    def test_checkout_uses_the_current_menu_price(self):
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad, 2)
        MenuItem.objects.filter(pk=self.salad.pk).update(price='15.00')
        response = self.check_out(client)
        self.assertEqual(response.data['total'], '30.00')
        line = OrderItem.objects.get(order_id=response.data['id'])
        self.assertEqual((str(line.unit_price), str(line.price)), ('15.00', '30.00'))

    @known_bug('B11')
    def test_checking_out_a_huge_total_is_not_a_server_error(self):
        """The checkout side of B11 (the cart side is already fixed by the C4 quantity cap)."""
        client = self.client_for(self.alice)
        expensive = self.make_menu_item('Yacht', '9999.99')
        self.add_to_cart(client, expensive, 2)
        self.assertLess(self.check_out(client).status_code, 500)

    def test_an_order_shows_the_products_that_were_ordered(self):
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad, 2)
        order_id = self.check_out(client).data['id']
        detail = client.get(f'{ORDERS}/{order_id}').data
        [line] = detail['orderitem']
        self.assertEqual((line['title'], line['quantity']), (self.salad.title, 2))

    def test_deleting_a_menu_item_keeps_the_order_history(self):
        """B13: the order line survives with its already-snapshotted price/quantity intact;
        only the now-dangling reference to the deleted menu item goes null."""
        client = self.client_for(self.alice)
        self.add_to_cart(client, self.salad, 2)
        order_id = self.check_out(client).data['id']
        response = self.client_for(self.manager).delete(f'{MENU}{self.salad.id}')
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        line = OrderItem.objects.get(order_id=order_id)
        self.assertIsNone(line.menuitem)
        self.assertEqual((line.quantity, str(line.unit_price), str(line.price)), (2, '12.50', '25.00'))
        self.assertEqual(str(Order.objects.get(pk=order_id).total), '25.00')

    @known_bug('B22')
    def test_the_orders_url_works_with_a_trailing_slash(self):
        self.assertEqual(self.client_for(self.alice).get(f'{ORDERS}/').status_code, status.HTTP_200_OK)


class OrderVisibilityTests(OrderTestCase):
    def setUp(self):
        super().setUp()
        self.alices_order = self.make_order(self.alice, delivery_crew=self.crew)
        self.bobs_order = self.make_order(self.bob)

    def test_a_customer_sees_only_their_own_orders(self):
        self.assertEqual(self.order_ids(self.alice), [self.alices_order.id])
        self.assertEqual(self.order_ids(self.bob), [self.bobs_order.id])

    def test_a_customer_can_open_their_own_order(self):
        response = self.client_for(self.alice).get(f'{ORDERS}/{self.alices_order.id}')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], self.alices_order.id)

    def test_a_customer_cannot_open_someone_elses_order(self):
        self.assertEqual(self.client_for(self.bob).get(f'{ORDERS}/{self.alices_order.id}').status_code, status.HTTP_404_NOT_FOUND)

    def test_a_hidden_order_looks_the_same_as_an_order_that_does_not_exist(self):
        client = self.client_for(self.bob)
        self.assertEqual(client.get(f'{ORDERS}/{self.alices_order.id}').status_code, client.get(f'{ORDERS}/9999').status_code)

    def test_query_parameters_cannot_reveal_other_customers_orders(self):
        client = self.client_for(self.bob)
        for query in (f'?user={self.alice.id}', '?ordering=-user', '?search=alice'):
            with self.subTest(query):
                self.assertEqual([order['id'] for order in self.list_all(client, ORDERS + query)], [self.bobs_order.id])

    def test_a_user_in_an_unknown_group_only_sees_their_own_orders(self):
        kitchen = self.make_customer('kitchen')
        Group.objects.create(name='Kitchen').user_set.add(kitchen)
        own_order = self.make_order(kitchen)
        self.assertEqual(self.order_ids(kitchen), [own_order.id])
        self.assertEqual(self.client_for(kitchen).get(f'{ORDERS}/{self.alices_order.id}').status_code, status.HTTP_404_NOT_FOUND)

    def test_delivery_crew_only_see_their_assigned_orders(self):
        self.assertEqual(self.order_ids(self.crew), [self.alices_order.id])
        self.assertEqual(self.client_for(self.crew).get(f'{ORDERS}/{self.alices_order.id}').status_code, status.HTTP_200_OK)
        self.assertEqual(self.client_for(self.crew).get(f'{ORDERS}/{self.bobs_order.id}').status_code, status.HTTP_404_NOT_FOUND)

    def test_other_delivery_crew_see_nothing_of_it(self):
        self.assertEqual(self.order_ids(self.other_crew), [])
        self.assertEqual(self.client_for(self.other_crew).get(f'{ORDERS}/{self.alices_order.id}').status_code, status.HTTP_404_NOT_FOUND)

    def test_managers_and_superusers_see_every_order(self):
        every_order = sorted([self.alices_order.id, self.bobs_order.id])
        self.assertEqual(self.order_ids(self.manager), every_order)
        self.assertEqual(self.order_ids(self.make_superuser()), every_order)

    def test_anonymous_user_sees_no_orders(self):
        client = self.client_for()
        self.assertEqual(client.get(ORDERS).status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(client.get(f'{ORDERS}/{self.alices_order.id}').status_code, status.HTTP_401_UNAUTHORIZED)

    def test_the_owner_can_use_safe_methods_on_their_order(self):
        client = self.client_for(self.alice)
        url = f'{ORDERS}/{self.alices_order.id}'
        self.assertEqual(client.head(url).status_code, status.HTTP_200_OK)
        self.assertEqual(client.options(url).status_code, status.HTTP_200_OK)


class ManagerOrderUpdateTests(OrderTestCase):
    def setUp(self):
        super().setUp()
        self.order = self.make_order(self.alice)
        self.url = f'{ORDERS}/{self.order.id}'
        self.client = self.client_for(self.manager)

    def test_a_manager_can_assign_a_delivery_crew_member(self):
        response = self.client.patch(self.url, {'delivery_crew': self.crew.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.snapshot(self.order)['delivery_crew_id'], self.crew.id)

    def test_a_manager_can_reassign_and_unassign_the_order(self):
        self.client.patch(self.url, {'delivery_crew': self.crew.id}, format='json')
        self.client.patch(self.url, {'delivery_crew': self.other_crew.id}, format='json')
        self.assertEqual(self.snapshot(self.order)['delivery_crew_id'], self.other_crew.id)
        self.assertEqual(self.client.patch(self.url, {'delivery_crew': None}, format='json').status_code, status.HTTP_200_OK)
        self.assertIsNone(self.snapshot(self.order)['delivery_crew_id'])

    def test_only_a_real_delivery_crew_member_can_be_assigned(self):
        for label, user_id in (('a customer', self.bob.id), ('a manager', self.manager.id), ('the superuser', self.make_superuser().id), ('nobody', 9999), ('garbage', 'abc')):
            with self.subTest(label):
                before = self.snapshot(self.order)
                self.assertEqual(self.client.patch(self.url, {'delivery_crew': user_id}, format='json').status_code, status.HTTP_400_BAD_REQUEST)
                self.assertEqual(self.snapshot(self.order), before)

    def test_a_manager_can_set_the_status(self):
        self.client.patch(self.url, {'status': True}, format='json')
        self.assertTrue(self.snapshot(self.order)['status'])
        self.client.patch(self.url, {'status': False}, format='json')
        self.assertFalse(self.snapshot(self.order)['status'])
        self.assertEqual(self.client.patch(self.url, {'status': 'maybe'}, format='json').status_code, status.HTTP_400_BAD_REQUEST)

    def test_the_answer_has_the_same_fields_as_the_order_itself(self):
        response = self.client.patch(self.url, {'status': True}, format='json')
        self.assertEqual(sorted(response.data), sorted(self.client.get(self.url).data))

    def test_a_manager_cannot_change_customer_data(self):
        before = self.snapshot(self.order)
        changes = {'user': self.manager.id, 'total': '0.01', 'date': '1999-01-01'}
        self.client.patch(self.url, changes, format='json')
        self.client.put(self.url, {**changes, 'status': False, 'delivery_crew': None}, format='json')
        self.assertEqual(self.snapshot(self.order), before)

    def test_customer_data_is_ignored_while_the_delivery_data_is_applied(self):
        self.client.patch(self.url, {'status': True, 'delivery_crew': self.crew.id, 'total': '0.01', 'user': self.manager.id}, format='json')
        order = self.snapshot(self.order)
        self.assertEqual((order['status'], order['delivery_crew_id'], str(order['total']), order['user_id']), (True, self.crew.id, '25.00', self.alice.id))

    def test_orders_cannot_be_deleted(self):
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

    def test_a_manager_can_open_the_order_in_the_browsable_api(self):
        response = self.client.get(self.url, HTTP_ACCEPT='text/html')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.client.options(self.url).status_code, status.HTTP_200_OK)

    @known_bug('B31')
    def test_changing_customer_data_is_an_explicit_error(self):
        self.assertEqual(self.client.patch(self.url, {'total': '0.01'}, format='json').status_code, status.HTTP_400_BAD_REQUEST)


class NoOneElseCanUpdateAnOrderTests(OrderTestCase):
    def test_customers_and_outsiders_cannot_write_to_an_order(self):
        """Everyone except a manager or the order's own assigned delivery crew (covered
        separately in DeliveryCrewOrderUpdateTests) is rejected outright."""
        order = self.make_order(self.alice, delivery_crew=self.crew)
        url = f'{ORDERS}/{order.id}'
        kitchen = self.make_customer('kitchen')
        Group.objects.create(name='Kitchen').user_set.add(kitchen)
        attempt = {'status': True, 'delivery_crew': self.other_crew.id, 'total': '0.01', 'user': self.bob.id}
        for who, user, expected in (
            ('anonymous', None, 401), ('the customer who owns it', self.alice, 403), ('another customer', self.bob, 403),
            ('a superuser outside the Manager group', self.make_superuser(), 403), ('a user in an unknown group', kitchen, 403),
        ):
            client = self.client_for(user)
            with self.subTest(who):
                before = self.snapshot(order)
                self.assertEqual(client.patch(url, attempt, format='json').status_code, expected)
                self.assertEqual(client.put(url, attempt, format='json').status_code, expected)
                self.assertEqual(client.delete(url).status_code, expected)
                self.assertEqual(self.snapshot(order), before)

    def test_delivery_crew_not_assigned_to_the_order_cannot_write_to_it(self):
        """A real delivery crew member passes the coarse permission check, but the order
        isn't in their queryset, so PATCH/PUT are a 404 - same 'looks like it doesn't
        exist' rule already applied to GET for orders outside a user's visibility. DELETE
        is 405 regardless of who's asking, since it's never wired up at all (see
        test_orders_cannot_be_deleted and test_orders_still_cannot_be_deleted_by_crew)."""
        order = self.make_order(self.alice, delivery_crew=self.crew)
        url = f'{ORDERS}/{order.id}'
        client = self.client_for(self.other_crew)
        before = self.snapshot(order)
        self.assertEqual(client.patch(url, {'status': True}, format='json').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(client.put(url, {'status': True}, format='json').status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(client.delete(url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertEqual(self.snapshot(order), before)


class DeliveryCrewOrderUpdateTests(OrderTestCase):
    """A delivery crew member can mark their own assigned order's status, and nothing else."""

    def setUp(self):
        super().setUp()
        self.order = self.make_order(self.alice, delivery_crew=self.crew)
        self.url = f'{ORDERS}/{self.order.id}'
        self.client = self.client_for(self.crew)

    def test_assigned_crew_can_set_the_status(self):
        response = self.client.patch(self.url, {'status': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(self.snapshot(self.order)['status'])
        self.assertFalse(self.client.patch(self.url, {'status': False}, format='json').data['status'])

    def test_assigned_crew_cannot_reassign_the_order(self):
        before = self.snapshot(self.order)
        response = self.client.patch(self.url, {'delivery_crew': self.other_crew.id}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.snapshot(self.order)['delivery_crew_id'], before['delivery_crew_id'])

    def test_assigned_crew_cannot_change_customer_data(self):
        before = self.snapshot(self.order)
        changes = {'user': self.other_crew.id, 'total': '0.01', 'date': '1999-01-01'}
        self.client.patch(self.url, changes, format='json')
        self.client.put(self.url, {**changes, 'status': before['status'], 'delivery_crew': self.crew.id}, format='json')
        self.assertEqual(self.snapshot(self.order), before)

    def test_orders_still_cannot_be_deleted_by_crew(self):
        self.assertEqual(self.client.delete(self.url).status_code, status.HTTP_405_METHOD_NOT_ALLOWED)
        self.assertTrue(Order.objects.filter(pk=self.order.pk).exists())

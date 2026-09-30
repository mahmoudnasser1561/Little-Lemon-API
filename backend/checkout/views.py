from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from django.utils import timezone
from restaurant.permissions import IsManager, IsDeliveryCrew
from cart.services import get_cart_items, get_cart_total, clear_cart
from delivery_crew.services import is_delivery_crew
from .models import Order, OrderItem
from .serializers import DeliveryCrewOrderUpdateSerializer, OrderSerializer, OrderUpdateSerializer

# Managers see all orders, delivery crew only their assigned orders, everyone else only their own
class OrderQuerysetMixin:
    def get_queryset(self):
        user = self.request.user
        if user.is_superuser or user.groups.filter(name='Manager').exists():
            return Order.objects.all()
        elif is_delivery_crew(user):
            return Order.objects.filter(delivery_crew=user)
        return Order.objects.filter(user=user)

class OrderView(OrderQuerysetMixin, generics.ListCreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        menuitem_count = get_cart_items(self.request.user).count()
        if menuitem_count == 0:
            return Response({"message": "cart is empty"}, status=status.HTTP_400_BAD_REQUEST)

        data = {
            'user': self.request.user.id,
            'total': get_cart_total(self.request.user),
            'date': timezone.localdate(),
        }
        order_serializer = OrderSerializer(data=data)
        order_serializer.is_valid(raise_exception=True)
        order = order_serializer.save()

        items = get_cart_items(self.request.user)

        for item in items:
            orderitem = OrderItem(
                order=order,
                menuitem=item.menuitem,
                unit_price=item.menuitem.price,
                price=item.quantity * item.menuitem.price,
                quantity=item.quantity,
            )
            orderitem.save()

        clear_cart(self.request.user)
        return Response(order_serializer.data)


class SingleOrderView(OrderQuerysetMixin, generics.RetrieveUpdateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def get_serializer_class(self):
        if self.request.method in SAFE_METHODS:
            return OrderSerializer

        if is_delivery_crew(self.request.user) and not self.request.user.groups.filter(name='Manager').exists():
            return DeliveryCrewOrderUpdateSerializer
        return OrderUpdateSerializer

    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        if self.request.method not in SAFE_METHODS:
            permission_classes = [IsAuthenticated, IsManager | IsDeliveryCrew]
        return [permission() for permission in permission_classes]

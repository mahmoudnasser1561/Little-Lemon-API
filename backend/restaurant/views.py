from rest_framework import generics, status, viewsets
from rest_framework.permissions import IsAuthenticated, SAFE_METHODS
from rest_framework.response import Response
from django.contrib.auth.models import User
from django.utils import timezone
from .permissions import IsManager, IsDeliveryCrew
from .models import Category, MenuItem
from checkout.models import Order, OrderItem
from checkout.serializers import DeliveryCrewOrderUpdateSerializer, OrderSerializer, OrderUpdateSerializer
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer
from . import caching
from cart.services import get_cart_items, get_cart_total, clear_cart
from delivery_crew.services import is_delivery_crew

# Manager Group Management
class GroupViewSet(viewsets.ViewSet):
    permission_classes = [IsManager]

    # GET /api/groups/manager/users
    def list(self, request):
        users = User.objects.all().filter(groups__name='Manager')
        items = UserSerializer(users, many=True)
        return Response(items.data)

# /api/categories
class CategoriesView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsManager]
        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        cached = caching.get_category_list(request.query_params)
        if cached is not None:
            response = Response(cached)
            response['X-Cache'] = 'HIT'
            return response

        response = super().list(request, *args, **kwargs)
        caching.set_category_list(request.query_params, response.data)
        response['X-Cache'] = 'MISS'
        return response

    def perform_create(self, serializer):
        serializer.save()
        caching.on_category_write()

# /api/menu-items
class MenuItemsView(generics.ListCreateAPIView):
    queryset = MenuItem.objects.all().order_by("id")
    serializer_class = MenuItemSerializer
    search_fields = ['category__title']
    ordering_fields = ['price', 'inventory']

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsManager]

        return [permission() for permission in permission_classes]

    def list(self, request, *args, **kwargs):
        cached = caching.get_menu_list(request.query_params)
        if cached is not None:
            response = Response(cached)
            response['X-Cache'] = 'HIT'
            return response

        response = super().list(request, *args, **kwargs)
        caching.set_menu_list(request.query_params, response.data)
        response['X-Cache'] = 'MISS'
        return response

    def perform_create(self, serializer):
        serializer.save()
        caching.on_menu_item_write()

# /api/menu-items/{menuItem}
class SingleMenuItemView(generics.RetrieveUpdateDestroyAPIView):
    queryset = MenuItem.objects.all()
    serializer_class = MenuItemSerializer

    def get_permissions(self):
        permission_classes = []
        if self.request.method != 'GET':
            permission_classes = [IsAuthenticated, IsManager]

        return [permission() for permission in permission_classes]

    def retrieve(self, request, *args, **kwargs):
        pk = kwargs['pk']
        cached = caching.get_menu_item(pk)
        if cached is not None:
            response = Response(cached)
            response['X-Cache'] = 'HIT'
            return response

        response = super().retrieve(request, *args, **kwargs)
        caching.set_menu_item(pk, response.data)
        response['X-Cache'] = 'MISS'
        return response

    def perform_update(self, serializer):
        instance = serializer.save()
        caching.on_menu_item_write(pk=instance.pk)

    def perform_destroy(self, instance):
        pk = instance.pk
        instance.delete()
        caching.on_menu_item_write(pk=pk)

# Order Management
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

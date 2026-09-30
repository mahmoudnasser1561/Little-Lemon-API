from rest_framework import generics, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth.models import User
from .permissions import IsManager
from .models import Category, MenuItem
from .serializers import CategorySerializer, MenuItemSerializer, UserSerializer
from . import caching

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

from rest_framework import serializers
from django.contrib.auth.models import User
from djoser.serializers import UserSerializer as DjoserUserSerializer
from .models import Category, MenuItem
from delivery_crew.services import is_delivery_crew

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

# Used only for GET/PATCH /api/users/me/ (wired via DJOSER["SERIALIZERS"]["current_user"]
class CurrentUserSerializer(DjoserUserSerializer):
    role = serializers.SerializerMethodField()

    class Meta(DjoserUserSerializer.Meta):
        fields = DjoserUserSerializer.Meta.fields + ('role',)

    def get_role(self, user):
        if user.groups.filter(name='Manager').exists():
            return 'manager'
        if is_delivery_crew(user):
            return 'delivery_crew'
        return 'customer'

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'slug', 'title']

# DRF's plain ImageField wraps its output in request.build_absolute_uri() whenever
# serializer context has a request (which generic views always provide) - that would
# bake in whatever host the request arrived as (e.g. "api", the docker-compose service
# name, once the dev proxy rewrites the Host header), which the browser can't resolve.
# .url alone is exactly right either way: a relative /media/... path under local
# FileSystemStorage (the frontend proxies that path the same way it already does
# /api and /token), or a real, directly-reachable URL once S3Boto3Storage is active.
class RelativeImageField(serializers.ImageField):
    def to_representation(self, value):
        return value.url if value else None

class MenuItemSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    category_id = serializers.IntegerField(write_only=True)
    image = RelativeImageField(required=False, allow_null=True)
    class Meta:
        model = MenuItem
        fields = ['id', 'title', 'price', 'featured', 'category', 'category_id', 'image']

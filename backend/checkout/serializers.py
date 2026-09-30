from rest_framework import serializers
from delivery_crew.services import is_delivery_crew
from .models import Order, OrderItem


class OrderItemSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()

    class Meta:
        model = OrderItem
        fields = ['order', 'menuitem', 'title', 'quantity', 'price']

    def get_title(self, obj):
        return obj.menuitem.title if obj.menuitem else None

class OrderSerializer(serializers.ModelSerializer):
    orderitem = OrderItemSerializer(many=True, read_only=True, source='orderitem_set')

    class Meta:
        model = Order
        fields = ['id', 'user', 'delivery_crew',
                  'status', 'date', 'total', 'orderitem']

# Managers only manage the delivery side of an order (crew assignment and status), customer data is read-only
class OrderUpdateSerializer(OrderSerializer):
    class Meta(OrderSerializer.Meta):
        read_only_fields = ['user', 'total', 'date']

    def validate_delivery_crew(self, value):
        if value is not None and not is_delivery_crew(value):
            raise serializers.ValidationError('User is not a delivery crew member.')
        return value

class DeliveryCrewOrderUpdateSerializer(OrderUpdateSerializer):
    class Meta(OrderUpdateSerializer.Meta):
        read_only_fields = OrderUpdateSerializer.Meta.read_only_fields + ['delivery_crew']

from django.db import models
from django.contrib.auth.models import User
from restaurant.models import MenuItem


class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    delivery_crew = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="delivery_crew", null=True)
    status = models.BooleanField(db_index=True, default=0)
    total = models.DecimalField(max_digits=6, decimal_places=2)
    date = models.DateField(db_index=True)

    class Meta:
        db_table = 'restaurant_order'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    # SET_NULL, not CASCADE: deleting a menu item must not delete the order history that
    menuitem = models.ForeignKey(MenuItem, on_delete=models.SET_NULL, null=True)
    quantity = models.SmallIntegerField()
    unit_price = models.DecimalField(max_digits=6, decimal_places=2)
    price = models.DecimalField(max_digits=6, decimal_places=2)

    class Meta:
        db_table = 'restaurant_orderitem'
        unique_together = ('order', 'menuitem')

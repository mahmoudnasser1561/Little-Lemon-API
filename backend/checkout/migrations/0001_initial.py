# State-only: Order/OrderItem moved here from the restaurant app (see
# restaurant/migrations/0010_remove_orderitem_order_and_more.py). db_table keeps both
# models pointed at their existing restaurant_order/restaurant_orderitem tables, so no
# real database operation runs here - the tables and their data are untouched.

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('restaurant', '0010_remove_orderitem_order_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='Order',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('status', models.BooleanField(db_index=True, default=0)),
                        ('total', models.DecimalField(decimal_places=2, max_digits=6)),
                        ('date', models.DateField(db_index=True)),
                        ('delivery_crew', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='delivery_crew', to=settings.AUTH_USER_MODEL)),
                        ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                    ],
                    options={
                        'db_table': 'restaurant_order',
                    },
                ),
                migrations.CreateModel(
                    name='OrderItem',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('quantity', models.SmallIntegerField()),
                        ('unit_price', models.DecimalField(decimal_places=2, max_digits=6)),
                        ('price', models.DecimalField(decimal_places=2, max_digits=6)),
                        ('menuitem', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='restaurant.menuitem')),
                        ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='checkout.order')),
                    ],
                    options={
                        'db_table': 'restaurant_orderitem',
                        'unique_together': {('order', 'menuitem')},
                    },
                ),
            ],
        ),
    ]

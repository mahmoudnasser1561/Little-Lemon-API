# State-only: Order/OrderItem moved to the checkout app (see checkout/migrations/0001_initial.py).
# No real database operation runs here - the tables stay exactly as they are.

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('restaurant', '0009_menuitem_image'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.RemoveField(
                    model_name='orderitem',
                    name='order',
                ),
                migrations.AlterUniqueTogether(
                    name='orderitem',
                    unique_together=None,
                ),
                migrations.RemoveField(
                    model_name='orderitem',
                    name='menuitem',
                ),
                migrations.DeleteModel(
                    name='Order',
                ),
                migrations.DeleteModel(
                    name='OrderItem',
                ),
            ],
        ),
    ]

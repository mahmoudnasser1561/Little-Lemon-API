from django.db import models, transaction
from django.contrib.auth.models import User, Group, UserManager
from django.contrib.auth.password_validation import validate_password

class Category(models.Model):
    slug = models.SlugField()
    title = models.CharField(max_length=255, db_index=True)
    def __str__(self): return self.title

class MenuItem(models.Model):
    title = models.CharField(max_length=255, db_index=True)
    price = models.DecimalField(max_digits=6, decimal_places=2, db_index=True)
    featured = models.BooleanField(db_index=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    # Optional: most seeded/demo items won't have one, and a manager creating an item
    # shouldn't be forced to attach a photo immediately. Storage backend (local disk vs
    # MinIO/S3) is controlled entirely by STORAGES in settings.py, not by anything here.
    image = models.ImageField(upload_to='menu-items/', blank=True, null=True)
    def __str__(self): return self.title

# Staff roles: a User that belongs to the role's group, created and validated through the role model
class RoleUserManager(UserManager):
    use_in_migrations = False
    role = None

    def get_queryset(self):
        return super().get_queryset().filter(groups__name=self.role)

    def create_user(self, username, password, email=None, **extra_fields):
        user = self.model(username=username, email=self.normalize_email(email), **extra_fields)
        validate_password(password, user)
        user.set_password(password)
        user.full_clean()
        with transaction.atomic():
            user.save(using=self._db)
            user.groups.add(Group.objects.get(name=self.role))
        return user

class ManagerUserManager(RoleUserManager):
    role = 'Manager'

class ManagerUser(User):
    objects = ManagerUserManager()

    class Meta:
        proxy = True
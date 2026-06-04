from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Max, Q
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


class Profile(models.Model):
    ROLE_CLIENT = 'client'
    ROLE_ADMIN = 'admin'
    ROLE_CHOICES = [
        (ROLE_CLIENT, 'Client'),
        (ROLE_ADMIN, 'Admin'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CLIENT)
    address = models.CharField(max_length=255, blank=True, null=True)
    address2 = models.CharField(max_length=255, blank=True, null=True)
    address3 = models.CharField(max_length=255, blank=True, null=True)
    address4 = models.CharField(max_length=255, blank=True, null=True)
    address5 = models.CharField(max_length=255, blank=True, null=True)
    address6 = models.CharField(max_length=255, blank=True, null=True)
    address7 = models.CharField(max_length=255, blank=True, null=True)
    address8 = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=40, blank=True, null=True)

    def __str__(self) -> str:
        return f'{self.user.username} ({self.get_role_display()})'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance: User, created: bool, **kwargs):
    if created:
        Profile.objects.create(user=instance)


class Category(models.Model):
    name = models.CharField(max_length=120, unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name


class Dish(models.Model):
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='dishes/', blank=True, null=True)
    is_available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name

    def active_discount_percent(self) -> int:
        today = timezone.localdate()
        active_offers = self.offers.filter(is_active=True).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=today),
            Q(end_date__isnull=True) | Q(end_date__gte=today),
        )
        return active_offers.aggregate(Max('percent_discount'))['percent_discount__max'] or 0

    def discounted_price(self):
        percent = self.active_discount_percent()
        if not percent:
            return self.price
        return self.price * (100 - percent) / 100


class DishVariant(models.Model):
    dish = models.ForeignKey(Dish, on_delete=models.CASCADE, related_name='variants')
    name = models.CharField(max_length=160)
    price_modifier = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_available = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.dish.name} - {self.name}'

    def get_price(self):
        """Get the total price including modifier and any discounts"""
        base_price = self.dish.price + self.price_modifier
        percent = self.dish.active_discount_percent()
        if not percent:
            return base_price
        return base_price * (100 - percent) / 100

    class Meta:
        unique_together = ('dish', 'name')


class Combo(models.Model):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    dishes = models.ManyToManyField(Dish, blank=True, related_name='combos')
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    def active_discount_percent(self) -> int:
        today = timezone.localdate()
        active_offers = self.offers.filter(is_active=True).filter(
            Q(start_date__isnull=True) | Q(start_date__lte=today),
            Q(end_date__isnull=True) | Q(end_date__gte=today),
        )
        return active_offers.aggregate(Max('percent_discount'))['percent_discount__max'] or 0

    def discounted_price(self):
        percent = self.active_discount_percent()
        if not percent:
            return self.price
        return self.price * (100 - percent) / 100


class Offer(models.Model):
    name = models.CharField(max_length=160)
    description = models.TextField(blank=True)
    percent_discount = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Percentage discount between 1 and 100.',
    )
    is_active = models.BooleanField(default=True)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    dishes = models.ManyToManyField(Dish, blank=True, related_name='offers')
    combos = models.ManyToManyField(Combo, blank=True, related_name='offers')

    def __str__(self) -> str:
        return self.name


class Order(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PAID = 'paid'
    STATUS_PREPARING = 'preparing'
    STATUS_OUT_FOR_DELIVERY = 'out_for_delivery'
    STATUS_COMPLETED = 'completed'
    STATUS_CANCELLED = 'cancelled'
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PAID, 'Paid'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_OUT_FOR_DELIVERY, 'Out for delivery'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    PAYMENT_UNPAID = 'unpaid'
    PAYMENT_PAID = 'paid'
    PAYMENT_REFUNDED = 'refunded'
    PAYMENT_STATUS_CHOICES = [
        (PAYMENT_UNPAID, 'Unpaid'),
        (PAYMENT_PAID, 'Paid'),
        (PAYMENT_REFUNDED, 'Refunded'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_UNPAID
    )
    payment_reference = models.CharField(max_length=120, blank=True)
    delivery_address = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=40)
    notes = models.TextField(blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f'Order #{self.id} - {self.user.username}'


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    dish = models.ForeignKey(Dish, on_delete=models.SET_NULL, null=True, blank=True)
    combo = models.ForeignKey(Combo, on_delete=models.SET_NULL, null=True, blank=True)
    variant = models.ForeignKey(DishVariant, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        item_name = self.dish.name if self.dish else self.combo.name if self.combo else 'Item'
        if self.variant:
            item_name += f' ({self.variant.name})'
        return f'{item_name} x {self.quantity}'

from django.contrib import admin

from .models import MenuCategory, Combo, MenuItem, MenuItemVariant, Offer, Order, OrderItem, Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role')
    list_select_related = ('user',)


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'isactive')
    list_filter = ('isactive',)
    search_fields = ('name',)


class MenuItemVariantInline(admin.TabularInline):
    model = MenuItemVariant
    extra = 1
    fields = ('name', 'price_modifier', 'is_available')


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_available')
    list_filter = ('is_available', 'category')
    search_fields = ('name',)
    inlines = [MenuItemVariantInline]


@admin.register(Combo)
class ComboAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('dishes',)


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'percent_discount', 'is_active', 'start_date', 'end_date')
    list_filter = ('is_active',)
    search_fields = ('name',)
    filter_horizontal = ('dishes', 'combos')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'user',
        'status',
        'payment_status',
        'total_amount',
        'created_at',
    )
    list_filter = ('status', 'payment_status')
    search_fields = ('user__username', 'payment_reference')
    inlines = [OrderItemInline]

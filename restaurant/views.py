from decimal import Decimal
import json

from django.contrib import messages
from django.contrib.auth import authenticate, login as auth_login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from .forms import (
    MenuCategoryForm,
    ComboForm,
    MenuItemForm,
    OfferForm,
    OrderCreateForm,
    OrderStatusForm,
    ProfileForm,
    RegistrationForm,
    UserRoleForm,
)
from .models import MenuCategory, Combo, MenuItem, MenuItemVariant, Offer, Order, OrderItem, Profile


def login_view(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None and user.profile.role == Profile.ROLE_ADMIN:
                auth_login(request, user)
                return redirect('admin_dashboard')
            elif user is not None and user.profile.role == Profile.ROLE_CLIENT:
                auth_login(request, user)
                return redirect('client_dashboard')
    else:
        if request.user.is_authenticated:
            if is_admin(request.user):
                return redirect('admin_dashboard')
            return redirect('client_dashboard')
        return render(
            request,
            'restaurant/home2.html',
        )


def logout_view(request):
    logout(request)
    return redirect('home')
def is_admin(user) -> bool:
    if not user.is_authenticated:
        return False
    if user.is_superuser or user.is_staff:
        return True
    return hasattr(user, 'profile') and user.profile.role == Profile.ROLE_ADMIN


def is_client(user) -> bool:
    return user.is_authenticated and hasattr(user, 'profile') and user.profile.role == Profile.ROLE_CLIENT


def admin_required(view_func):
    return user_passes_test(is_admin, login_url='login')(view_func)


def client_required(view_func):
    return user_passes_test(is_client, login_url='login')(view_func)


def home(request):

    dishes = MenuItem.objects.filter(is_available=True).select_related('category')
    combos = Combo.objects.filter(is_active=True).prefetch_related('dishes')
    offers = Offer.objects.filter(is_active=True)
    categories = MenuCategory.objects.filter(is_active=True).order_by('name')
    cart_items, cart_total = _build_cart_items(_get_cart(request))
    
    return render(
        request,
        'restaurant/home_dashboard.html',
        {
            'dishes': dishes,
            'combos': combos,
            'offers': offers,
            'categories': categories,
            'cart_items': cart_items,
            'cart_total': cart_total,
        },
    )
    


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        print(form.errors)
        print(form.is_valid())
        if form.is_valid():
            user = form.save()
            auth_login(request, user)
            messages.success(request, 'Account created successfully.')
            return redirect('client_dashboard')
        else:
            return redirect('home')
    else:
        return redirect('home')


def _get_cart(request):
    return request.session.get('cart', {})


def _set_cart(request, cart):
    request.session['cart'] = cart
    request.session.modified = True


def _cart_key(kind: str, item_id: int, variant_id: int = None) -> str:
    """Generate cart key with optional variant"""
    if variant_id:
        return f'{kind}:{item_id}:v{variant_id}'
    return f'{kind}:{item_id}'


def _build_cart_items(cart):
    dish_ids = []
    variant_ids = []
    combo_ids = []
    
    for key in cart:
        if key.startswith('dish:'):
            parts = key.split(':')
            dish_ids.append(int(parts[1]))
            if len(parts) > 2:  # Has variant
                variant_ids.append(int(parts[2][1:]))
        elif key.startswith('combo:'):
            combo_ids.append(int(key.split(':')[1]))

    dishes = {dish.id: dish for dish in MenuItem.objects.filter(id__in=dish_ids, is_available=True).prefetch_related('variants')}
    variants = {v.id: v for v in MenuItemVariant.objects.filter(id__in=variant_ids, is_available=True)} if variant_ids else {}
    combos = {combo.id: combo for combo in Combo.objects.filter(id__in=combo_ids, is_active=True)}

    items = []
    total = Decimal('0.00')

    for key, quantity in cart.items():
        if key.startswith('dish:'):
            parts = key.split(':')
            dish_id = int(parts[1])
            variant_id = int(parts[2][1:]) if len(parts) > 2 else None
            
            dish = dishes.get(dish_id)
            if not dish:
                continue
            
            variant = variants.get(variant_id) if variant_id else None
            
            # Calculate price based on variant or base dish
            if variant:
                unit_price = variant.get_price()
                variant_name = variant.name
            else:
                unit_price = Decimal(str(dish.discounted_price()))
                variant_name = None
            
            line_total = unit_price * quantity
            items.append(
                {
                    'key': key,
                    'type': 'dish',
                    'object': dish,
                    'variant': variant,
                    'variant_name': variant_name,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'line_total': line_total,
                }
            )
            total += line_total
        elif key.startswith('combo:'):
            combo_id = int(key.split(':')[1])
            combo = combos.get(combo_id)
            if not combo:
                continue
            unit_price = Decimal(str(combo.discounted_price()))
            line_total = unit_price * quantity
            items.append(
                {
                    'key': key,
                    'type': 'combo',
                    'object': combo,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'line_total': line_total,
                }
            )
            total += line_total

    return items, total


def _format_cart_for_ajax(items, total):
    """Format cart data for AJAX response"""
    formatted_items = []
    for item in items:
        name = item['object'].name
        if item.get('variant_name'):
            name += f" ({item['variant_name']})"
        
        formatted_items.append({
            'key': item['key'],
            'type': item['type'],
            'name': name,
            'image': item['object'].image.url if item['object'].image else None,
            'quantity': item['quantity'],
            'unit_price': float(item['unit_price']),
            'line_total': float(item['line_total']),
        })
    return {
        'items': formatted_items,
        'total': float(total),
        'count': len(items),
    }


@client_required
@require_http_methods(["POST"])
def api_cart_add(request):
    """AJAX endpoint to add item to cart"""
    try:
        data = json.loads(request.body)
        item_type = data.get('type')  # 'dish' or 'combo'
        item_id = data.get('id')
        variant_id = data.get('variant_id')  # Optional variant ID
        
        if item_type == 'dish':
            item = get_object_or_404(MenuItem, id=item_id, is_available=True)
            
            # Validate variant if provided
            if variant_id:
                variant = get_object_or_404(MenuItemVariant, id=variant_id, dish=item, is_available=True)
            
        elif item_type == 'combo':
            item = get_object_or_404(Combo, id=item_id, is_active=True)
        else:
            return JsonResponse({'error': 'Invalid item type'}, status=400)
        
        cart = _get_cart(request)
        key = _cart_key(item_type, item_id, variant_id)
        cart[key] = cart.get(key, 0) + 1
        _set_cart(request, cart)
        
        items, total = _build_cart_items(cart)
        return JsonResponse({
            'success': True,
            'message': f'Added {item.name} to cart',
            'cart': _format_cart_for_ajax(items, total),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@client_required
@require_http_methods(["POST"])
def api_cart_update_quantity(request):
    """AJAX endpoint to update item quantity"""
    try:
        data = json.loads(request.body)
        item_key = data.get('key')
        quantity = int(data.get('quantity', 0))
        
        cart = _get_cart(request)
        
        if quantity <= 0:
            cart.pop(item_key, None)
        else:
            if item_key in cart:
                cart[item_key] = quantity
        
        _set_cart(request, cart)
        items, total = _build_cart_items(cart)
        
        return JsonResponse({
            'success': True,
            'cart': _format_cart_for_ajax(items, total),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@client_required
@require_http_methods(["POST"])
def api_cart_remove(request):
    """AJAX endpoint to remove item from cart"""
    try:
        data = json.loads(request.body)
        item_key = data.get('key')
        
        cart = _get_cart(request)
        if item_key in cart:
            cart.pop(item_key, None)
        
        _set_cart(request, cart)
        items, total = _build_cart_items(cart)
        
        return JsonResponse({
            'success': True,
            'message': 'Item removed from cart',
            'cart': _format_cart_for_ajax(items, total),
        })
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)


@client_required
@require_http_methods(["GET"])
def client_dashboard(request):
    
    dishes = MenuItem.objects.filter(is_available=True).select_related('category')
    combos = Combo.objects.filter(is_active=True).prefetch_related('dishes')
    offers = Offer.objects.filter(is_active=True)
    categories = MenuCategory.objects.filter(is_active=True).order_by('name')
    cart_items, cart_total = _build_cart_items(_get_cart(request))
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(
        request,
        'restaurant/client_dashboard_glovo.html',
        {
            'dishes': dishes,
            'combos': combos,
            'offers': offers,
            'categories': categories,
            'cart_items': cart_items,
            'cart_total': cart_total,
            'recent_orders': recent_orders,
        },
    )


@login_required(login_url='login')
@require_http_methods(["GET", "POST"])
def update_client_profile(request):
    """Update client profile data (address and phone number)"""
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully.')
            return redirect('client_dashboard')
    else:
        form = ProfileForm(instance=request.user.profile)
    
    return render(request, 'restaurant/update_client_profile.html', {'form': form})


@client_required
@require_http_methods(["GET"])
def api_cart_get(request):
    """AJAX endpoint to get current cart"""
    cart = _get_cart(request)
    items, total = _build_cart_items(cart)
    return JsonResponse({
        'success': True,
        'cart': _format_cart_for_ajax(items, total),
    })



    dishes = MenuItem.objects.filter(is_available=True).select_related('category')
    combos = Combo.objects.filter(is_active=True).prefetch_related('dishes')
    offers = Offer.objects.filter(is_active=True)
    categories = MenuCategory.objects.filter(is_active=True).order_by('name')
    cart_items, cart_total = _build_cart_items(_get_cart(request))
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    return render(
        request,
        'restaurant/client_dashboard_glovo.html',
        {
            'dishes': dishes,
            'combos': combos,
            'offers': offers,
            'categories': categories,
            'cart_items': cart_items,
            'cart_total': cart_total,
            'recent_orders': recent_orders,
        },
    )


@client_required
def cart_add_dish(request, dish_id):
    if request.method != 'POST':
        return redirect('client_dashboard')
    dish = get_object_or_404(MenuItem, id=dish_id, is_available=True)
    cart = _get_cart(request)
    key = _cart_key('dish', dish.id)
    cart[key] = cart.get(key, 0) + 1
    _set_cart(request, cart)
    messages.success(request, f'Added {dish.name} to your cart.')
    return redirect('client_dashboard')


@client_required
def cart_add_combo(request, combo_id):
    if request.method != 'POST':
        return redirect('client_dashboard')
    combo = get_object_or_404(Combo, id=combo_id, is_active=True)
    cart = _get_cart(request)
    key = _cart_key('combo', combo.id)
    cart[key] = cart.get(key, 0) + 1
    _set_cart(request, cart)
    messages.success(request, f'Added {combo.name} to your cart.')
    return redirect('client_dashboard')


@client_required
def cart_update(request):
    if request.method != 'POST':
        return redirect('client_dashboard')
    cart = _get_cart(request)
    for key, value in request.POST.items():
        if not key.startswith('qty_'):
            continue
        item_key = key.replace('qty_', '')
        if item_key in cart:
            quantity = max(0, int(value))
            if quantity == 0:
                cart.pop(item_key, None)
            else:
                cart[item_key] = quantity
    _set_cart(request, cart)
    messages.success(request, 'Cart updated.')
    return redirect('client_dashboard')


@client_required
def cart_remove(request, item_key):
    cart = _get_cart(request)
    if item_key in cart:
        cart.pop(item_key, None)
        _set_cart(request, cart)
        messages.info(request, 'Item removed from cart.')
    return redirect('client_dashboard')


@client_required
@transaction.atomic
def checkout(request):
    cart_items, cart_total = _build_cart_items(_get_cart(request))
    if not cart_items:
        messages.warning(request, 'Your cart is empty.')
        return redirect('client_dashboard')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.user = request.user
            order.total_amount = cart_total
            order.save()

            for item in cart_items:
                OrderItem.objects.create(
                    order=order,
                    dish=item['object'] if item['type'] == 'dish' else None,
                    combo=item['object'] if item['type'] == 'combo' else None,
                    quantity=item['quantity'],
                    unit_price=item['unit_price'],
                    line_total=item['line_total'],
                )

            _set_cart(request, {})
            messages.success(request, 'Order created. Complete payment to confirm.')
            return redirect('payment_placeholder', order_id=order.id)
    else:
        form = OrderCreateForm()

    return render(
        request,
        'restaurant/checkout.html',
        {
            'form': form,
            'cart_items': cart_items,
            'cart_total': cart_total,
            'user_address': request.user.profile.address if hasattr(request.user, 'profile') else None,
            'user_phone': request.user.profile.phone_number if hasattr(request.user, 'profile') else None,
        },
    )


@client_required
def payment_placeholder(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.payment_status == Order.PAYMENT_PAID:
        return redirect('order_tracking')

    if request.method == 'POST':
        order.payment_status = Order.PAYMENT_PAID
        order.status = Order.STATUS_PAID
        order.payment_reference = f'CMI-SIM-{order.id}-{timezone.now().strftime("%Y%m%d%H%M%S")}'
        order.save(update_fields=['payment_status', 'status', 'payment_reference'])
        messages.success(request, 'Payment simulated successfully.')
        return redirect('order_tracking')

    return render(request, 'restaurant/payment_placeholder.html', {'order': order})


@client_required
def order_tracking(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at').prefetch_related('items')
    return render(request, 'restaurant/order_tracking.html', {'orders': orders})


@admin_required
def admin_dashboard(request):
    stats = {
        'dishes': MenuItem.objects.count(),
        'combos': Combo.objects.count(),
        'offers': Offer.objects.count(),
        'orders': Order.objects.count(),
        'pending_orders': Order.objects.filter(status=Order.STATUS_PENDING).count(),
    }
    return render(request, 'restaurant/admin_dashboard.html', {'stats': stats})


@admin_required
def admin_categories(request):
    if request.method == 'POST':
        form = MenuCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'MenuCategory saved.')
            return redirect('admin_categories')
    else:
        form = MenuCategoryForm()
    categories = MenuCategory.objects.order_by('name')
    return render(
        request,
        'restaurant/admin_categories.html',
        {'form': form, 'categories': categories},
    )


@admin_required
@admin_required
def admin_dishes(request):
    dishes = MenuItem.objects.select_related('category').order_by('name')
    categories = MenuCategory.objects.filter(is_active=True).order_by('name')
    return render(request, 'restaurant/admin_dishes.html', {
        'dishes': dishes,
        'categories': categories,
    })


@admin_required
def admin_dish_create(request):
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'MenuItem created.'})
            messages.success(request, 'MenuItem created.')
            return redirect('admin_dishes')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = MenuItemForm()
    return render(request, 'restaurant/admin_dish_form.html', {'form': form, 'title': 'New MenuItem'})


@admin_required
def admin_dish_edit(request, dish_id):
    dish = get_object_or_404(MenuItem, id=dish_id)
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=dish)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'MenuItem updated.'})
            messages.success(request, 'MenuItem updated.')
            return redirect('admin_dishes')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = MenuItemForm(instance=dish)
    return render(request, 'restaurant/admin_dish_form.html', {'form': form, 'title': 'Edit MenuItem'})


@admin_required
def admin_dish_delete(request, dish_id):
    dish = get_object_or_404(MenuItem, id=dish_id)
    if request.method == 'POST':
        dish.delete()
        messages.info(request, 'MenuItem deleted.')
    return redirect('admin_dishes')


@admin_required
@require_http_methods(["GET"])
def admin_dish_data(request, dish_id):
    """Fetch dish data as JSON for modal editing"""
    dish = get_object_or_404(MenuItem, id=dish_id)
    return JsonResponse({
        'id': dish.id,
        'name': dish.name,
        'description': '',
        'price': str(dish.price),
        'category': dish.category_id,
        'is_available': dish.is_available,
    })


@admin_required
def admin_combos(request):
    combos = Combo.objects.prefetch_related('dishes').order_by('name')
    dishes = MenuItem.objects.filter(is_available=True).order_by('name')
    return render(request, 'restaurant/admin_combos.html', {
        'combos': combos,
        'dishes': dishes,
    })


@admin_required
def admin_combo_create(request):
    if request.method == 'POST':
        form = ComboForm(request.POST)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Combo created.'})
            messages.success(request, 'Combo created.')
            return redirect('admin_combos')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = ComboForm()
    return render(request, 'restaurant/admin_combo_form.html', {'form': form, 'title': 'New Combo'})


@admin_required
def admin_combo_edit(request, combo_id):
    combo = get_object_or_404(Combo, id=combo_id)
    if request.method == 'POST':
        form = ComboForm(request.POST, instance=combo)
        if form.is_valid():
            form.save()
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': 'Combo updated.'})
            messages.success(request, 'Combo updated.')
            return redirect('admin_combos')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'errors': form.errors}, status=400)
    else:
        form = ComboForm(instance=combo)
    return render(request, 'restaurant/admin_combo_form.html', {'form': form, 'title': 'Edit Combo'})


@admin_required
def admin_combo_delete(request, combo_id):
    combo = get_object_or_404(Combo, id=combo_id)
    if request.method == 'POST':
        combo.delete()
        messages.info(request, 'Combo deleted.')
    return redirect('admin_combos')


@admin_required
@require_http_methods(["GET"])
def admin_combo_data(request, combo_id):
    """Fetch combo data as JSON for modal editing"""
    combo = get_object_or_404(Combo, id=combo_id)
    return JsonResponse({
        'id': combo.id,
        'name': combo.name,
        'description': combo.description or '',
        'price': str(combo.price),
        'is_active': combo.is_active,
        'dishes': list(combo.dishes.values_list('id', flat=True)),
    })


@admin_required
def admin_offers(request):
    offers = Offer.objects.order_by('-id')
    dishes = MenuItem.objects.all()
    combos = Combo.objects.all()
    return render(request, 'restaurant/admin_offers.html', {'offers': offers, 'dishes': dishes, 'combos': combos})


@admin_required
def admin_offer_create(request):
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Offer created.')
            return redirect('admin_offers')
    else:
        form = OfferForm()
    return render(request, 'restaurant/admin_offer_form.html', {'form': form, 'title': 'New Offer'})


@admin_required
def admin_offer_edit(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    if request.method == 'POST':
        form = OfferForm(request.POST, instance=offer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Offer updated.')
            return redirect('admin_offers')
    else:
        form = OfferForm(instance=offer)
    return render(request, 'restaurant/admin_offer_form.html', {'form': form, 'title': 'Edit Offer'})


@admin_required
def admin_offer_delete(request, offer_id):
    offer = get_object_or_404(Offer, id=offer_id)
    if request.method == 'POST':
        offer.delete()
        messages.info(request, 'Offer deleted.')
    return redirect('admin_offers')


@admin_required
def admin_orders(request):
    orders = Order.objects.select_related('user').order_by('-created_at')
    pending_count = orders.filter(status=Order.STATUS_PENDING).count()
    completed_count = orders.filter(status=Order.STATUS_COMPLETED).count()
    paid_count = orders.filter(payment_status=Order.PAYMENT_PAID).count()
    return render(
        request,
        'restaurant/admin_orders.html',
        {
            'orders': orders,
            'pending_count': pending_count,
            'completed_count': completed_count,
            'paid_count': paid_count,
        },
    )


@admin_required
def admin_order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        form = OrderStatusForm(request.POST, instance=order)
        if form.is_valid():
            form.save()
            messages.success(request, 'Order status updated.')
            return redirect('admin_order_detail', order_id=order.id)
    else:
        form = OrderStatusForm(instance=order)
    return render(
        request,
        'restaurant/admin_order_detail.html',
        {'order': order, 'form': form},
    )


@admin_required
def admin_users(request):
    users = Profile.objects.select_related('user').order_by('user__username')
    if request.method == 'POST':
        profile = get_object_or_404(Profile, id=request.POST.get('profile_id'))
        form = UserRoleForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'User role updated.')
        return redirect('admin_users')
    return render(request, 'restaurant/admin_users.html', {'users': users})

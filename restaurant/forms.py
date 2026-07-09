from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import MenuCategory, Combo, MenuItem, Offer, Order, Profile


class RegistrationForm(UserCreationForm):
    # email = forms.EmailField(required=True)  # Not necessary for now

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2')
    
    def clean_password2(self):
        # Override to disable Django's password validation
        return self.cleaned_data.get('password2')


class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('address', 'phone_number')
        widgets = {
            'address': forms.TextInput(attrs={'placeholder': 'Enter your address'}),
            'phone_number': forms.TextInput(attrs={'placeholder': 'Enter your phone number'}),
        }


class MenuCategoryForm(forms.ModelForm):
    class Meta:
        model = MenuCategory
        fields = ('name', 'isactive')


class MenuItemForm(forms.ModelForm):
    class Meta:
        model = MenuItem
        fields = ('category', 'name', 'price', 'image', 'is_available')


class ComboForm(forms.ModelForm):
    class Meta:
        model = Combo
        fields = ('name', 'price', 'dishes', 'is_active')
        widgets = {
            'dishes': forms.CheckboxSelectMultiple,
        }


class OfferForm(forms.ModelForm):
    class Meta:
        model = Offer
        fields = (
            'name',
            'percent_discount',
            'is_active',
            'start_date',
            'end_date',
            'dishes',
            'combos',
        )
        widgets = {
            'dishes': forms.CheckboxSelectMultiple,
            'combos': forms.CheckboxSelectMultiple,
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }


class OrderCreateForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('delivery_address', 'phone_number', 'notes')
        widgets = {
            'notes': forms.Textarea(attrs={'rows': 3}),
        }


class OrderStatusForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ('status',)


class UserRoleForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('role',)

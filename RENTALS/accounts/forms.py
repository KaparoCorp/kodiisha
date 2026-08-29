from django import forms
from django.contrib.auth.models import User
from django.utils import timezone

from .models import Invitation, Profile
from properties.models import Property
from django.contrib.auth.forms import UserCreationForm

class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=True, widget=forms.TextInput(attrs={'class': 'form-control'}))
    role = forms.ChoiceField(
        choices=Profile.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        initial=Profile.LANDLORD,
        required=True,
    )

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2', 'role']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap styling to password fields
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Set profile role from form data
            role = self.cleaned_data.get('role', Profile.LANDLORD)
            user.profile.role = role
            user.profile.save(update_fields=['role'])
        return user
    
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }

class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'avatar', 'notification_enabled']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. +1 234 567 890'}),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }


class InvitationCreateForm(forms.ModelForm):
    properties = forms.ModelMultipleChoiceField(
        queryset=Property.objects.none(),
        widget=forms.SelectMultiple(attrs={
            'class': 'form-control tom-select-multi',
            'placeholder': 'Search and select properties...',
        }),
        required=True,
        help_text='Select one or more properties to grant access to.',
    )

    class Meta:
        model = Invitation
        fields = ['email', 'first_name', 'last_name', 'role', 'properties']
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'name@example.com'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self._user = user
        super().__init__(*args, **kwargs)
        if user:
            self.fields['properties'].queryset = Property.objects.filter(user=user)
        self.fields['properties'].label = 'Grant Access To Properties'

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        pending_invite = Invitation.objects.filter(
            email__iexact=email,
            status=Invitation.PENDING,
            expires_at__gt=timezone.now(),
        ).exists()
        if pending_invite:
            raise forms.ValidationError('There is already a pending invitation for this email.')
        return email


class InvitationAcceptForm(UserCreationForm):
    email = forms.EmailField(required=True, disabled=True)
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))
    last_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={'class': 'form-control'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, invitation=None, **kwargs):
        self.invitation = invitation
        initial = kwargs.setdefault('initial', {})
        if invitation:
            initial.setdefault('email', invitation.email)
            initial.setdefault('first_name', invitation.first_name)
            initial.setdefault('last_name', invitation.last_name)
        super().__init__(*args, **kwargs)
        self.fields['email'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.invitation.email if self.invitation else self.cleaned_data['email']
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('A user with this email already exists.')
        return email

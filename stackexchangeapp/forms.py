from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Stack

class UserCreationFormStackApp(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class StackCreationForm(forms.ModelForm):
    class Meta:
        model = Stack
        fields = ("title", "description")
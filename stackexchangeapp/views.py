from django.shortcuts import render
from .forms import UserCreationFormStackApp, StackCreationForm
from django.urls import reverse_lazy
from django.views.generic import CreateView, TemplateView
from .models import *
# Create your views here.

class SignUpView(CreateView):
    form_class = UserCreationFormStackApp
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

class HomeView(TemplateView):
    template_name = "home.html"
    stacks = Stack.objects.all()
    def get(self, request, *args, **kwargs):
        context = {"user": request.user, "stacks": self.stacks}
        return render(request, self.template_name, context)

class StackCreationView(CreateView):
    template_name = "stack_creation.html"
    form_class = StackCreationForm
    success_url = reverse_lazy("home")
    model = Stack
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
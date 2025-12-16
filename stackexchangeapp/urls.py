from django.urls import path, include
from .views import SignUpView, HomeView, StackCreationView
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', login_required(HomeView.as_view()), name="home"),
    path('accounts/signup/', SignUpView.as_view(), name="signup"),
    path('accounts/', include("django.contrib.auth.urls")),
    path('create-stack/', login_required(StackCreationView.as_view()), name="create_stack")
]
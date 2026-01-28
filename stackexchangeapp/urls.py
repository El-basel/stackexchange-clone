from django.urls import path, include
from .views import *
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('', HomeView.as_view(), name="home"),
    path('accounts/signup/', SignUpView.as_view(), name="signup"),
    path('accounts/', include("django.contrib.auth.urls")),
    path('create-stack/', StackCreationView.as_view(), name="create_stack"),
    path('join-stack/<int:stack_id>', JoinStackView.as_view(), name="join_stack"),
    path('leave-stack/<int:stack_id>', LeaveStackView.as_view(), name="leave_stack"),
    path('stack/<int:stack_id>/ask', AskQuestionView.as_view(),name="ask_question"),
    path('stack/<int:stack_id>/<slug:stack_slug>', StackDetailView.as_view(),name="stack"),
    path('stack/<int:stack_id>/question/<int:question_id>', QuestionDetailView.as_view(), name="question_detail"),
    path('stack/<int:stack_id>/question/<int:question_id>/<str:vote_type>', UpDownVoteView.as_view(), name='question_vote'),
    path('stack/<int:stack_id>/answer/<int:question_id>/<int:answer_id>/<str:vote_type>', UpDownVoteView.as_view(), name='answer_vote'),
]
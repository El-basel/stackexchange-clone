from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserCreationFormStackApp, StackCreationForm, QuestionForm, AnswerForm
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView, View, DetailView
from django.views.generic.edit import FormMixin
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
# Create your views here.

class SignUpView(CreateView):
    form_class = UserCreationFormStackApp
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"
    stacks = Stack.objects.all()
    def get(self, request, *args, **kwargs):
        joined_stacks_ids = StackMembership.objects.filter(user=request.user).values_list('stack_id', flat=True)
        context = {"user": request.user, "stacks": self.stacks, 'joined_stacks_ids':joined_stacks_ids}
        return render(request, self.template_name, context)

class StackCreationView(LoginRequiredMixin, CreateView):
    template_name = "stack_creation.html"
    form_class = StackCreationForm
    success_url = reverse_lazy("home")
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        StackMembership.objects.create(user=self.request.user, stack=form.instance, reputation = 0)
        return response
    
class JoinStackView(LoginRequiredMixin, CreateView):
    def post(self, request, *args, **kwargs):
        stack_id = kwargs['stack_id']
        stack = Stack.objects.get(pk=stack_id)
        StackMembership.objects.get_or_create(user=request.user, stack=stack, defaults={'reputation':0})
        return redirect('home')
    
class LeaveStackView(LoginRequiredMixin, CreateView):
    def post(self, request, *args, **kwargs):
        stack_id = kwargs['stack_id']
        stack = Stack.objects.get(pk=stack_id)
        StackMembership.objects.filter(user=request.user, stack=stack).delete()
        return redirect('home')
    
class StackDetailView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        stack = Stack.objects.get(pk=kwargs['stack_id'])
        context = {'stack': stack, 'questions':stack.questions.all()}
        return render(request, 'stack.html', context)

class AskQuestionView(LoginRequiredMixin, CreateView):
    form_class = QuestionForm
    template_name = 'ask_question.html'
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['stack'] = get_object_or_404(Stack, id=self.kwargs['stack_id'])
        return kwargs

    def form_valid(self, form):
        stack = get_object_or_404(Stack, id=self.kwargs['stack_id'])
        form.instance.asked_by = self.request.user
        form.instance.stack = stack
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('stack', kwargs={
            'stack_id': self.object.stack.id,
            'stack_slug': self.object.stack.slug,
        })
    
class QuestionDetailView(LoginRequiredMixin, DetailView, FormMixin):
    template_name = "question_detail.html"
    model = Question
    context_object_name = 'question'
    pk_url_kwarg = 'question_id'
    form_class = AnswerForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        answers = self.object.answer_set.annotate(
            vote_score=Count('vote', filter=Q(vote__vote_type='up')) -
                        Count('vote', filter=Q(vote__vote_type='down'))
        ).order_by('-vote_score', '-created_at')
        context['answers'] = answers
        if 'form' not in context:
            context['form'] = self.get_form()
        return context
    
    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()

        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        
    def form_valid(self, form):
        answer = form.save(commit=False)
        answer.question = self.object
        answer.answered_by = self.request.user
        answer.save()

        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('question_detail', kwargs={
            'stack_id': self.object.stack.id,
            'question_id':self.object.id,
        })

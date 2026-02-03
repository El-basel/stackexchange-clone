from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserCreationFormStackApp, StackCreationForm, QuestionForm, AnswerForm
from django.urls import reverse_lazy, reverse
from django.views.generic import CreateView, TemplateView, View, DetailView
from django.views.generic.edit import FormMixin
from .models import *
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q, Count
# Create your views here.

class ErrorView():
    def get(request):
        return render(request, '404.html')

class SignUpView(CreateView):
    form_class = UserCreationFormStackApp
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"

class HomeView(LoginRequiredMixin, TemplateView):
    template_name = "home.html"
    def get(self, request, *args, **kwargs):
        stacks = Stack.objects.all()
        joined_stacks_ids = StackMembership.objects.filter(user=request.user).values_list('stack_id', flat=True)
        context = {"user": request.user, "stacks": stacks, 'joined_stacks_ids':joined_stacks_ids}
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
        stack = get_object_or_404(Stack, pk=stack_id)
        StackMembership.objects.get_or_create(user=request.user, stack=stack, defaults={'reputation':0})
        return redirect('home')
    
class LeaveStackView(LoginRequiredMixin, CreateView):
    def post(self, request, *args, **kwargs):
        stack_id = kwargs['stack_id']
        stack = get_object_or_404(Stack, pk=stack_id)
        StackMembership.objects.filter(user=request.user, stack=stack).delete()
        return redirect('home')
    
class StackDetailView(LoginRequiredMixin, View):
    def get(self, request, *args, **kwargs):
        stack = Stack.objects.get(pk=kwargs['stack_id'])
        membership = get_object_or_404(StackMembership, user=request.user, stack=stack)
        context = {'stack': stack, 'questions':stack.questions.all(), 'membership':membership}
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
            vote_score=Count('vote', filter=Q(vote__vote_type=True)) -
                        Count('vote', filter=Q(vote__vote_type=False))
        ).order_by('-vote_score')
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

class AcceptAnswerView(View):
    def post(self, request, stack_id, question_id, answer_id):
        answer = get_object_or_404(Answer, id=answer_id)
        accepted_answer = Answer.objects.filter(question=answer.question, is_accepted=True).first()
        accept = request.POST.get('accept', '')
        if accepted_answer:
            accepted_answer.is_accepted = False
            answer.is_accepted = True
            answer.save()
            accepted_answer.save()
        else:
            if accept == "True":
                answer.is_accepted=True
                answer.save()
            elif accept == "False":
                answer.is_accepted=False
                answer.save()
        return redirect('question_detail', stack_id=stack_id, question_id=question_id)

class UpDownVoteView(LoginRequiredMixin, View):
    def post(self, request, stack_id, question_id, vote_type, answer_id=None):
        # Get objects
        stack = get_object_or_404(Stack, pk=stack_id)
        question = get_object_or_404(Question, pk=question_id)
        answer = get_object_or_404(Answer, pk=answer_id) if answer_id else None
        
        # Determine what we're voting on
        if answer:
            target_object = answer
            content_owner = answer.answered_by
            vote_filter = {'user': request.user, 'answer': answer}
            vote_create = {'answer': answer}
        else:
            target_object = question
            content_owner = question.asked_by
            vote_filter = {'user': request.user, 'question': question}
            vote_create = {'question': question}
        
        # Can't vote on your own content
        if request.user == content_owner:
            return redirect('question_detail', stack_id=stack_id, question_id=question_id)
        
        # Get memberships
        owner_membership = StackMembership.objects.filter(
            user=content_owner, 
            stack=stack
        ).first()
        
        voter_membership = StackMembership.objects.filter(
            user=request.user, 
            stack=stack
        ).first()
        
        # Check memberships exist
        if not owner_membership or not voter_membership:
            return redirect('question_detail', stack_id=stack_id, question_id=question_id)
        
        # Check for existing vote
        existing_vote = Vote.objects.filter(**vote_filter).first()
        
        if existing_vote:
            # Undo old vote reputation
            self._undo_reputation(
                existing_vote.vote_type, 
                owner_membership, 
                voter_membership,
                is_answer=bool(answer)
            )
            
            if existing_vote.vote_type == vote_type:
                # Toggle off - just delete
                existing_vote.delete()
            else:
                # Change vote
                existing_vote.vote_type = vote_type
                existing_vote.save()
                
                # Apply new vote reputation
                self._apply_reputation(
                    vote_type, 
                    owner_membership, 
                    voter_membership,
                    is_answer=bool(answer)
                )
        else:
            # Create new vote
            Vote.objects.create(
                user=request.user,
                vote_type=vote_type,
                **vote_create
            )
            
            # Apply reputation
            self._apply_reputation(
                vote_type, 
                owner_membership, 
                voter_membership,
                is_answer=bool(answer)
            )
        
        # Save memberships
        owner_membership.save()
        voter_membership.save()
        
        return redirect('question_detail', stack_id=stack_id, question_id=question_id)
    
    def _apply_reputation(self, vote_type, owner_membership, voter_membership, is_answer):
        """Apply reputation changes for a vote"""
        if vote_type == 'up':
            owner_membership.reputation += 10
        else:  # downvote
            owner_membership.reputation -= 2
            if is_answer:
                voter_membership.reputation -= 1  # Cost to downvote answer
    
    def _undo_reputation(self, vote_type, owner_membership, voter_membership, is_answer):
        """Undo reputation changes when removing/changing a vote"""
        if vote_type == 'up':
            owner_membership.reputation -= 10
        else:  # downvote
            owner_membership.reputation += 2
            if is_answer:
                voter_membership.reputation += 1  # Refund downvote cost
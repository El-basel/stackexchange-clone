from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils.text import slugify

class User(AbstractUser):
    email = models.EmailField(blank=False)

class Stack(models.Model):
    title = models.CharField(max_length=30)
    slug = models.SlugField(blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class StackMembership(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stack = models.ForeignKey(Stack, on_delete=models.CASCADE)
    reputation = models.IntegerField(default=0)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('user', 'stack')


class Tag(models.Model):
    name = models.CharField(max_length=30)
    stack = models.ForeignKey(Stack, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('name', 'stack')

    def __str__(self):
        return self.name


class Question(models.Model):
    title = models.CharField(max_length=30)
    description = models.TextField()
    votes = models.IntegerField(default=0)
    asked_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="question")
    stack = models.ForeignKey(Stack, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    edited_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name="edited_by")
    edited_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag)

    @property
    def vote_count(self):
        upvotes = self.vote_set.filter(vote_type='up').count()
        downvotes = self.vote_set.filter(vote_type='down').count()
        return upvotes - downvotes
    
    def __str__(self):
        return self.title

class Answer(models.Model):
    description = models.TextField()
    votes = models.IntegerField(default=0)
    is_accepted = models.BooleanField(default=False)
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    answered_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    @property
    def vote_count(self):
        upvotes = self.vote_set.filter(vote_type='up').count()
        downvotes = self.vote_set.filter(vote_type='down').count()
        return upvotes - downvotes

class Comment(models.Model):
    description = models.TextField(max_length=600)
    comment_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def clean(self):
        if not (bool(self.question) ^ bool(self.answer)):
            raise ValidationError("Comment must be on either question or answer")

class Vote(models.Model):
    VOTE_CHOICES = [('up', 'Upvote'), ('down', 'Downvote')]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    question = models.ForeignKey(Question, on_delete=models.CASCADE, null=True, blank=True)
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, null=True, blank=True)
    vote_type = models.CharField(max_length=4, choices=VOTE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'question'],
                condition=models.Q(question__isnull=False),
                name='unique_user_question_vote'
            ),
            models.UniqueConstraint(
                fields=['user', 'answer'],
                condition=models.Q(answer__isnull=False),
                name='unique_user_answer_vote'
            ),
        ]
    def clean(self):
        if not (bool(self.question) ^ bool(self.answer)):
            raise ValidationError("Vote must be on either question or answer")
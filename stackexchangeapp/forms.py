from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, Stack, Question, Tag, Answer

class UserCreationFormStackApp(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class StackCreationForm(forms.ModelForm):
    class Meta:
        model = Stack
        fields = ("title", "description")

class QuestionForm(forms.ModelForm):
    tag_names = forms.CharField(max_length=200, help_text="Enter tags separated by commas (e.g., tag1, tag2, tag3)")
    class Meta:
        model = Question
        fields = ("title", "description")

    def __init__(self, *args, **kwargs):
        self.stack = kwargs.pop('stack', None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        question = super().save(commit=False)

        if commit:
            question.save()

            tag_names = self.cleaned_data['tag_names'].split(',')
            for tag_name in tag_names:
                if tag_name:
                    tag, created = Tag.objects.get_or_create(
                        name=tag_name,
                        stack=self.stack
                    )
                    question.tags.add(tag)
        return question

class AnswerForm(forms.ModelForm):
    class Meta:
        model = Answer
        fields = ("description",)
        widgets = {
            'description': forms.Textarea(attrs={
                'rows':6, 
                'placeholder':'Write your answer here...',
                })
        }
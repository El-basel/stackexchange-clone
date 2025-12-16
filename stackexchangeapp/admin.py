
from django.contrib import admin
from .models import User, Stack, StackMembership, Question, Answer, Vote, Tag, Comment

# Register all models
admin.site.register(User)
admin.site.register(Stack)
admin.site.register(StackMembership)
admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(Vote)
admin.site.register(Tag)
admin.site.register(Comment)
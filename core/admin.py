from django.contrib import admin
from .models import Profile, Book, Post, Like, Repost, Comment, Follow, Notification

# Register your models here.
admin.site.register(Profile)
admin.site.register(Book)
admin.site.register(Post)
admin.site.register(Like)
admin.site.register(Repost)
admin.site.register(Comment)
admin.site.register(Follow)
admin.site.register(Notification)
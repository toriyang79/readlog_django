from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse # New import

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nickname = models.CharField(max_length=255)
    profile_image = models.ImageField(upload_to='profile_pics/', null=True, blank=True)

    def __str__(self):
        return self.nickname

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, null=True, blank=True)
    cover_url = models.CharField(max_length=255, null=True, blank=True)
    isbn = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'books'

    def __str__(self):
        return self.title

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.SET_NULL, null=True, blank=True)
    user_photo = models.ImageField(upload_to='post_photos/', null=True, blank=True) # Renamed from user_photo_url
    book_cover_url_snapshot = models.CharField(max_length=255, null=True, blank=True)
    text = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    like_count = models.IntegerField(default=0)
    repost_count = models.IntegerField(default=0)

    class Meta:
        db_table = 'posts'

    def __str__(self):
        return f'Post by {self.user.username} at {self.created_at}'

class Like(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'likes'
        unique_together = ('user', 'post')

class Repost(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reposts'
        unique_together = ('user', 'post')

class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'comments'

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post}'

class Follow(models.Model):
    follower = models.ForeignKey(User, related_name='following', on_delete=models.CASCADE)
    followee = models.ForeignKey(User, related_name='followers', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'follows'
        unique_together = ('follower', 'followee')

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    from_user = models.ForeignKey(User, related_name='sent_notifications', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, on_delete=models.CASCADE, null=True, blank=True)
    notification_type = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'notifications'

    def __str__(self):
        return f'Notification for {self.user.username}'

    def get_display_message(self):
        from_user_nickname = self.from_user.profile.nickname if self.from_user.profile else self.from_user.username
        if self.notification_type == 'like':
            return f'{from_user_nickname}님이 회원님의 게시물을 좋아합니다.'
        elif self.notification_type == 'repost':
            return f'{from_user_nickname}님이 회원님의 게시물을 리포스트했습니다.'
        elif self.notification_type == 'comment':
            return f'{from_user_nickname}님이 회원님의 게시물에 댓글을 남겼습니다.'
        elif self.notification_type == 'follow':
            return f'{from_user_nickname}님이 회원님을 팔로우하기 시작했습니다.'
        return f'새로운 알림: {self.notification_type}'

    def get_notification_url(self):
        if self.notification_type in ['like', 'repost', 'comment'] and self.post:
            return reverse('feed') + f'#post-' + str(self.post.id) # Anchor to the post on the feed page
        elif self.notification_type == 'follow':
            return reverse('profile_detail', args=[self.from_user.id])
        return '#' # Default to no specific link
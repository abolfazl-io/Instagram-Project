from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from django.conf import settings
from datetime import timedelta
import os

# MyUserManager, MyUser, Profile, Comment models remain unchanged...
class MyUserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        if not username:
            raise ValueError("Users must have a username")

        email = extra_fields.get('email')
        if email:
            extra_fields['email'] = self.normalize_email(email)

        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_admin', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(username, password, **extra_fields)

class MyUser(AbstractBaseUser):
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    objects = MyUserManager()

    def __str__(self):
        return self.username

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    @property
    def is_staff(self):
        return self.is_admin


class Profile(models.Model):
    user = models.OneToOneField(MyUser, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50, blank=True)
    last_name = models.CharField(max_length=50, blank=True)
    bio = models.TextField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to='profile_images/', blank=True, null=True)
    # فیلد جدید برای دنبال‌کنندگان
    followers = models.ManyToManyField(MyUser, related_name='following', blank=True)

    def __str__(self):
        return f"Profile of {self.user.username}"

    def count_followers(self):
        return self.followers.count()

    def count_following(self):
        # تعداد پروفایل‌هایی که این کاربر دنبال می‌کند
        return Profile.objects.filter(followers=self.user).count()

class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True, allow_unicode=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "دسته‌بندی"
        verbose_name_plural = "دسته‌بندی‌ها"

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts'
    )
    title = models.CharField(max_length=50)
    desc = models.TextField()
    # The 'image' field is now removed from here.
    create = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    categories = models.ManyToManyField(Category, related_name='posts', blank=True)
    publish = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='liked_posts',
        blank=True
    )
    dislikes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='disliked_posts',
        blank=True
    )

    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()

    class Meta:
        ordering = ['-publish']

    def __str__(self):
        return self.title


# NEW MODEL FOR POST MEDIA
class PostMedia(models.Model):
    post = models.ForeignKey(Post, related_name='media', on_delete=models.CASCADE)
    file = models.FileField(upload_to='post_media/')
    
    @property
    def is_video(self):
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        # os.path.splitext splits the path into a pair (root, ext).
        ext = os.path.splitext(self.file.name)[1]
        return ext.lower() in video_extensions

# Comment and Story models remain unchanged...
class Comment(models.Model):
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    body = models.TextField()

    # ریپلای
    parent_comment = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='replies'
    )

    # لایک و دیس‌لایک
    likes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='comment_likes',
        blank=True
    )
    dislikes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='comment_dislikes',
        blank=True
    )

    create = models.DateTimeField(auto_now_add=True)
    update = models.DateTimeField(auto_now=True)
    active = models.BooleanField(default=True)

    class Meta:
        ordering = ['create']

    def __str__(self):
        return f'Comment by {self.user.username} on {self.post.title}'

    def total_likes(self):
        return self.likes.count()

    def total_dislikes(self):
        return self.dislikes.count()



class Story(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='stories')
    image = models.ImageField(upload_to='stories/')
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='liked_stories', blank=True)
    viewers = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='viewed_stories', blank=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(hours=24)

    def total_likes(self):
        return self.likes.count()

    def total_views(self):
        return self.viewers.count()

    def __str__(self):
        return f"Story by {self.user.username} at {self.created_at}"


class StoryComment(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='story_comments')
    body = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # اینجا باید به صورت لیست باشد
        ordering = ['created_at']

    def __str__(self):
        return f'Comment by {self.user.username} on story {self.story.id}'

class Thread(models.Model):
    participants = models.ManyToManyField(MyUser, related_name='threads')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    name = models.CharField(max_length=100, null=True, blank=True)
    admin = models.ForeignKey(MyUser, on_delete=models.CASCADE, related_name='admin_threads', null=True, blank=True)


    def __str__(self):
        return f"Thread between {', '.join([user.username for user in self.participants.all()])}"

# shop1/models.py

# shop1/models.py


class Message(models.Model):
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(MyUser, on_delete=models.CASCADE)
    body = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='direct_messages/', blank=True, null=True)
    shared_post = models.ForeignKey(Post, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    parent_message = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='replies')
    seen_by = models.ManyToManyField(MyUser, related_name='seen_messages', blank=True)
    likes = models.ManyToManyField(MyUser, related_name='liked_messages', blank=True)
    is_view_once = models.BooleanField(default=False)
    viewed_by = models.ManyToManyField(MyUser, related_name='viewed_once_messages', blank=True)
    view_once_duration = models.IntegerField(null=True, blank=True)
    class Meta:
        ordering = ['created_at']

    @property
    def is_video(self):
        if not self.file:
            return False
        video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
        name, ext = os.path.splitext(self.file.name)
        return ext.lower() in video_extensions

    def __str__(self):
        return f"Message from {self.sender.username} in thread {self.thread.id}"
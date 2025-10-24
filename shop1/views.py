from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from .models import Post, Comment, Story , StoryComment
from django.db.models import Q
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models import Count
from google.cloud import vision
from django.conf import settings
import io
import requests
import base64
import json
import os

import threading
import requests
import base64
import json
import io
import os
from django.conf import settings
from google.cloud import vision
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.views.decorators.csrf import csrf_protect
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView
from django.db.models import Count, Q
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.http import JsonResponse
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# In shop1/views.py

def home(request):
    stories = Story.objects.filter(created_at__gte=timezone.now() - timedelta(hours=24)).order_by('-created_at')
    # Use prefetch_related to optimize database queries for media files
    posts = Post.objects.filter(status='published').prefetch_related('media').order_by('-publish')
    
    context = {
        'stories': stories,
        'posts': posts
    }
    return render(request, 'home.html', context)

    
def loginView(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('shop1:home')

        error = 'نام کاربری یا رمز عبور اشتباه است'
        return render(request, 'login.html', {'error': error})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('shop1:login')

@csrf_protect
def register_view(request):
    if request.method == 'POST':
        username = request.POST.get("username")
        password = request.POST.get("password")
        password2 = request.POST.get("password2")

        if password != password2:
            messages.error(request, "رمز عبور و تکرار آن یکی نیست")
            return render(request, 'register.html')

        if not username or not password:
            messages.error(request, "تمام فیلدها الزامی هستند")
            return render(request, 'register.html')

        if MyUser.objects.filter(username=username).exists():
            messages.error(request, "این نام کاربری قبلاً ثبت شده است")
            return render(request, 'register.html')

        user = MyUser.objects.create_user(username=username, password=password)
        login(request, user)

        next_url = request.GET.get('next')
        if next_url:
            return redirect(next_url)
        return redirect('shop1:home')

    return render(request, 'register.html')




@login_required
def edit_profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('shop1:profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'edit_profile.html', {'form': form})

def post_list(request):
    posts = Post.objects.filter(status='published').order_by('-publish')
    return render(request, 'blog/post_list.html', {'posts': posts})

def post_detail(request, pk):
    post = get_object_or_404(Post, pk=pk, status='published')
    comments = post.comments.filter(active=True)

    if request.method == 'POST':
        body = request.POST.get('body')
        Comment.objects.create(post=post, user=request.user, body=body)
        return redirect('shop1:post_detail', pk=pk)

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'comments': comments,
    })

@login_required
def add_comment(request, pk, parent_id=None):
    post = get_object_or_404(Post, pk=pk, status='published')
    parent_comment = None

    if parent_id:
        parent_comment = get_object_or_404(Comment, id=parent_id, post=post)

    if request.method == 'POST':
        body = request.POST.get('body')
        if not body.strip():
            return redirect('shop1:post_detail', pk=pk)

        Comment.objects.create(
            post=post,
            user=request.user,
            body=body,
            parent_comment=parent_comment
        )

    return redirect('shop1:post_detail', pk=pk)



@login_required
def like_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    user_liked = False

    if request.user in post.likes.all():
        # اگر کاربر قبلاً لایک کرده، لایک را بردار
        post.likes.remove(request.user)
        user_liked = False
    else:
        # در غیر این صورت، لایک کن
        post.likes.add(request.user)
        user_liked = True
        # اگر کاربر قبلاً دیسلایک کرده، آن را حذف کن
        if request.user in post.dislikes.all():
            post.dislikes.remove(request.user)

    # اگر درخواست از نوع AJAX بود، پاسخ JSON برگردان
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'total_likes': post.total_likes(), 'user_liked': user_liked})

    # اگر درخواست عادی بود (برای مواقعی که جاوااسکریپت غیرفعال است)، ریدایرکت کن
    return redirect('shop1:post_detail', pk=pk)

@login_required
def dislike_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if request.user in post.dislikes.all():
        post.dislikes.remove(request.user)
    else:
        post.dislikes.add(request.user)
        post.likes.remove(request.user)
    return redirect('shop1:post_detail', pk=pk)

@login_required
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
    else:
        comment.likes.add(request.user)
        comment.dislikes.remove(request.user)
    return redirect('shop1:post_detail', pk=comment.post.pk)

@login_required
def dislike_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if request.user in comment.dislikes.all():
        comment.dislikes.remove(request.user)
    else:
        comment.dislikes.add(request.user)
        comment.likes.remove(request.user)
    return redirect('shop1:post_detail', pk=comment.post.pk)

def search_users(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = MyUser.objects.filter(username__icontains=query)
    return render(request, 'search_results.html', {
        'query': query,
        'results': results
    })

# shop1/views.py

@login_required
def profile_view(request):
    profile = get_object_or_404(Profile, user=request.user)
    user_posts = Post.objects.filter(user=request.user, status='published').order_by('-publish')
    posts_count = user_posts.count()
    
    context = {
        'profile': profile,
        'user_posts': user_posts,
        'posts_count': posts_count,
        'followers_count': profile.count_followers(),
        'following_count': profile.count_following(),
    }
    return render(request, 'profile.html', context)


def public_profile(request, username):
    user_obj = get_object_or_404(MyUser, username=username)
    profile = get_object_or_404(Profile, user=user_obj)
    posts = Post.objects.filter(user=user_obj, status='published').order_by('-publish')
    
    # بررسی اینکه آیا کاربر لاگین کرده، این پروفایل را فالو می‌کند یا نه
    is_following = False
    if request.user.is_authenticated:
        is_following = request.user in profile.followers.all()

    context = {
        'profile': profile,
        'posts': posts,
        'is_following': is_following,
        'followers_count': profile.count_followers(),
        'following_count': profile.count_following(),
        'posts_count': posts.count(),
    }
    return render(request, 'public_profile.html', context)

@login_required
def delete_account(request):
    if request.method == 'POST':
        user = request.user
        logout(request)
        user.delete()
        messages.success(request, "اکانت شما با موفقیت حذف شد.")
        return redirect('shop1:home')
    return render(request, 'delete_account.html')


@login_required
def create_story(request):
    if request.method == 'POST':
        image = request.FILES.get('image')
        if image:
            Story.objects.create(user=request.user, image=image)
            return redirect('shop1:home')
    return render(request, 'create_story.html')



@login_required
def view_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)

    if story.is_expired():
        return redirect('shop1:home')

    if request.user != story.user:
        story.viewers.add(request.user)

    comments = story.comments.all()
    
    context = {
        'story': story,
        'comments': comments,
    }
    return render(request, 'view_story.html', context)

@login_required
def like_story(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if request.user in story.likes.all():
        story.likes.remove(request.user)
    else:
        story.likes.add(request.user)
    return redirect('shop1:view_story', story_id=story.id)

@login_required
def add_story_comment(request, story_id):
    story = get_object_or_404(Story, id=story_id)
    if request.method == 'POST':
        body = request.POST.get('body')
        if body:
            StoryComment.objects.create(story=story, user=request.user, body=body)
    return redirect('shop1:view_story', story_id=story.id)


@login_required
def follow_unfollow(request, username):
    if request.method == 'POST':
        target_user = get_object_or_404(MyUser, username=username)
        profile = target_user.profile
        
        if request.user in profile.followers.all():
            # اگر از قبل فالو کرده، آنفالو کن
            profile.followers.remove(request.user)
            is_following = False
        else:
            # در غیر این صورت، فالو کن
            profile.followers.add(request.user)
            is_following = True
            
        return JsonResponse({'is_following': is_following, 'followers_count': profile.count_followers()})
    return redirect('shop1:public_profile', username=username)


def followers_list(request, username):
    user = get_object_or_404(MyUser, username=username)
    profile = user.profile
    # .followers.all() لیستی از کاربرانی که این پروفایل را دنبال می‌کنند برمی‌گرداند
    followers = profile.followers.all()
    
    context = {
        'profile_user': user,
        'user_list': followers,
        'title': 'دنبال‌کنندگان'
    }
    return render(request, 'user_list.html', context)

def following_list(request, username):
    user = get_object_or_404(MyUser, username=username)
    # user.following.all() با استفاده از related_name که در مدل تعریف کردیم،
    # لیستی از پروفایل‌هایی که این کاربر دنبال می‌کند را برمی‌گرداند
    following_profiles = user.following.all()
    # ما به لیست خود کاربران نیاز داریم، نه پروفایل‌ها
    following_users = [profile.user for profile in following_profiles]

    context = {
        'profile_user': user,
        'user_list': following_users,
        'title': 'دنبال‌شوندگان'
    }
    return render(request, 'user_list.html', context)

# shop1/views.py
from django.db.models import Count

# ... (کدهای ویوهای قبلی) ...

@login_required
def inbox(request):
    threads = Thread.objects.filter(participants=request.user).order_by('-updated_at')
    context = {
        'threads': threads
    }
    return render(request, 'inbox.html', context)

# shop1/views.py

# shop1/views.py

# shop1/views.py

@login_required
def thread_view(request, thread_id):
    thread = get_object_or_404(Thread, id=thread_id, participants=request.user)
    
    messages_to_mark = thread.messages.exclude(sender=request.user)
    for message in messages_to_mark:
        message.seen_by.add(request.user)
        
    is_group = thread.participants.count() > 2
    
    # کد جدید برای مدیریت نام گروه یا کاربر مقابل
    other_user = None
    if not is_group:
        other_user = thread.participants.exclude(id=request.user.id).first()

    if request.method == 'POST':
        body = request.POST.get('body')
        parent_message_id = request.POST.get('parent_message_id')
        parent_message = None

        if parent_message_id:
            try:
                parent_message = Message.objects.get(id=parent_message_id)
            except Message.DoesNotExist:
                parent_message = None

        if body:
            message = Message.objects.create(
                thread=thread, 
                sender=request.user, 
                body=body,
                parent_message=parent_message
            )
            thread.save() 
            
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                response_data = {
                    'sender': message.sender.username,
                    'body': message.body,
                    'created_at': message.created_at.strftime('%H:%M'),
                    'is_reply': bool(message.parent_message),
                }
                if message.parent_message:
                    response_data['parent_body'] = message.parent_message.body
                    response_data['parent_sender'] = message.parent_message.sender.username
                return JsonResponse(response_data)

        return redirect('shop1:thread_view', thread_id=thread_id)
            
    messages = thread.messages.all()

    context = {
        'thread': thread,
        'messages': messages,
        'other_user': other_user,
        'is_group': is_group,
    }
    return render(request, 'thread.html', context)

@login_required
def create_thread(request, username):
    receiver = get_object_or_404(MyUser, username=username)
    
    # بررسی اینکه آیا از قبل چتی بین این دو کاربر وجود دارد یا نه
    threads = Thread.objects.filter(participants=request.user).filter(participants=receiver)
    # مطمئن می‌شویم که چت دقیقا بین همین دو نفر است
    exact_thread = threads.annotate(p_count=Count('participants')).filter(p_count=2).first()

    if exact_thread:
        # اگر چت وجود داشت، به همان صفحه چت برو
        return redirect('shop1:thread_view', thread_id=exact_thread.id)
    else:
        # در غیر این صورت، یک چت جدید بساز
        new_thread = Thread.objects.create()
        new_thread.participants.add(request.user, receiver)
        return redirect('shop1:thread_view', thread_id=new_thread.id)


@login_required
def mark_messages_as_seen(request, thread_id):
    if request.method == 'POST':
        thread = get_object_or_404(Thread, id=thread_id, participants=request.user)
        # تمام پیام‌هایی که فرستنده آنها کاربر فعلی نیست را پیدا کن
        messages_to_mark = thread.messages.exclude(sender=request.user)
        for message in messages_to_mark:
            # کاربر فعلی را به لیست seen_by اضافه کن
            message.seen_by.add(request.user)
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

# shop1/views.py

@login_required
def share_post(request, post_pk):
    post = get_object_or_404(Post, pk=post_pk)
    threads = Thread.objects.filter(participants=request.user)

    if request.method == 'POST':
        thread_ids = request.POST.getlist('threads')
        channel_layer = get_channel_layer()

        for thread_id in thread_ids:
            try:
                thread = Thread.objects.get(id=thread_id)
                message = Message.objects.create(
                    thread=thread,
                    sender=request.user,
                    shared_post=post
                )
                message.seen_by.add(request.user)

                first_media = post.media.first()
                media_url = first_media.file.url if first_media else ''

                message_data = {
                    'type': 'new_message',
                    'message': {
                        'id': message.id,
                        'sender': message.sender.username,
                        'body': message.body,
                        'is_reply': False,
                        'parent': None,
                        'likes_count': 0,
                        'shared_post': {
                            'pk': post.pk,
                            'media_url': media_url,
                            'user': post.user.username,
                        }
                    }
                }
                
                async_to_sync(channel_layer.group_send)(
                    f'chat_{thread_id}',
                    {'type': 'chat_message', 'message': message_data['message']}
                )
            except Thread.DoesNotExist:
                continue
        
        messages.success(request, "پست با موفقیت به اشتراک گذاشته شد.")
        return redirect('shop1:home')

    context = { 'post': post, 'threads': threads }
    return render(request, 'share_post.html', context)

# shop1/views.py

# تابع کمکی برای تشخیص ویدیو
def is_video(file_path):
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv', '.webm']
    ext = os.path.splitext(file_path)[1]
    return ext.lower() in video_extensions

@login_required
def upload_direct_file(request, thread_id):
    if request.method == 'POST':
        thread = get_object_or_404(Thread, id=thread_id, participants=request.user)
        file = request.FILES.get('file')
        body = request.POST.get('body', '')
        is_view_once = request.POST.get('is_view_once') == 'true'
        duration = request.POST.get('duration') # دریافت زمان تایمر
        if thread.participants.count() > 2:
            is_view_once = False
        if not file and not body.strip():
            return JsonResponse({'status': 'error', 'message': 'Cannot send an empty message.'}, status=400)

        message = Message.objects.create(
            thread=thread, 
            sender=request.user, 
            body=body, 
            file=file, 
            is_view_once=is_view_once
        )
        message.seen_by.add(request.user)
        thread.save()

        channel_layer = get_channel_layer()
        file_url = message.file.url if message.file else None
        file_is_video = is_video(message.file.name) if message.file else False

        message_data = {
            'id': message.id,
            'sender': message.sender.username,
            'body': message.body,
            'file_url': file_url,
            'is_video': file_is_video,
            'is_view_once': message.is_view_once,
            'view_once_duration': message.view_once_duration, # ارسال زمان تایمر
            'viewed_by_user': request.user.username in [user.username for user in message.viewed_by.all()],
            'is_reply': False, 
            'parent': None, 
            'likes_count': 0,
            'shared_post': None
        }

        async_to_sync(channel_layer.group_send)(
            f'chat_{thread_id}',
            {'type': 'chat_message', 'message': message_data}
        )
        return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)


@login_required
def mark_media_as_viewed(request, message_id):
    if request.method == 'POST':
        message = get_object_or_404(Message, id=message_id)
        if request.user in message.thread.participants.all() and message.is_view_once:
            message.viewed_by.add(request.user)
            return JsonResponse({'status': 'ok'})
    return JsonResponse({'status': 'error'}, status=400)

# shop1/views.py

# shop1/views.py

@login_required
def create_group(request):
    followers = request.user.profile.followers.all()

    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        selected_user_ids = request.POST.getlist('users')

        if not selected_user_ids:
            messages.error(request, "حداقل یک عضو برای شروع چت الزامی است.")
            return redirect('shop1:create_group')

        # --- START: منطق جدید و هوشمند ---
        if len(selected_user_ids) == 1:
            # اگر فقط یک نفر انتخاب شده، به چت دونفره بروید
            receiver = get_object_or_404(MyUser, id=selected_user_ids[0])
            
            # بررسی اینکه آیا از قبل چتی بین این دو کاربر وجود دارد
            threads = Thread.objects.filter(participants=request.user).filter(participants=receiver)
            exact_thread = threads.annotate(p_count=Count('participants')).filter(p_count=2).first()

            if exact_thread:
                return redirect('shop1:thread_view', thread_id=exact_thread.id)
            else:
                # اگر چت دونفره وجود نداشت، یکی بساز
                new_thread = Thread.objects.create()
                new_thread.participants.add(request.user, receiver)
                return redirect('shop1:thread_view', thread_id=new_thread.id)
        
        else:
            # اگر دو نفر یا بیشتر انتخاب شدند، گروه بساز
            if not group_name:
                messages.error(request, "برای گروه، انتخاب نام الزامی است.")
                return redirect('shop1:create_group')

            new_thread = Thread.objects.create(name=group_name, admin=request.user)
            new_thread.participants.add(request.user)
            for user_id in selected_user_ids:
                new_thread.participants.add(MyUser.objects.get(id=user_id))
            
            return redirect('shop1:thread_view', thread_id=new_thread.id)
        # --- END: منطق جدید و هوشمند ---

    context = {
        'followers': followers
    }
    return render(request, 'create_group.html', context)

# shop1/views.py

@login_required
def edit_group(request, thread_id):
    # اطمینان از اینکه کاربر ادمین گروه است
    thread = get_object_or_404(Thread, id=thread_id, admin=request.user)
    
    if request.method == 'POST':
        group_name = request.POST.get('group_name')
        selected_user_ids = request.POST.getlist('users')

        if not group_name:
            messages.error(request, "نام گروه الزامی است.")
            return redirect('shop1:edit_group', thread_id=thread.id)

        # آپدیت نام گروه
        thread.name = group_name
        
        # آپدیت لیست اعضا (set لیست قبلی را پاک و لیست جدید را جایگزین می‌کند)
        # ما خود ادمین را هم به لیست اضافه می‌کنیم
        selected_users = [MyUser.objects.get(id=uid) for uid in selected_user_ids]
        thread.participants.set([request.user] + selected_users)
        
        thread.save()
        messages.success(request, "گروه با موفقیت ویرایش شد.")
        return redirect('shop1:thread_view', thread_id=thread.id)

    # لیست تمام کاربرانی که می‌توان به گروه اضافه کرد (فالوورها)
    potential_members = request.user.profile.followers.all()
    # لیست ID اعضای فعلی گروه برای اینکه چک‌باکس‌هایشان تیک خورده باشد
    current_member_ids = [user.id for user in thread.participants.all()]

    context = {
        'thread': thread,
        'potential_members': potential_members,
        'current_member_ids': current_member_ids
    }
    return render(request, 'edit_group.html', context)

def explore_view(request):
    """
    پست‌های عمومی را بر اساس محبوبیت (تعداد لایک) برای صفحه اکسپلور نمایش می‌دهد.
    """
    # تعداد پست‌ها را افزایش می‌دهیم تا طرح‌بندی بهتر دیده شود
    posts = Post.objects.filter(status='published').annotate(
        like_count=Count('likes')
    ).order_by('-like_count', '-publish')[:30] # <-- واکشی ۳۰ پست برتر

    return render(request, 'explore.html', {'posts': posts})



def get_image_categories(image_file):
    """
    تصویر را به Google Vision API ارسال کرده و لیستی از برچسب‌ها را برمی‌گرداند.
    """
    try:
        # ساخت کلاینت برای ارتباط با API
        client = vision.ImageAnnotatorClient()
        
        # خواندن محتوای فایل تصویر
        content = image_file.read()
        image = vision.Image(content=content)

        # ارسال درخواست برای تشخیص برچسب (Label Detection)
        response = client.label_detection(image=image)
        labels = response.label_annotations

        # استخراج نام برچسب‌ها با دقت بالای ۸۵٪
        category_names = [label.description for label in labels if label.score > 0.85]
        
        # بازگرداندن فایل به ابتدای آن برای ذخیره‌سازی در دیتابیس
        image_file.seek(0)
        
        return category_names

    except Exception as e:
        print(f"Error calling Google Vision API: {e}")
        image_file.seek(0)
        return []




# --- تابع تحلیل تصویر (بدون تغییر) ---
def get_image_categories_rest(image_content):
    try:
        api_key = settings.GOOGLE_VISION_API_KEY
        url = f"https://vision.googleapis.com/v1/images:annotate?key={api_key}"
        encoded_image = base64.b64encode(image_content).decode('utf-8')

        payload = {
            "requests": [{
                "image": {"content": encoded_image},
                "features": [{"type": "LABEL_DETECTION", "maxResults": 10}]
            }]
        }
        response = requests.post(url, json=payload)
        response.raise_for_status()
        result = response.json()

        if 'error' in result['responses'][0]:
            raise Exception(f"Google Vision API Error: {result['responses'][0]['error']['message']}")

        labels = result['responses'][0].get('labelAnnotations', [])
        return [label['description'] for label in labels if label.get('score', 0) > 0.85]
    except Exception as e:
        print(f"!!! ERROR in background task: {e}")
        return []

# --- تابع جدید برای اجرا در پس‌زمینه ---
def process_post_categories(post_id, image_contents):
    """
    این تابع در یک ترد جداگانه اجرا می‌شود تا تحلیل تصاویر را انجام دهد.
    """
    try:
        post = Post.objects.get(id=post_id)
        all_category_names = set()

        for content in image_contents:
            category_names = get_image_categories_rest(content)
            for name in category_names:
                all_category_names.add(name.lower())

        category_ids = []
        for cat_name in all_category_names:
            category, created = Category.objects.get_or_create(
                name=cat_name,
                defaults={'slug': cat_name.replace(' ', '-')}
            )
            category_ids.append(category.id)
        
        if category_ids:
            post.categories.set(category_ids)
            print(f"--- Categories successfully added to Post ID: {post_id} ---")

    except Post.DoesNotExist:
        print(f"!!! ERROR: Post with ID {post_id} not found in background task.")


# --- تابع create_post اصلاح‌شده ---
@login_required
def create_post(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        desc = request.POST.get('desc')
        status = request.POST.get('status')
        files = request.FILES.getlist('files')

        if not files:
            messages.error(request, "شما باید حداقل یک عکس یا ویدیو آپلود کنید.")
            return render(request, 'blog/create_post.html')

        # پست بلافاصله ایجاد می‌شود
        post = Post.objects.create(
            user=request.user,
            title=title,
            desc=desc,
            status=status
        )

        image_contents_for_processing = []
        for f in files:
            # ابتدا فایل‌ها را به پست متصل می‌کنیم
            PostMedia.objects.create(post=post, file=f)
            # محتوای فایل‌های عکس را برای ارسال به ترد پس‌زمینه آماده می‌کنیم
            if not f.content_type.startswith('video'):
                image_contents_for_processing.append(f.read())

        # اگر عکسی برای تحلیل وجود داشت، ترد را اجرا می‌کنیم
        if image_contents_for_processing:
            # اجرای تحلیل در یک ترد جداگانه
            thread = threading.Thread(
                target=process_post_categories,
                args=(post.id, image_contents_for_processing)
            )
            thread.start()

        # کاربر بلافاصله به صفحه پست هدایت می‌شود
        return redirect('shop1:post_detail', pk=post.pk)

    return render(request, 'blog/create_post.html')
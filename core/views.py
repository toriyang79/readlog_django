from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import JsonResponse
import json # New import
from . import services
from .models import Like, Repost, Comment, Follow, Notification # New import
from django.contrib.auth.models import User # New import

def feed(request):
    posts = services.list_posts()
    if request.user.is_authenticated:
        liked_posts_ids = Like.objects.filter(user=request.user, post__in=posts).values_list('post_id', flat=True)
        reposted_posts_ids = Repost.objects.filter(user=request.user, post__in=posts).values_list('post_id', flat=True)
        for post in posts:
            post.is_liked = post.id in liked_posts_ids
            post.is_reposted = post.id in reposted_posts_ids
    return render(request, 'feed.html', {'posts': posts})

def create_post_view(request):
    search_results = []
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return redirect(reverse('feed'))

        if 'search_book' in request.POST: # Handle book search
            query = request.POST.get('query')
            if query:
                search_results = services.search_books(query)
            return render(request, 'create_post.html', {'search_results': search_results})

        # Handle post creation
        text = request.POST.get('text')
        book_title = request.POST.get('book_title')
        book_author = request.POST.get('book_author')
        book_cover_url = request.POST.get('book_cover_url')
        user_photo = request.FILES.get('user_photo')

        book = None
        if book_title and book_author:
            book = services.save_book_if_needed(book_title, book_author, book_cover_url)

        services.create_post(
            user_id=request.user.id,
            book_id=book.id if book else None,
            user_photo=user_photo,
            book_cover_url_snapshot=book_cover_url,
            text=text
        )
        return redirect(reverse('feed'))
    elif request.method == 'GET':
        query = request.GET.get('query')
        if query:
            search_results = services.search_books(query)
    return render(request, 'create_post.html', {'search_results': search_results})

def profile(request, user_id=None):
    if user_id:
        viewed_user = get_object_or_404(User, id=user_id)
    else:
        if not request.user.is_authenticated:
            return redirect(reverse('feed'))
        viewed_user = request.user

    user_profile = viewed_user.profile
    my_posts = services.my_posts(viewed_user.id)
    my_reposts = services.my_reposts(viewed_user.id)

    is_following = False
    if request.user.is_authenticated and request.user != viewed_user:
        is_following = services.is_following(request.user.id, viewed_user.id)

    follower_count = services.get_follower_count(viewed_user.id)
    following_count = services.get_following_count(viewed_user.id)

    context = {
        'viewed_user': viewed_user,
        'user_profile': user_profile,
        'my_posts': my_posts,
        'my_reposts': my_reposts,
        'is_following': is_following,
        'follower_count': follower_count,
        'following_count': following_count,
    }
    return render(request, 'profile.html', context)

def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        nickname = request.POST.get('nickname')

        # Basic validation
        if not email or not password or not nickname:
            return render(request, 'signup.html', {'error': 'All fields are required.'})

        try:
            services.create_user(email, password, nickname)
            return redirect(reverse('login')) # Redirect to login page after successful signup
        except Exception as e:
            return render(request, 'signup.html', {'error': str(e)})
    return render(request, 'signup.html')

def edit_post_view(request, post_id):
    if not request.user.is_authenticated:
        return redirect(reverse('feed'))

    post = services.get_post(post_id)
    if not post or post.user.id != request.user.id:
        return redirect(reverse('feed')) # Or a 404/permission denied page

    if request.method == 'POST':
        new_text = request.POST.get('text')
        new_user_photo = request.FILES.get('user_photo')

        services.update_post(
            user_id=request.user.id,
            post_id=post_id,
            new_text=new_text,
            new_user_photo=new_user_photo
        )
        return redirect(reverse('profile'))
    
    context = {'post': post}
    return render(request, 'edit_post.html', context)

def delete_post_view(request, post_id):
    if not request.user.is_authenticated:
        return redirect(reverse('feed'))

    post = services.get_post(post_id)
    if not post or post.user.id != request.user.id:
        return redirect(reverse('feed')) # Or a 404/permission denied page

    if request.method == 'POST':
        services.delete_post(request.user.id, post_id)
        return redirect(reverse('profile'))
    
    # For GET request to delete, render a confirmation page
    context = {'post': post}
    return render(request, 'delete_post_confirm.html', context)

def like_post(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    if request.method == 'POST':
        liked, new_like_count = services.toggle_like(request.user.id, post_id)
        return JsonResponse({'status': 'success', 'liked': liked, 'new_like_count': new_like_count})
    
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)

def toggle_repost(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    if request.method == 'POST':
        reposted, new_repost_count = services.toggle_repost(request.user.id, post_id)
        return JsonResponse({'status': 'success', 'reposted': reposted, 'new_repost_count': new_repost_count})
    
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)

def add_comment(request, post_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            comment_text = data.get('comment_text')
            if not comment_text:
                return JsonResponse({'status': 'error', 'message': '댓글 내용을 입력해주세요.'}, status=400)
            
            comment = services.add_comment(request.user.id, post_id, comment_text)
            return JsonResponse({
                'status': 'success',
                'comment': {
                    'id': comment.id,
                    'text': comment.text,
                    'author': comment.user.profile.nickname,
                    'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M"),
                }
            })
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': '잘못된 JSON 형식입니다.'}, status=400)
    
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)

def list_comments_api(request, post_id):
    comments = services.list_comments(post_id)
    comments_data = []
    for comment in comments:
        comments_data.append({
            'id': comment.id,
            'text': comment.text,
            'author': comment.user.profile.nickname,
            'created_at': comment.created_at.strftime("%Y-%m-%d %H:%M"),
        })
    return JsonResponse({'status': 'success', 'comments': comments_data})

def toggle_follow(request, user_id):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    if request.method == 'POST':
        # user_id is the ID of the user being followed/unfollowed
        followed_user = get_object_or_404(User, id=user_id)

        if request.user == followed_user:
            return JsonResponse({'status': 'error', 'message': '자기 자신을 팔로우할 수 없습니다.'}, status=400)

        followed, follower_count = services.toggle_follow(request.user.id, followed_user.id)
        return JsonResponse({'status': 'success', 'followed': followed, 'follower_count': follower_count})
    
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)

def list_notifications_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    notifications = services.list_notifications(request.user.id)
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            'id': notif.id,
            'type': notif.notification_type,
            'from_user': notif.from_user.profile.nickname,
            'post_id': notif.post.id if notif.post else None,
            'is_read': notif.is_read,
            'created_at': notif.created_at.strftime("%Y-%m-%d %H:%M"),
            'message': notif.get_display_message(),
            'url': notif.get_notification_url()
        })
    return JsonResponse({'status': 'success', 'notifications': notifications_data})

def mark_notifications_read_api(request):
    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'message': '로그인이 필요합니다.'}, status=401)

    if request.method == 'POST':
        services.mark_all_notifications_read(request.user.id)
        return JsonResponse({'status': 'success', 'message': '모든 알림을 읽음으로 표시했습니다.'})
    
    return JsonResponse({'status': 'error', 'message': '잘못된 요청입니다.'}, status=400)
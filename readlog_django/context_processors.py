from core import services

def unread_notifications(request):
    if request.user.is_authenticated:
        count = services.unread_notifications_count(request.user.id)
        return {'unread_notifications_count': count}
    return {'unread_notifications_count': 0}
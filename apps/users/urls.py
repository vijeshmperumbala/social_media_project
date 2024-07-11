from django.urls import path
from apps.users.views import (
    AuthenticationView, 
    FriendRequestView, 
    UserView,
)
from rest_framework.routers import DefaultRouter


router = DefaultRouter()
router.register(r'', AuthenticationView)


urlpatterns = [
    path('signup/', AuthenticationView.as_view({'post': 'signup'}), name='user-signup'),
    path('login/', AuthenticationView.as_view({'get': 'login'}), name='user-login'),
    path('user-name-update/', UserView.as_view({'post': 'name_update'}), name='user-name-update'),
    path('user-search/', UserView.as_view({'post': 'user_search'}), name='user-search'),
    path('send-friends-requests/', FriendRequestView.as_view({'post': 'send_friend_request'})),
    path('accept-friend-request/', FriendRequestView.as_view({'post': 'accept_friend_request'}),
         name='accept-friend-request'),
    path('reject-friend-request/', FriendRequestView.as_view({'post': 'reject_friend_request'}),
         name='reject-friend-request'),
    path('list-pending-requests/', FriendRequestView.as_view({'get': 'list_pending_friends_request'}), name='list-pending-requests'),
    path('list-friends/', FriendRequestView.as_view({'get': 'list_friends'}), name='list-friends'),
]

urlpatterns += router.urls

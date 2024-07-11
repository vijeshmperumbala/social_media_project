from django.shortcuts import get_object_or_404
from django.http import Http404
from django.contrib.auth import get_user_model

from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import AuthenticationFailed
from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.contrib.auth.hashers import make_password
from rest_framework import status

from apps.users.models import FriendRequest, User
from apps.users.serializer import (
    LoginSerializer,
    UserDisplaySerializer,
    UserSearchSerializer,
    UserSignupSerializer,
    FriendRequestSerializer,
    UserNameUpdateSerializer,
)


User = get_user_model()


class AuthenticationView(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSignupSerializer

    @action(detail=False, methods=["post"], url_path="signup")
    def signup(self, request, *args, **kwargs):
        """
            The `signup` function registers a user if they are not already registered and returns appropriate responses
            based on the registration status.

            :param request: The HTTP request object containing user registration data.
            :return: A Response object indicating the outcome of the user registration process:
                    - Custom data is returned if the user is successfully registered.
                    - Error messages are returned if there are issues during registration.
        """
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user_obj, created = User.objects.get_or_create(
                email=serializer.validated_data["email"],
                defaults={
                    "password": make_password(serializer.validated_data["password"])
                },
            )
            if created:
                custom_data = {
                    "message": "User Registered Successfully",
                    "data": serializer.data,
                }
                return Response(custom_data, status=status.HTTP_201_CREATED)
            else:
                custom_data = {
                    "message": "User already registered. Try logging in.",
                }
                return Response(custom_data, status=status.HTTP_200_OK)
        else:
            custom_data = {
                "message": serializer.errors,
            }
            return Response(custom_data, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], url_path="login")
    def login(self, request, *args, **kwargs):
        """
            The `login` function validates user login data using a serializer and returns a response based on the validation result.

            :param request: The HTTP request object containing login data.
            :return: A Response object indicating the outcome of the login attempt:
                    - If successful, custom data is returned indicating successful login.
                    - If authentication fails (AuthenticationFailed exception), it returns a custom message with HTTP status code 401.
                    - If the serializer validation fails, it returns the serializer errors with HTTP status code 400.
        """
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            try:
                data = serializer.validated_data
                custom_data = {"message": "User logged in successfully", "data": data}
                return Response(custom_data, status=status.HTTP_200_OK)
            except AuthenticationFailed as e:
                custom_data = {"message": str(e.detail)}
                return Response(custom_data, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserView(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = UserNameUpdateSerializer
    pagination_class = PageNumberPagination

    @action(detail=False, methods=["post"], url_path="name_update")
    def name_update(self, request, *args, **kwargs):
        """
            The `name_update` function updates a user's name in the database based on the provided user ID or the authenticated user's ID.

            :param request: The HTTP request object containing user authentication and request data.
            :return: A response indicating the outcome of the name update operation.
                    If successful, it returns "User Name Updated Successfully" with HTTP status code 200.
                    If the user is not found, it returns "User Not Found" with HTTP status code 404.
        """

        user_id = request.data.get("user_id")
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            if user_id:
                try:
                    user_obj = User.objects.get(pk=user_id)
                except Http404:
                    return Response(
                        {"error": "User Not Found."}, status=status.HTTP_404_NOT_FOUND
                    )
            else:
                try:
                    user_obj = User.objects.get(pk=request.user.id)
                except Http404:
                    return Response(
                        {"error": "User Not Found."}, status=status.HTTP_404_NOT_FOUND
                    )

            if user_obj:
                user_obj.name = serializer.validated_data["name"]
                user_obj.save()

                custom_data = {
                    "message": "User Name Updated Successfully.",
                }
                return Response(custom_data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], url_path="user_search")
    def user_search(self, request, *args, **kwargs):
        """
            The function `user_search` filters users based on email or name input, paginates the results, and returns a response.

            :param request: The HTTP request object containing query parameters for user search.
            :return: A paginated response with user data based on the provided search parameters (email or name).
                    If no email or name is provided, an error message indicates the required parameters.
                    Errors from invalid input are returned with HTTP status 400.
        """
        serializer = UserSearchSerializer(data=request.query_params)
        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            name = serializer.validated_data.get("name")
            queryset = User.objects.all()

            if email:
                queryset = queryset.filter(email__iexact=email)
            elif name:
                queryset = queryset.filter(name__icontains=name)
            else:
                custom_data = {
                    "error": "Please provide either 'email' or 'name' as search parameter."
                }
                return Response(custom_data, status=status.HTTP_400_BAD_REQUEST)

            paginator = self.pagination_class()
            paginated_queryset = paginator.paginate_queryset(queryset, request)
            serializer = UserDisplaySerializer(paginated_queryset, many=True)
            return paginator.get_paginated_response(serializer.data)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FriendRequestView(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='send_friend_request')
    def send_friend_request(self, request, *args, **kwargs):
        """
            This function handles sending a friend request between two users, checking various conditions before creating the request.

            :param request: The HTTP request object containing user information and request data.
            :return: A Response object indicating the outcome of the friend request. Different responses are returned based on the conditions checked.
        """
        requested_user_id = request.user.id
        request_received_user_id = request.data.get("request_received_user_id")

        if not request_received_user_id:
            return Response(
                {"error": "Received user ID is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        requested_user = get_object_or_404(User, pk=requested_user_id)

        try:
            request_received_user = get_object_or_404(User, pk=request_received_user_id)
        except Http404:
            return Response(
                {"error": "Friend not found."}, status=status.HTTP_404_NOT_FOUND
            )

        if requested_user == request_received_user:
            return Response(
                {"error": "You cannot send Friend Request to Same User."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not FriendRequest.can_send_friend_request(requested_user):
            return Response(
                {
                    "error": "You cannot send more than 3 friend requests within a minute."
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        if FriendRequest.check_already_request_send(
            requested_user, request_received_user
        ):
            return Response(
                {"message": "Already have pending request."}, status=status.HTTP_200_OK
            )

        if FriendRequest.check_already_friend(requested_user, request_received_user):
            return Response(
                {"message": "Already your friend."}, status=status.HTTP_200_OK
            )

        FriendRequest.objects.create(
            requested_user=requested_user, request_received_user=request_received_user
        )
        return Response(
            {"message": "Friend request sent successfully."},
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=['post'], url_path='accept_friend_request')
    def accept_friend_request(self, request, *args, **kwargs):
        """
            This function accepts a friend request and updating its status to "accepted".

            :param request: The HTTP request object containing user information and request data.
            :return: A Response object with a message indicating if the friend request was accepted successfully or if there was an error.
                    The response includes a status code to indicate the outcome.
        """
        request_id = request.data.get('request_id')

        if not request_id:
            return Response({"error": "Request ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            friend_request = get_object_or_404(FriendRequest, pk=request_id, status=1)
        except Http404:
            return Response({"error": "This friend request is no longer pending."},
                            status=status.HTTP_400_BAD_REQUEST)

        if friend_request.requested_user != request.user:
            return Response({"error": "You do not have permission to accept this friend request."},
                            status=status.HTTP_403_FORBIDDEN)

        friend_request.status = 2
        friend_request.save()

        return Response({"message": "Friend request accepted successfully."},
                        status=status.HTTP_200_OK)

    @action(detail=False, methods=['post'], url_path='reject_friend_request')
    def reject_friend_request(self, request, *args, **kwargs):
        """
            This function rejects a friend request by updating its status to rejected.

            :param request: The HTTP request object containing user information.
            :return: A Response object with a message indicating if the rejection was successful or if there was an error.
                    The response includes a status code to indicate the outcome.
        """
        request_id = request.data.get("request_id")

        if not request_id:
            return Response(
                {"error": "Request ID is required."}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            friend_request = get_object_or_404(FriendRequest, pk=request_id, status=1)
        except Http404:
            return Response(
                {"error": "This friend request is no longer pending."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if friend_request.requested_user != request.user:
            return Response(
                {"error": "You do not have permission to accept this friend request."},
                status=status.HTTP_403_FORBIDDEN,
            )

        friend_request.status = 3
        friend_request.save()

        return Response(
            {"message": "Friend request rejected successfully."},
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=['get'], url_path='list_pending_friends_request')
    def list_pending_friends_request(self, request, *args, **kwargs):
        """
            This function lists pending friend requests for a specific user.

            :param request: The HTTP request object containing user information.
            :return: A response with a message and data about pending friend requests.
                    If there are pending requests, it returns "Listed Pending Friends Requests" with the request data.
                    If there are no pending requests, it returns "You don't have any pending friend requests."
        """
        user = request.user
        request_user = get_object_or_404(User, pk=user.id)

        pending_requests = FriendRequest.objects.filter(
            requested_user=request_user, status=1
        )

        if pending_requests.exists():
            serializer = FriendRequestSerializer(pending_requests, many=True)
            custom_data = {
                "message": "Listed Pending Friends Requests.",
                "data": serializer.data,
            }
            return Response(custom_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "You don't have any pending friend requests."},
                status=status.HTTP_200_OK,
            )

    @action(detail=False, methods=['get'], url_path='list_friends')
    def list_friends(self, request, *args, **kwargs):
        """
            List the friends of a user based on accepted friend requests (status=2) Accepted.

            :param request: The current HTTP request object.
            :return: A response with a success message and the friends list data if there are friends,
                    or a message indicating no friends if the list is empty.
        """
        user = request.user
        request_user = get_object_or_404(User, pk=user.id)

        friends_list = [
            friends.request_received_user
            for friends in FriendRequest.objects.filter(
                requested_user=request_user, status=2
            )
        ]
        if friends_list:
            serializer = UserDisplaySerializer(friends_list, many=True)
            custom_data = {
                "message": "Listed Friends List successfully.",
                "data": serializer.data,
            }
            return Response(custom_data, status=status.HTTP_200_OK)
        else:
            return Response(
                {"message": "You don't have any friends."}, status=status.HTTP_200_OK
            )

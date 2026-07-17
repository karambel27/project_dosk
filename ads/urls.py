from django.urls import path

from . import views
from .models import Response

urlpatterns = [
    path("", views.IndexView.as_view(), name="home"),
    path("ads/create/", views.CreateAdsView.as_view(), name="createdads"),
    path("ads/<int:pk>/", views.ShowAdsView.as_view(), name="showads"),
    path("ads/<int:pk>/edit/", views.UpdateAdsView.as_view(), name="updatedads"),
    path("ads/<int:pk>/delete/", views.DeleteAdsView.as_view(), name="deletedads"),
    path("ads/<int:pk>/responses/", views.CreateResponseView.as_view(), name="create_response"),
    path("profiles/<int:pk>/", views.ProfileShowView.as_view(), name="profileshow"),
    path("responses/", views.ResponsesMenuView.as_view(), name="responses_menu"),
    path("responses/mine/", views.MyResponse.as_view(), name="myresponse"),
    path("responses/received/", views.ResponseAds.as_view(), name="myresponseads"),
    path(
        "responses/<int:pk>/accept/",
        views.update_response_status,
        {"target_status": Response.Status.ACCEPTED},
        name="accept",
    ),
    path(
        "responses/<int:pk>/reject/",
        views.update_response_status,
        {"target_status": Response.Status.REJECTED},
        name="reject",
    ),
    path("ads/mine/", views.MyAds.as_view(), name="myads"),
]

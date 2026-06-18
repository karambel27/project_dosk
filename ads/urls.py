from django.urls import path
from . import views
from .views import CreateResponseView

urlpatterns = [
    path('', views.IndexView.as_view(), name='home'),
    path('showads/<int:pk>', views.ShowAdsView.as_view(), name='showads'),
    path('createdads/', views.CreateAdsView.as_view(), name='createdads'),
    path('updatedads/<int:pk>', views.UpdateAdsView.as_view(), name='updatedads'),
    path('deletedads/<int:pk>', views.DeleteAdsView.as_view(), name='deletedads'),
    path('showads/<int:pk>/response/', CreateResponseView.as_view(), name='create_response'),
    path('profileshow/<int:pk>', views.ProfileShowView.as_view(), name='profileshow'),
    path('myresponse/', views.MyResponse.as_view(), name='myresponse'),
    path('myresponseads/', views.ResponseAds.as_view(), name='myresponseads'),
    path('responsensesmenu/', views.ResponsesMenuView.as_view(), name='responsensesmenu'),
    path('accept/<int:pk>', views.acceptres, name='accept'),
    path('delete/<int:pk>', views.deleteres, name='delete'),
    path('myads/', views.MyAds.as_view(), name='myads'),
]

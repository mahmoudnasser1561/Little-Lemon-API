from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import views

urlpatterns = [
    path(
        'groups/manager/users',
        views.GroupViewSet.as_view({'get': 'list'})
    ),

    path('api-token-auth/', obtain_auth_token),
    # path("users/", include("djoser.urls")),
    
    path('categories/', views.CategoriesView.as_view()),
    
    path(
        'menu-items/', 
         views.MenuItemsView.as_view()
    ),
    
    path(
        'menu-items/<int:pk>',
        views.SingleMenuItemView.as_view()
    ),
]

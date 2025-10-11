from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
  path("", views.start, name="start"),  # 👈 new start page (default)
  # 🏠 Home (redirects to welcome or login)
    path("", views.home, name="home"),

    # 🔐 Authentication
    path("register/", views.register, name="reg"),
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),

    # 👤 User Pages
    path("welcome/", views.welcome, name="welcome"),
    path("profile/", views.profile, name="profile"),
  path('edit/<str:doc_id>/', views.edit_user, name='edit_user'),
  path('delete/<str:doc_id>/', views.delete_user, name='delete_user'),

  # 💬 Contact Pages
    path("contact/", views.contacts, name="contact"),
    path('show/', views.show_data, name='show'),


  # ⚙️ Admin Panel
    path("admin/", admin.site.urls),

path("edit-profile/", views.edit_profile, name="edit_profile"),


]

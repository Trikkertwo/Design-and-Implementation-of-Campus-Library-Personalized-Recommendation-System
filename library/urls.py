from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),
    path('password/reset/', views.password_reset_view, name='password_reset'),
    path('password/change/', views.password_change_view, name='password_change'),
    path('captcha/refresh/', views.refresh_captcha, name='refresh_captcha'),

    path('books/', views.book_list, name='book_list'),
    path('books/<int:book_id>/', views.book_detail, name='book_detail'),
    path('books/<int:book_id>/borrow/', views.borrow_book, name='borrow_book'),
    path('books/<int:book_id>/return/', views.return_book, name='return_book'),
    path('books/<int:book_id>/renew/', views.renew_book, name='renew_book'),
    path('books/<int:book_id>/favorite/', views.toggle_favorite, name='toggle_favorite'),
    path('books/<int:book_id>/rate/', views.rate_book, name='rate_book'),
    path('books/<int:book_id>/comment/', views.add_comment, name='add_comment'),

    path('history/', views.history, name='history'),
    path('notifications/', views.notification_list, name='notification_list'),

    path('dashboard/', views.dashboard, name='dashboard'),
    path('dashboard/books/', views.dashboard_books, name='dashboard_books'),
    path('dashboard/books/new/', views.dashboard_book_create, name='dashboard_book_create'),
    path('dashboard/books/<int:book_id>/edit/', views.dashboard_book_edit, name='dashboard_book_edit'),
    path('dashboard/books/<int:book_id>/delete/', views.dashboard_book_delete, name='dashboard_book_delete'),
    path('dashboard/users/', views.dashboard_users, name='dashboard_users'),
    path('dashboard/users/<int:user_id>/toggle/', views.dashboard_user_toggle, name='dashboard_user_toggle'),
    path('dashboard/borrows/', views.dashboard_borrows, name='dashboard_borrows'),
    path('dashboard/comments/', views.dashboard_comments, name='dashboard_comments'),
    path('dashboard/comments/<int:comment_id>/delete/', views.dashboard_comment_delete, name='dashboard_comment_delete'),
    path('dashboard/recommendations/', views.dashboard_recommendation, name='dashboard_recommendation'),
]

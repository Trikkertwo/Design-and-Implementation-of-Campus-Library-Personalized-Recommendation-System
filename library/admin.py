from django.contrib import admin

from .models import Book, BorrowRecord, Comment, Favorite, Footprint, Notification, Rating, RecommendationLog


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'isbn', 'category', 'publish_year', 'available_copies')
    search_fields = ('title', 'author', 'isbn', 'category')
    list_filter = ('category', 'publish_year')


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'book', 'status', 'borrowed_at', 'due_date', 'renew_count')
    list_filter = ('status',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('book', 'user', 'is_deleted', 'created_at')
    list_filter = ('is_deleted',)


admin.site.register([Favorite, Rating, Notification, Footprint, RecommendationLog])

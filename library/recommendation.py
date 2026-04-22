from django.db.models import Avg, Count

from .models import Book, BorrowRecord, Favorite


def hot_books(limit=8):
    return Book.objects.annotate(
        borrow_count=Count('borrowrecord')
    ).order_by('-borrow_count', '-created_at')[:limit]


def new_books(limit=8):
    return Book.objects.order_by('-created_at')[:limit]


def personalized_books(user, limit=8):
    categories = list(
        BorrowRecord.objects.filter(user=user).values('book__category').annotate(c=Count('id')).order_by('-c')
    )
    if categories:
        top = [item['book__category'] for item in categories[:3]]
        viewed = BorrowRecord.objects.filter(user=user).values_list('book_id', flat=True)
        return Book.objects.filter(category__in=top).exclude(id__in=viewed).order_by('-created_at')[:limit]
    favored = Favorite.objects.filter(user=user).values_list('book_id', flat=True)
    if favored:
        return Book.objects.exclude(id__in=favored).order_by('-created_at')[:limit]
    return hot_books(limit)


def similar_books(book, limit=6):
    related_users = BorrowRecord.objects.filter(book=book).values_list('user_id', flat=True)
    qs = Book.objects.filter(borrowrecord__user_id__in=related_users).exclude(id=book.id).annotate(
        score=Count('borrowrecord')
    ).order_by('-score', '-created_at')
    if qs.exists():
        return qs[:limit]
    return Book.objects.filter(category=book.category).exclude(id=book.id).order_by('-created_at')[:limit]


def guess_you_like(user, limit=8):
    return Book.objects.annotate(avg_score=Avg('rating__score')).order_by('-avg_score', '-created_at')[:limit]

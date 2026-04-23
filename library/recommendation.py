from collections import Counter
from itertools import chain

from django.db.models import Avg, Case, Count, ExpressionWrapper, F, FloatField, Value, When
from django.db.models.functions import Coalesce

from .models import Book, BorrowRecord, Favorite, Footprint

BORROW_CATEGORY_WEIGHT = 3
FAVORITE_CATEGORY_WEIGHT = 2
FOOTPRINT_CATEGORY_WEIGHT = 1

PERSONALIZED_BORROW_SIGNAL_WEIGHT = 0.45
PERSONALIZED_RATING_SIGNAL_WEIGHT = 0.35
PERSONALIZED_CATEGORY_SIGNAL_WEIGHT = 0.20

GUESS_RATING_SIGNAL_WEIGHT = 0.45
GUESS_BORROW_SIGNAL_WEIGHT = 0.35
GUESS_USER_MATCH_WEIGHT = 0.20
GUESS_TOP_CATEGORY_LIMIT = 3
PERSONALIZED_TOP_CATEGORY_LIMIT = 4


def hot_books(limit=8):
    return Book.objects.annotate(
        borrow_count=Count('borrowrecord')
    ).order_by('-borrow_count', '-created_at')[:limit]


def new_books(limit=8):
    return Book.objects.order_by('-created_at')[:limit]


def personalized_books(user, limit=8):
    borrowed_categories = BorrowRecord.objects.filter(user=user).values_list('book__category', flat=True)
    favored_categories = Favorite.objects.filter(user=user).values_list('book__category', flat=True)
    footprint_categories = Footprint.objects.filter(user=user).values_list('book__category', flat=True)

    category_weights = Counter()
    for category in borrowed_categories:
        category_weights[category] += BORROW_CATEGORY_WEIGHT
    for category in favored_categories:
        category_weights[category] += FAVORITE_CATEGORY_WEIGHT
    for category in footprint_categories:
        category_weights[category] += FOOTPRINT_CATEGORY_WEIGHT

    interacted_book_ids = set(
        chain(
            BorrowRecord.objects.filter(user=user).values_list('book_id', flat=True),
            Favorite.objects.filter(user=user).values_list('book_id', flat=True),
            Footprint.objects.filter(user=user).values_list('book_id', flat=True),
        )
    )

    qs = Book.objects.exclude(id__in=interacted_book_ids).annotate(
        borrow_count=Count('borrowrecord'),
        avg_score=Coalesce(Avg('rating__score'), Value(0.0), output_field=FloatField()),
    )
    if category_weights:
        top_categories = dict(category_weights.most_common(PERSONALIZED_TOP_CATEGORY_LIMIT))
        category_score = Case(
            *[When(category=category, then=Value(float(weight))) for category, weight in top_categories.items()],
            default=Value(0.0),
            output_field=FloatField(),
        )
    else:
        category_score = Value(0.0, output_field=FloatField())
    return qs.annotate(
        recommendation_score=ExpressionWrapper(
            F('borrow_count') * Value(PERSONALIZED_BORROW_SIGNAL_WEIGHT)
            + F('avg_score') * Value(PERSONALIZED_RATING_SIGNAL_WEIGHT)
            + category_score * Value(PERSONALIZED_CATEGORY_SIGNAL_WEIGHT),
            output_field=FloatField(),
        )
    ).order_by('-recommendation_score', '-created_at')[:limit]


def similar_books(book, limit=6):
    related_users = BorrowRecord.objects.filter(book=book).values_list('user_id', flat=True)
    qs = Book.objects.filter(borrowrecord__user_id__in=related_users).exclude(id=book.id).annotate(
        score=Count('borrowrecord')
    ).order_by('-score', '-created_at')
    if qs.exists():
        return qs[:limit]
    return Book.objects.filter(category=book.category).exclude(id=book.id).order_by('-created_at')[:limit]


def guess_you_like(user, limit=8):
    preferred_categories = list(
        BorrowRecord.objects.filter(user=user)
        .values('book__category')
        .annotate(c=Count('id'))
        .order_by('-c')
        .values_list('book__category', flat=True)[:GUESS_TOP_CATEGORY_LIMIT]
    )
    qs = Book.objects.annotate(
        borrow_count=Count('borrowrecord'),
        avg_score=Coalesce(Avg('rating__score'), Value(0.0), output_field=FloatField()),
    )
    if preferred_categories:
        qs = qs.annotate(
            user_match=Case(
                *[When(category=category, then=Value(1.0)) for category in preferred_categories],
                default=Value(0.0),
                output_field=FloatField(),
            )
        )
    else:
        qs = qs.annotate(user_match=Value(0.0, output_field=FloatField()))
    return qs.annotate(
        score=ExpressionWrapper(
            F('avg_score') * Value(GUESS_RATING_SIGNAL_WEIGHT)
            + F('borrow_count') * Value(GUESS_BORROW_SIGNAL_WEIGHT)
            + F('user_match') * Value(GUESS_USER_MATCH_WEIGHT),
            output_field=FloatField(),
        )
    ).order_by('-score', '-created_at')[:limit]

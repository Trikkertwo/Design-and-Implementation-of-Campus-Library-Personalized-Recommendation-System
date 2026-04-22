from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Book, BorrowRecord
from .recommendation import hot_books


class LibraryFlowTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='u1', password='Pass12345!')
        self.book = Book.objects.create(
            title='Python 实战',
            author='张三',
            isbn='9787302000001',
            category='计算机',
            publisher='清华大学出版社',
            publish_year=2025,
            summary='desc',
            total_copies=3,
            available_copies=3,
        )

    def test_borrow_return_flow(self):
        self.client.force_login(self.user)
        self.client.post(reverse('borrow_book', args=[self.book.id]))
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 2)
        self.assertEqual(BorrowRecord.objects.filter(user=self.user).count(), 1)

        self.client.post(reverse('return_book', args=[self.book.id]))
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_copies, 3)

    def test_hot_recommendation(self):
        other = User.objects.create_user(username='u2', password='Pass12345!')
        BorrowRecord.objects.create(user=self.user, book=self.book, due_date=timezone.now())
        BorrowRecord.objects.create(user=other, book=self.book, due_date=timezone.now())
        self.assertEqual(list(hot_books(limit=1))[0].id, self.book.id)

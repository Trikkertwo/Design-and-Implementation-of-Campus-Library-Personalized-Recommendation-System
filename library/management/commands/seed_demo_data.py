import random
from datetime import timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from library.models import Book, BorrowRecord, Comment, Favorite, Notification, Rating


class Command(BaseCommand):
    help = '填充演示数据：>=300 图书 + 关联借阅收藏评分评论通知'

    def handle(self, *args, **options):
        random.seed(20260422)
        categories = ['计算机', '数学', '文学', '历史', '经济', '管理', '艺术', '外语']
        publishers = ['高教出版社', '机械工业出版社', '清华大学出版社', '人民邮电出版社', '电子工业出版社']

        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'Admin123!')
            self.stdout.write(self.style.SUCCESS('已创建管理员 admin / Admin123!'))

        users = []
        for i in range(1, 61):
            username = f'user{i:03d}'
            user, _ = User.objects.get_or_create(username=username, defaults={'email': f'{username}@example.com'})
            user.set_password('User12345!')
            user.save(update_fields=['password'])
            users.append(user)

        books = []
        for i in range(1, 321):
            category = random.choice(categories)
            total = random.randint(3, 12)
            book, _ = Book.objects.get_or_create(
                isbn=f'9787302{i:06d}',
                defaults={
                    'title': f'{category}导论与实践 {i}',
                    'author': f'作者{i % 80 + 1}',
                    'category': category,
                    'publisher': random.choice(publishers),
                    'publish_year': random.randint(2010, 2026),
                    'summary': f'本书为{category}方向教学与实践参考，包含案例、方法论、课堂与项目建议，适合本科生学习。',
                    'cover_url': 'https://picsum.photos/seed/bookdemo/300/420',
                    'total_copies': total,
                    'available_copies': total,
                },
            )
            books.append(book)

        for user in users:
            sample_books = random.sample(books, k=random.randint(8, 20))
            for book in sample_books:
                score = random.randint(1, 5)
                Rating.objects.update_or_create(user=user, book=book, defaults={'score': score})
                if random.random() > 0.55:
                    Favorite.objects.get_or_create(user=user, book=book)
                if random.random() > 0.65:
                    Comment.objects.get_or_create(
                        user=user,
                        book=book,
                        content=f'这本书对我很有帮助，尤其是第{random.randint(1, 8)}章。',
                    )
                if random.random() > 0.4:
                    days = random.randint(5, 60)
                    record, _ = BorrowRecord.objects.get_or_create(
                        user=user,
                        book=book,
                        borrowed_at=timezone.now() - timedelta(days=days),
                        defaults={'due_date': timezone.now() + timedelta(days=random.randint(-5, 30))},
                    )
                    if record.due_date < timezone.now() and random.random() > 0.5:
                        Notification.objects.get_or_create(
                            user=user,
                            title='借阅到期提醒',
                            content=f'《{book.title}》已到期，请尽快办理归还。',
                        )

        self.stdout.write(self.style.SUCCESS('演示数据填充完成：图书>=320，用户=60，含借阅/收藏/评分/评论/通知数据'))

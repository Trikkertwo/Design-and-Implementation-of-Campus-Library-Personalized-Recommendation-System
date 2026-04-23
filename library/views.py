import random
import string
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Count
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import BookForm, CommentForm, LoginForm, RegisterForm, ResetPasswordForm
from .models import Book, BorrowRecord, Comment, Favorite, Footprint, Notification, Rating, RecommendationLog
from .recommendation import guess_you_like, hot_books, new_books, personalized_books, similar_books


CAPTCHA_KEY = 'simple_captcha'
DEFAULT_BOOK_COVER_URL = 'https://picsum.photos/seed/defaultbook/240/340'


def _generate_captcha():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))


def _captcha(request):
    code = request.session.get(CAPTCHA_KEY)
    if not code:
        code = _generate_captcha()
        request.session[CAPTCHA_KEY] = code
    return code


def _validate_captcha(request, captcha):
    return captcha.upper() == request.session.get(CAPTCHA_KEY, '').upper()


def refresh_captcha(request):
    code = _generate_captcha()
    request.session[CAPTCHA_KEY] = code
    return JsonResponse({'captcha': code})


def register_view(request):
    form = RegisterForm(request.POST or None)
    captcha = _captcha(request)
    if request.method == 'POST' and form.is_valid():
        if not _validate_captcha(request, form.cleaned_data['captcha']):
            messages.error(request, '验证码错误')
        else:
            User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password'],
            )
            request.session[CAPTCHA_KEY] = _generate_captcha()
            messages.success(request, '注册成功，请登录')
            return redirect('login')
    return render(request, 'auth/register.html', {'form': form, 'captcha': captcha})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(request.POST or None)
    captcha = _captcha(request)
    if request.method == 'POST' and form.is_valid():
        if not _validate_captcha(request, form.cleaned_data['captcha']):
            messages.error(request, '验证码错误')
        else:
            user = authenticate(username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            if user and user.is_active:
                login(request, user)
                request.session[CAPTCHA_KEY] = _generate_captcha()
                return redirect('home')
            messages.error(request, '用户名或密码错误，或账号被禁用')
    return render(request, 'auth/login.html', {'form': form, 'captcha': captcha})


def logout_view(request):
    logout(request)
    return redirect('login')


def password_reset_view(request):
    form = ResetPasswordForm(request.POST or None)
    captcha = _captcha(request)
    if request.method == 'POST' and form.is_valid():
        if not _validate_captcha(request, form.cleaned_data['captcha']):
            messages.error(request, '验证码错误')
        else:
            user = User.objects.filter(username=form.cleaned_data['username']).first()
            if not user:
                messages.error(request, '用户不存在')
            else:
                user.set_password(form.cleaned_data['new_password'])
                user.save(update_fields=['password'])
                request.session[CAPTCHA_KEY] = _generate_captcha()
                messages.success(request, '密码已重置，请重新登录')
                return redirect('login')
    return render(request, 'auth/password_reset.html', {'form': form, 'captcha': captcha})


@login_required
def password_change_view(request):
    if request.method == 'POST':
        old_password = request.POST.get('old_password', '')
        new_password = request.POST.get('new_password', '')
        if not request.user.check_password(old_password):
            messages.error(request, '原密码错误')
        elif len(new_password) < 6:
            messages.error(request, '新密码至少 6 位')
        else:
            request.user.set_password(new_password)
            request.user.save(update_fields=['password'])
            update_session_auth_hash(request, request.user)
            messages.success(request, '密码修改成功')
            return redirect('home')
    return render(request, 'auth/password_change.html')


@login_required
def home(request):
    RecommendationLog.objects.create(user=request.user, strategy='home', note='首页推荐展示')
    context = {
        'hot_books': hot_books(),
        'new_books': new_books(),
        'personalized_books': personalized_books(request.user),
        'guess_books': guess_you_like(request.user),
        'default_book_cover_url': DEFAULT_BOOK_COVER_URL,
    }
    return render(request, 'home.html', context)


@login_required
def book_list(request):
    qs = Book.objects.all()
    keyword = request.GET.get('keyword', '').strip()
    author = request.GET.get('author', '').strip()
    isbn = request.GET.get('isbn', '').strip()
    category = request.GET.get('category', '').strip()
    if keyword:
        qs = qs.filter(title__icontains=keyword)
    if author:
        qs = qs.filter(author__icontains=author)
    if isbn:
        qs = qs.filter(isbn__icontains=isbn)
    if category:
        qs = qs.filter(category__icontains=category)
    return render(request, 'book_list.html', {
        'books': qs[:100],
        'query': request.GET,
        'default_book_cover_url': DEFAULT_BOOK_COVER_URL,
    })


@login_required
def book_detail(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    Footprint.objects.create(user=request.user, book=book)
    comments = Comment.objects.filter(book=book, is_deleted=False)
    user_borrow = BorrowRecord.objects.filter(user=request.user, book=book, status=BorrowRecord.STATUS_BORROWED).first()
    is_favorited = Favorite.objects.filter(user=request.user, book=book).exists()
    RecommendationLog.objects.create(user=request.user, strategy='similar', note=f'查看图书 {book_id}')
    return render(request, 'book_detail.html', {
        'book': book,
        'comments': comments,
        'similar_books': similar_books(book),
        'user_borrow': user_borrow,
        'is_favorited': is_favorited,
        'comment_form': CommentForm(),
        'default_book_cover_url': DEFAULT_BOOK_COVER_URL,
    })


@login_required
@require_POST
def borrow_book(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    if book.available_copies == 0:
        messages.error(request, '库存不足，无法借阅')
        return redirect('book_detail', book_id=book_id)
    if BorrowRecord.objects.filter(user=request.user, book=book, status=BorrowRecord.STATUS_BORROWED).exists():
        messages.error(request, '该图书已在借阅中，无需重复借阅')
        return redirect('book_detail', book_id=book_id)
    active_count = BorrowRecord.objects.filter(user=request.user, status=BorrowRecord.STATUS_BORROWED).count()
    if active_count >= 10:
        messages.error(request, '单用户最多同时借阅10本')
        return redirect('book_detail', book_id=book_id)
    BorrowRecord.objects.create(
        user=request.user,
        book=book,
        due_date=timezone.now() + timedelta(days=30),
    )
    book.available_copies -= 1
    book.save(update_fields=['available_copies'])
    Notification.objects.create(user=request.user, title='借阅成功', content=f'《{book.title}》已借阅，30天后到期。')
    messages.success(request, '借阅成功')
    return redirect('book_detail', book_id=book_id)


@login_required
@require_POST
def return_book(request, book_id):
    borrow = BorrowRecord.objects.filter(user=request.user, book_id=book_id, status=BorrowRecord.STATUS_BORROWED).first()
    if not borrow:
        messages.error(request, '没有待归还记录')
        return redirect('book_detail', book_id=book_id)
    borrow.status = BorrowRecord.STATUS_RETURNED
    borrow.returned_at = timezone.now()
    borrow.save(update_fields=['status', 'returned_at'])
    borrow.book.available_copies = min(borrow.book.available_copies + 1, borrow.book.total_copies)
    borrow.book.save(update_fields=['available_copies'])
    messages.success(request, '归还成功')
    return redirect('book_detail', book_id=book_id)


@login_required
@require_POST
def renew_book(request, book_id):
    borrow = BorrowRecord.objects.filter(user=request.user, book_id=book_id, status=BorrowRecord.STATUS_BORROWED).first()
    if not borrow:
        messages.error(request, '没有可续借记录')
    elif borrow.renew_count >= 2:
        messages.error(request, '最多续借2次')
    else:
        borrow.renew_count += 1
        borrow.due_date += timedelta(days=15)
        borrow.save(update_fields=['renew_count', 'due_date'])
        messages.success(request, '续借成功')
    return redirect('book_detail', book_id=book_id)


@login_required
@require_POST
def toggle_favorite(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    favorite, created = Favorite.objects.get_or_create(user=request.user, book=book)
    if not created:
        favorite.delete()
        messages.success(request, '已取消收藏')
    else:
        messages.success(request, '收藏成功')
    return redirect('book_detail', book_id=book_id)


@login_required
@require_POST
def rate_book(request, book_id):
    try:
        score = int(request.POST.get('score', '0'))
    except ValueError:
        score = 0
    if score < 1 or score > 5:
        messages.error(request, '评分需在1~5之间')
        return redirect('book_detail', book_id=book_id)
    book = get_object_or_404(Book, pk=book_id)
    Rating.objects.update_or_create(user=request.user, book=book, defaults={'score': score})
    messages.success(request, '评分成功')
    return redirect('book_detail', book_id=book_id)


@login_required
@require_POST
def add_comment(request, book_id):
    form = CommentForm(request.POST)
    if form.is_valid():
        Comment.objects.create(user=request.user, book_id=book_id, content=form.cleaned_data['content'])
        messages.success(request, '评论发布成功')
    else:
        messages.error(request, '评论内容不能为空或超长')
    return redirect('book_detail', book_id=book_id)


@login_required
def history(request):
    borrows = BorrowRecord.objects.filter(user=request.user)[:50]
    favorites = Favorite.objects.filter(user=request.user)[:50]
    footprints = Footprint.objects.filter(user=request.user)[:50]
    return render(request, 'history.html', {'borrows': borrows, 'favorites': favorites, 'footprints': footprints})


@login_required
def notification_list(request):
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    now = timezone.now()
    due_soon = BorrowRecord.objects.filter(
        user=request.user,
        status=BorrowRecord.STATUS_BORROWED,
        due_date__lte=now + timedelta(days=3),
    )
    for item in due_soon:
        Notification.objects.get_or_create(
            user=request.user,
            title='到期提醒',
            content=f'《{item.book.title}》将在 {item.due_date.strftime("%Y-%m-%d")} 到期，请及时归还。',
        )
    notifications = Notification.objects.filter(user=request.user)[:100]
    return render(request, 'notifications.html', {'notifications': notifications})


def _staff_required(user):
    return user.is_authenticated and user.is_staff


@user_passes_test(_staff_required)
def dashboard(request):
    stats = {
        'borrow_count': BorrowRecord.objects.count(),
        'hot_books': Book.objects.annotate(c=Count('borrowrecord')).order_by('-c')[:10],
        'active_users': User.objects.filter(is_active=True).count(),
        'book_count': Book.objects.count(),
    }
    return render(request, 'dashboard/index.html', stats)


@user_passes_test(_staff_required)
def dashboard_books(request):
    books = Book.objects.all()[:200]
    return render(request, 'dashboard/books.html', {'books': books})


@user_passes_test(_staff_required)
def dashboard_book_create(request):
    form = BookForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '图书创建成功')
        return redirect('dashboard_books')
    return render(request, 'dashboard/book_form.html', {'form': form, 'title': '新增图书'})


@user_passes_test(_staff_required)
def dashboard_book_edit(request, book_id):
    book = get_object_or_404(Book, pk=book_id)
    form = BookForm(request.POST or None, instance=book)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '图书修改成功')
        return redirect('dashboard_books')
    return render(request, 'dashboard/book_form.html', {'form': form, 'title': '编辑图书'})


@user_passes_test(_staff_required)
@require_POST
def dashboard_book_delete(request, book_id):
    get_object_or_404(Book, pk=book_id).delete()
    messages.success(request, '图书已删除')
    return redirect('dashboard_books')


@user_passes_test(_staff_required)
def dashboard_users(request):
    users = User.objects.all()[:200]
    return render(request, 'dashboard/users.html', {'users': users})


@user_passes_test(_staff_required)
@require_POST
def dashboard_user_toggle(request, user_id):
    user = get_object_or_404(User, pk=user_id)
    if not user.is_superuser:
        user.is_active = not user.is_active
        user.save(update_fields=['is_active'])
    return redirect('dashboard_users')


@user_passes_test(_staff_required)
def dashboard_borrows(request):
    borrows = BorrowRecord.objects.select_related('book', 'user')[:200]
    return render(request, 'dashboard/borrows.html', {'borrows': borrows})


@user_passes_test(_staff_required)
def dashboard_comments(request):
    comments = Comment.objects.select_related('book', 'user')[:200]
    return render(request, 'dashboard/comments.html', {'comments': comments})


@user_passes_test(_staff_required)
@require_POST
def dashboard_comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, pk=comment_id)
    comment.is_deleted = True
    comment.save(update_fields=['is_deleted'])
    return redirect('dashboard_comments')


@user_passes_test(_staff_required)
def dashboard_recommendation(request):
    RecommendationLog.objects.create(user=request.user, strategy='manual_refresh', note='管理员手动刷新模型')
    logs = RecommendationLog.objects.select_related('user')[:100]
    return render(request, 'dashboard/recommendations.html', {'logs': logs})

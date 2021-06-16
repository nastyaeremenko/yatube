from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post


User = get_user_model()


def index(request):
    post_list = Post.objects.select_related('group').all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {'page': page,
               'paginator': paginator}
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts = group.groups.all()

    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {'group': group,
               'page': page,
               'paginator': paginator}
    return render(request, 'posts/group.html', context)


@login_required
def new_post(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('index')

    return render(request, 'posts/new_post.html', {'form': form})


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = author.posts.all()

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    posts_count = post_list.count()

    follows = Follow.objects.all()
    followers_count = author.follower.count()
    following_count = author.following.count()

    following = (request.user.is_authenticated and
                 follows.filter(user=request.user, author=author).exists())

    context = {'page': page,
               'author': author,
               'paginator': paginator,
               'posts_count': posts_count,
               'followers_count': followers_count,
               'following_count': following_count,
               'following': following}
    return render(request, 'posts/profile.html', context)


def post_view(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    author = post.author
    posts_count = author.posts.all().count()
    comments = post.comments.all()
    form = CommentForm()

    follows = Follow.objects.all()
    followers_count = author.follower.count()
    following_count = author.following.count()

    following = (request.user.is_authenticated and
                 follows.filter(user=request.user, author=author).exists())

    context = {'post': post,
               'author': author,
               'posts_count': posts_count,
               'comments': comments,
               'form': form,
               'followers_count': followers_count,
               'following_count': following_count,
               'following': following}
    return render(request, 'posts/post.html', context)


@login_required
def post_edit(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)

    if post.author != request.user:
        return redirect('post', username=username, post_id=post_id)

    form = PostForm(
        request.POST or None, files=request.FILES or None, instance=post)
    if form.is_valid():
        post.save()
        return redirect('post', username=username, post_id=post_id)

    context = {'form': form,
               'post': post,
               'is_edit': True}
    return render(request, 'posts/new_post.html', context)


def page_not_found(request, exception):
    return render(
        request,
        "misc/404.html",
        {"path": request.path},
        status=404
    )


def server_error(request):
    return render(request, "misc/500.html", status=500)


@login_required
def add_comment(request, username, post_id):
    post = get_object_or_404(Post, pk=post_id, author__username=username)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        form.save()

    return redirect('post', username=username, post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)

    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page = paginator.get_page(page_number)

    context = {'page': page,
               'paginator': paginator}
    return render(request, "posts/follow.html", context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if author != request.user:
        Follow.objects.get_or_create(
            user=request.user,
            author=author)
    return redirect('profile', username=username)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('profile', username=username)

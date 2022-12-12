from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


def get_page(objct, page_number, objects_per_page=settings.OBJECTS_PER_PAGE):
    paginator = Paginator(objct, objects_per_page)
    return paginator.get_page(page_number)


def index(request):
    template = 'posts/index.html'
    posts = Post.objects.all()
    page_number = request.GET.get('page')
    context = {
        'page_obj': get_page(posts, page_number),
    }

    return render(request, template, context)


def group_posts(request, slug):
    template = 'posts/group_list.html'
    group = get_object_or_404(Group, slug=slug)
    posts = group.posts.all()
    page_number = request.GET.get('page')
    context = {
        'group': group,
        'page_obj': get_page(posts, page_number),
    }

    return render(request, template, context)


def profile(request, username):
    template = 'posts/profile.html'
    author = get_object_or_404(User, username=username)
    user_posts = author.posts.all()
    page_number = request.GET.get('page')
    following = False
    if request.user.is_authenticated:
        following = request.user.follower.filter(author=author).exists()
    context = {
        'author': author,
        'page_obj': get_page(user_posts, page_number),
        'following': following,
    }

    return render(request, template, context)


def post_detail(request, post_id):
    template = 'posts/post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    form = CommentForm()
    comments = post.comments.all()
    context = {
        'form': form,
        'post': post,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        form = form.save(commit=False)
        form.author = request.user
        form.save()
        return redirect('posts:profile', request.user)
    template = 'posts/create_post.html'
    context = {
        'form': form
    }

    return render(request, template, context=context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id)

    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post
    )
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)

    template = 'posts/create_post.html'
    context = {
        'post': post,
        'form': form,
        'is_edit': True
    }

    return render(request, template, context=context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = get_object_or_404(Post, pk=post_id)
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    posts = Post.objects.filter(author__following__user=request.user)
    page_number = request.GET.get('page')
    context = {
        'page_obj': get_page(posts, page_number),
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    try:
        Follow.objects.create(
            user=request.user,
            author=get_object_or_404(User, username=username),
        )
    except Exception:
        return redirect('posts:profile', username)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(
        user=request.user,
        author=get_object_or_404(User, username=username),
    ).delete()
    return redirect('posts:profile', username)


# -----------
# from django.views.generic import ListView, DetailView

# path('', views.Index.as_view(), name='index'),
# class Index(ListView):  # работает
#     model = Post
#     template_name = 'posts/index.html'
#     paginate_by = settings.OBJECTS_PER_PAGE

# path('group/<slug:slug>/', views.Group_posts.as_view(), name='group_list'),
# class Group_posts(ListView): # работает
#     template_name = 'posts/group_list.html'
#     paginate_by = settings.OBJECTS_PER_PAGE

#     def get_queryset(self):
#         group = get_object_or_404(Group, slug=self.kwargs['slug']) # !!!!!
#         return group.posts.all()

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         slug = self.kwargs['slug']
#         context['group'] = get_object_or_404(Group, slug=slug) # !!!!!
#         return context

# path('profile/<str:username>/', views.Profile.as_view(), name='profile'),
# class Profile(DetailView): # не работает
#     model = User
#     template_name = 'posts/profile.html'
#     paginate_by = settings.OBJECTS_PER_PAGE
#     slug_url_kwarg = 'username'
#     context_object_name = 'author'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         following = False
#         print(self.kwargs['username'])
#         author = get_object_or_404(User, username=self.kwargs['username'])
#         user_posts = author.posts.all()
#         context['following'] = following
#         return context


# path('posts/<int:post_id>/', views.Post_detail.as_view(), name='post_detail')
# class Post_detail(DetailView):  # работает
#     model = Post
#     template_name = 'posts/post_detail.html'
#     paginate_by = settings.OBJECTS_PER_PAGE
#     pk_url_kwarg = 'post_id'
#     context_object_name = 'post'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['form'] = CommentForm()
#         post = get_object_or_404(Post, pk=self.kwargs['post_id']) # !!!!!
#         #post = self.kwargs.get('post')
#         context['comments'] = post.comments.all()
#         return context

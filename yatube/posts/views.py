from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User


class Index(ListView):
    model = Post
    template_name = 'posts/index.html'
    paginate_by = settings.OBJECTS_PER_PAGE


class GroupPosts(ListView):
    model = Post
    template_name = 'posts/group_list.html'
    paginate_by = settings.OBJECTS_PER_PAGE

    def get_queryset(self):
        self.queryset = (
            Post
            .objects
            .select_related('group')
            .filter(group__slug=self.kwargs['slug'])
        )
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['group'] = get_object_or_404(Group, slug=self.kwargs['slug'])
        return context


class Profile(ListView):
    model = Post
    template_name = 'posts/profile.html'
    paginate_by = settings.OBJECTS_PER_PAGE
    context_object_name = 'author'

    def get_queryset(self):
        self.queryset = (
            Post
            .objects
            .select_related('author')
            .filter(author__username=self.kwargs['username'])
        )
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        author = get_object_or_404(User, username=self.kwargs['username'])
        context['author'] = author

        following = False
        if self.request.user.is_authenticated:
            following = self.request.user.follower.filter(
                author=author).exists()
        context['following'] = following

        return context


class PostDetail(DetailView):
    model = Post
    template_name = 'posts/post_detail.html'
    paginate_by = settings.OBJECTS_PER_PAGE
    pk_url_kwarg = 'post_id'
    context_object_name = 'post'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CommentForm()
        context['comments'] = self.object.comments.all()
        return context


class PostCreate(LoginRequiredMixin, CreateView):
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def form_valid(self, form):
        self.object = form.save(commit=False)
        self.object.author = self.request.user
        self.object.save()
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy(
            'posts:profile',
            kwargs={'username': self.request.user}
        )


class PostEdit(LoginRequiredMixin, UpdateView):
    model = Post
    pk_url_kwarg = 'post_id'
    form_class = PostForm
    template_name = 'posts/create_post.html'

    def get_object(self, *args, **kwargs):
        object = super().get_object(*args, **kwargs)
        if object.author != self.request.user:
            redirect('posts:post_detail', self.kwargs['post_id'])
        return object

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_edit'] = True
        return context

    def get_success_url(self):
        return reverse_lazy(
            'posts:post_detail',
            kwargs={'post_id': self.kwargs['post_id']}
        )


class FollowIndex(LoginRequiredMixin, ListView):
    model = Post
    template_name = 'posts/follow.html'
    paginate_by = settings.OBJECTS_PER_PAGE

    def get_queryset(self):
        self.queryset = (
            Post
            .objects
            .filter(author__following__user=self.request.user)
        )
        return super().get_queryset()


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

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import Post, Category, Comment, Like, PostImage
from .forms import PostForm, PostImageFormSet, CommentForm
from .permissions import can_edit_post, can_delete_post, get_visible_posts


@login_required
def community_dashboard(request):

    posts = get_visible_posts(request.user).order_by('-created_at')

    search_query = request.GET.get('search', '')
    if search_query:
        posts = posts.filter(
            Q(title__icontains=search_query) | 
            Q(content__icontains=search_query) |
            Q(excerpt__icontains=search_query)
        )

    category_id = request.GET.get('category')
    if category_id:
        posts = posts.filter(category_id=category_id)
 
    paginator = Paginator(posts, 10) 
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
    }
    return render(request, 'community/post_list.html', context)


@login_required
def post_detail(request, slug):
    """View a single post with comments"""
    post = get_object_or_404(Post, slug=slug, status='published')

    user_role = getattr(request.user, 'role', 'patient')
    if not (post.visible_to_all or 
            (user_role == 'staff' and post.visible_to_staff) or
            (user_role == 'patient' and post.visible_to_patients) or
            request.user.is_superuser):
        messages.error(request, "You don't have permission to view this post.")
        return redirect('community:dashboard')

    post.views_count += 1
    post.save(update_fields=['views_count'])

    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.post = post
            comment.author = request.user
            parent_id = request.POST.get('parent_id')
            if parent_id:
                comment.parent_id = parent_id
            comment.save()
            messages.success(request, "Comment added successfully!")
            return redirect('community:post_detail', slug=slug)
    else:
        comment_form = CommentForm()
    
    comments = post.comments.filter(parent__isnull=True, is_approved=True)
    user_has_liked = post.likes.filter(user=request.user).exists()
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'user_has_liked': user_has_liked,
        'can_edit': can_edit_post(request.user, post),
        'can_delete': can_delete_post(request.user, post),
    }
    return render(request, 'community/post_detail.html', context)


@login_required
def post_create(request):
 
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        image_formset = PostImageFormSet(request.POST, request.FILES)
        
        if form.is_valid() and image_formset.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()

            image_formset.instance = post
            image_formset.save()
            
            messages.success(request, "Post created successfully!")
            return redirect('community:post_detail', slug=post.slug)
    else:
        form = PostForm()
        image_formset = PostImageFormSet()
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'action': 'Create',
    }
    return render(request, 'community/post_form.html', context)


@login_required
def post_edit(request, slug):

    post = get_object_or_404(Post, slug=slug)
    
    if not can_edit_post(request.user, post):
        messages.error(request, "You don't have permission to edit this post.")
        return redirect('community:post_detail', slug=slug)
    
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        image_formset = PostImageFormSet(request.POST, request.FILES, instance=post)
        
        if form.is_valid() and image_formset.is_valid():
            form.save()
            image_formset.save()
            messages.success(request, "Post updated successfully!")
            return redirect('community:post_detail', slug=post.slug)
    else:
        form = PostForm(instance=post)
        image_formset = PostImageFormSet(instance=post)
    
    context = {
        'form': form,
        'image_formset': image_formset,
        'post': post,
        'action': 'Edit',
    }
    return render(request, 'community/post_form.html', context)


@login_required
def post_delete(request, slug):

    post = get_object_or_404(Post, slug=slug)
    
    if not can_delete_post(request.user, post):
        messages.error(request, "You don't have permission to delete this post.")
        return redirect('community:post_detail', slug=slug)
    
    if request.method == 'POST':
        post.delete()
        messages.success(request, "Post deleted successfully!")
        return redirect('community:dashboard')
    
    context = {'post': post}
    return render(request, 'community/post_confirm_delete.html', context)


@login_required
def my_posts(request):

    posts = Post.objects.filter(author=request.user).order_by('-created_at')
    
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {'page_obj': page_obj}
    return render(request, 'community/my_posts.html', context)


@login_required
@require_POST
def toggle_like(request, slug):
    """Toggle like on a post (AJAX)"""
    post = get_object_or_404(Post, slug=slug)
    like, created = Like.objects.get_or_create(post=post, user=request.user)
    
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    
    return JsonResponse({
        'liked': liked,
        'likes_count': post.likes.count()
    })


@login_required
@require_POST
def delete_comment(request, comment_id):

    comment = get_object_or_404(Comment, id=comment_id)
    
    if comment.author == request.user or request.user.is_superuser:
        post_slug = comment.post.slug
        comment.delete()
        messages.success(request, "Comment deleted successfully!")
        return redirect('community:post_detail', slug=post_slug)
    else:
        messages.error(request, "You don't have permission to delete this comment.")
        return redirect('community:post_detail', slug=comment.post.slug)


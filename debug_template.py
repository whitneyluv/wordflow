#!/usr/bin/env python3
import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/whitney/PycharmProjects/wordflow')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from wordflow.models import Comment, Post
from wordflow.templatetags.post_extras import comment_count

print('Testing template filter directly:')
for post in Post.objects.all()[:10]:
    direct_count = Comment.objects.filter(post=post).count()
    filter_count = comment_count(post)
    print(f'Post {post.id} ({post.postname[:30]}...):')
    print(f'  Direct query: {direct_count} comments')
    print(f'  Template filter: {filter_count} comments')
    print(f'  Match: {direct_count == filter_count}')
    print()

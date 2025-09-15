#!/usr/bin/env python3
import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/whitney/PycharmProjects/wordflow')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from wordflow.models import Comment, Post

print('Total comments in database:', Comment.objects.count())
print('Posts with comments:')
for post in Post.objects.all()[:10]:
    comment_count = Comment.objects.filter(post_id=post.id).count()
    print(f'Post {post.id} ({post.postname[:30]}...): {comment_count} comments')
    if comment_count > 0:
        comments = Comment.objects.filter(post_id=post.id)
        for comment in comments:
            print(f'  - {comment.user.username}: {comment.content[:50]}...')

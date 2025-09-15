#!/usr/bin/env python3
import os
import sys
import django

# Setup Django environment
sys.path.append('/Users/whitney/PycharmProjects/wordflow')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.template import Context, Template
from wordflow.models import Post, Comment

# Test template rendering directly
template_content = """
{% load post_extras %}
Post ID: {{ post.id }}
Post name: {{ post.postname }}
Comment count (filter): {{ post|comment_count }}
Comment count (direct): {{ comment_count_direct }}
"""

template = Template(template_content)

for post in Post.objects.all()[:5]:
    comment_count_direct = Comment.objects.filter(post=post).count()
    context = Context({
        'post': post,
        'comment_count_direct': comment_count_direct
    })
    
    result = template.render(context)
    print(f"--- Post {post.id} ---")
    print(result)
    print()

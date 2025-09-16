from django.core.management.base import BaseCommand
from wordflow.models import Post, Category


class Command(BaseCommand):
    help = 'Update existing posts to have proper category_obj assignments'

    def handle(self, *args, **options):
        posts_updated = 0
        posts_without_category = 0
        
        for post in Post.objects.all():
            if post.category and not post.category_obj:
                # Попытаться найти или создать категорию
                category, created = Category.objects.get_or_create(
                    name=post.category.strip()
                )
                post.category_obj = category
                post.save()
                posts_updated += 1
                
                if created:
                    self.stdout.write(
                        self.style.SUCCESS(f'Создана новая категория: {category.name}')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Обновлен пост "{post.postname}" с категорией "{category.name}"')
                )
            elif not post.category and not post.category_obj:
                posts_without_category += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Обновлено постов: {posts_updated}')
        )
        self.stdout.write(
            self.style.WARNING(f'Постов без категории: {posts_without_category}')
        )

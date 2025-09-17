from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from wordflow.models import Post, Comment

class Command(BaseCommand):
    help = 'Create user groups with appropriate permissions'

    def handle(self, *args, **options):
        editors_group, created = Group.objects.get_or_create(name='Редакторы')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Редакторы" создана'))
        else:
            self.stdout.write(self.style.WARNING('Группа "Редакторы" уже существует'))

        post_content_type = ContentType.objects.get_for_model(Post)
        comment_content_type = ContentType.objects.get_for_model(Comment)

        post_permissions = [
            'change_post',
            'view_post',
        ]

        comment_permissions = [
            'delete_comment',
            'view_comment',
            'change_comment',
        ]

        # Добавляем права к группе
        for perm_codename in post_permissions:
            try:
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type=post_content_type
                )
                editors_group.permissions.add(permission)
                self.stdout.write(f'Добавлено право: {perm_codename}')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Право {perm_codename} не найдено'))

        for perm_codename in comment_permissions:
            try:
                permission = Permission.objects.get(
                    codename=perm_codename,
                    content_type=comment_content_type
                )
                editors_group.permissions.add(permission)
                self.stdout.write(f'Добавлено право: {perm_codename}')
            except Permission.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Право {perm_codename} не найдено'))

        moderators_group, created = Group.objects.get_or_create(name='Модераторы')
        
        if created:
            self.stdout.write(self.style.SUCCESS('Группа "Модераторы" создана'))
        else:
            self.stdout.write(self.style.WARNING('Группа "Модераторы" уже существует'))

        all_post_permissions = Permission.objects.filter(content_type=post_content_type)
        all_comment_permissions = Permission.objects.filter(content_type=comment_content_type)
        
        for permission in all_post_permissions:
            moderators_group.permissions.add(permission)
            
        for permission in all_comment_permissions:
            moderators_group.permissions.add(permission)

        self.stdout.write(self.style.SUCCESS('Группы и права успешно настроены!'))
        self.stdout.write('Теперь вы можете назначать пользователей в группы через админку Django.')

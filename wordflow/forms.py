from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.contrib.auth.password_validation import validate_password
from .models import Post, Category
from ckeditor.widgets import CKEditorWidget
import re

class PostForm(forms.ModelForm):
    content = forms.CharField(
        label='Содержание',
        widget=CKEditorWidget(config_name='basic'),
        required=True  # Обязательное поле
    )
    
    category_choice = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Выберите категорию или создайте новую",
        required=False,
        label='Выбрать существующую категорию',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    new_category = forms.CharField(
        max_length=100,
        required=False,
        label='Или создать новую категорию',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название новой категории'})
    )
    
    class Meta:
        model = Post
        fields = ['postname', 'content', 'image']
        widgets = {
            'postname': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'image': forms.FileInput(attrs={'class': 'form-control', 'required': True}),
        }
        labels = {
            'postname': 'Заголовок',
            'image': 'Изображение',
        }
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        
        # Удаляем HTML теги из контента для проверки
        import re
        content_text = re.sub(r'<[^>]+>', '', content).strip()
        
        if not content_text:
            raise ValidationError('Пост должен содержать текст. Нельзя создавать посты с пустым содержанием.')
        
        return content
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        
        if not image:
            raise ValidationError('Пост должен содержать изображение. Нельзя создавать посты без фотографий.')
        
        return image
    
    def clean(self):
        cleaned_data = super().clean()
        category_choice = cleaned_data.get('category_choice')
        new_category = cleaned_data.get('new_category', '').strip()
        
        # Проверяем, что выбрана существующая категория или введена новая
        if not category_choice and not new_category:
            raise ValidationError('Выберите существующую категорию или создайте новую.')
        
        # Если введены и выбрана категория, и новая - приоритет новой
        if category_choice and new_category:
            cleaned_data['category_choice'] = None  # Очищаем выбор, используем новую
        
        return cleaned_data

class PostEditForm(forms.ModelForm):
    content = forms.CharField(
        label='Содержание',
        widget=CKEditorWidget(config_name='basic'),
        required=True
    )
    editors = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label='Редакторы'
    )
    
    category_choice = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        empty_label="Выберите категорию или создайте новую",
        required=False,
        label='Выбрать существующую категорию',
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    new_category = forms.CharField(
        max_length=100,
        required=False,
        label='Или создать новую категорию',
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Введите название новой категории'})
    )
    
    class Meta:
        model = Post
        fields = ['postname', 'content', 'image']
        widgets = {
            'postname': forms.TextInput(attrs={'class': 'form-control', 'required': True}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'postname': 'Заголовок',
            'image': 'Обновить изображение (необязательно)',
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Исключаем автора поста из списка редакторов
            self.fields['editors'].queryset = User.objects.exclude(id=user.id)
            
            # Если редактируем существующий пост, устанавливаем текущих редакторов
            if self.instance and self.instance.pk:
                self.fields['editors'].initial = self.instance.editors.all()
                # Устанавливаем текущую категорию поста
                if self.instance.category_obj:
                    self.fields['category_choice'].initial = self.instance.category_obj
    
    def clean_content(self):
        content = self.cleaned_data.get('content', '').strip()
        
        # Удаляем HTML теги из контента для проверки
        import re
        content_text = re.sub(r'<[^>]+>', '', content).strip()
        
        if not content_text:
            raise ValidationError('Пост должен содержать текст. Нельзя создавать посты с пустым содержанием.')
        
        return content
    
    def clean_image(self):
        image = self.cleaned_data.get('image')
        
        # Для редактирования: проверяем изображение только если его нет у существующего поста
        if not image and (not self.instance or not self.instance.image):
            raise ValidationError('Пост должен содержать изображение. Нельзя создавать посты без фотографий.')
        
        return image
    
    def clean(self):
        cleaned_data = super().clean()
        category_choice = cleaned_data.get('category_choice')
        new_category = cleaned_data.get('new_category', '').strip()
        
        # Проверяем, что выбрана существующая категория или введена новая
        if not category_choice and not new_category:
            raise ValidationError('Выберите существующую категорию или создайте новую.')
        
        # Если введены и выбрана категория, и новая - приоритет новой
        if category_choice and new_category:
            cleaned_data['category_choice'] = None  # Очищаем выбор, используем новую
        
        return cleaned_data

class CustomUserCreationForm(forms.ModelForm):
    email = forms.EmailField(
        required=True,
        label='Email адрес',
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    first_name = forms.CharField(
        max_length=30,
        required=True,
        label='Имя',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    last_name = forms.CharField(
        max_length=30,
        required=True,
        label='Фамилия',
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    password1 = forms.CharField(
        label='Пароль',
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text='Ваш пароль должен содержать как минимум 8 символов, не должен быть слишком простым или широко распространенным, и не должен состоять только из цифр.'
    )
    password2 = forms.CharField(
        label='Подтверждение пароля',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1', 'password2')
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'username': 'Имя пользователя',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email:
            # Проверка базового формата email
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, email):
                raise ValidationError('Пожалуйста, укажите правильный email адрес (например: example@gmail.com)')
            
            # Список разрешенных доменов
            allowed_domains = [
                'gmail.com', 'mail.ru', 'yandex.ru', 'yandex.com', 'yahoo.com',
                'outlook.com', 'hotmail.com', 'rambler.ru', 'list.ru', 'bk.ru',
                'inbox.ru', 'ya.ru', 'icloud.com', 'protonmail.com'
            ]
            
            domain = email.split('@')[-1].lower()
            if domain not in allowed_domains:
                raise ValidationError(
                    f'Используйте email с одним из разрешенных доменов: {", ".join(allowed_domains)}'
                )
            
            # Проверка на существование email
            if User.objects.filter(email=email).exists():
                raise ValidationError('Пользователь с таким email уже существует.')
        
        return email

    def clean_password1(self):
        password1 = self.cleaned_data.get('password1')
        if password1:
            errors = []
            
            # Проверка длины
            if len(password1) < 8:
                errors.append('Пароль слишком короткий. Он должен содержать как минимум 8 символов.')
            
            # Проверка на только цифры
            if password1.isdigit():
                errors.append('Пароль не может состоять только из цифр.')
            
            # Проверка на только буквы
            if password1.isalpha():
                errors.append('Пароль не может состоять только из букв.')
            
            # Проверка разнообразия символов
            has_upper = any(c.isupper() for c in password1)
            has_lower = any(c.islower() for c in password1)
            has_digit = any(c.isdigit() for c in password1)
            has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in password1)
            
            char_types = sum([has_upper, has_lower, has_digit, has_special])
            if char_types < 3:
                errors.append('Пароль должен содержать минимум 3 типа символов: заглавные буквы, строчные буквы, цифры и специальные символы.')
            
            # Проверка на повторяющиеся символы
            if len(set(password1)) < 4:
                errors.append('Пароль содержит слишком мало уникальных символов.')
            
            # Проверка на последовательности
            sequences = ['123456', '654321', 'abcdef', 'fedcba', 'qwerty', 'asdfgh', 'zxcvbn']
            for seq in sequences:
                if seq in password1.lower():
                    errors.append('Пароль содержит простые последовательности символов.')
                    break
            
            # Проверка на повторяющиеся паттерны
            for i in range(len(password1) - 2):
                pattern = password1[i:i+3]
                if password1.count(pattern) > 1:
                    errors.append('Пароль содержит повторяющиеся паттерны.')
                    break

            common_passwords = [
                '12345678', '87654321', '123456789', '987654321', '1234567890',
                '11111111', '22222222', '33333333', '44444444', '55555555',
                '66666666', '77777777', '88888888', '99999999', '00000000',
                '123123', '111111', '222222', '333333', '444444', '555555',
                '666666', '777777', '888888', '999999', '000000', '121212',
                '131313', '141414', '151515', '161616', '171717', '181818',
                '191919', '202020', '212121', '232323', '242424', '252525',
                '262626', '272727', '282828', '292929', '303030',

                'password', 'password1', 'password123', 'pass', 'pass123',
                'qwerty', 'qwerty123', 'qwertyui', 'qwertyuiop', 'asdfgh',
                'asdfghjk', 'asdfghjkl', 'zxcvbn', 'zxcvbnm', 'admin',
                'administrator', 'root', 'user', 'guest', 'test', 'demo',
                'welcome', 'login', 'master', 'super', 'secret', 'default',
                'computer', 'internet', 'windows', 'microsoft', 'google',
                'facebook', 'twitter', 'instagram', 'youtube', 'apple', 'qwerty12'

                'пароль', 'парольпароль', 'пароль123', 'йцукен', 'йцукенг',
                'фывапр', 'фывапролд', 'ячсмить', 'ячсмитьбю', 'админ',
                'администратор', 'пользователь', 'гость', 'тест', 'демо',
                'добро пожаловать', 'вход', 'мастер', 'супер', 'секрет',
                'компьютер', 'интернет', 'виндовс', 'майкрософт', 'гугл',

                '19900101', '19910101', '19920101', '19930101', '19940101',
                '19950101', '19960101', '19970101', '19980101', '19990101',
                '20000101', '20010101', '20020101', '20030101', '20040101',
                '20050101', '20060101', '20070101', '20080101', '20090101',
                '20100101', '20110101', '20120101', '20130101', '20140101',
                '20150101', '20160101', '20170101', '20180101', '20190101',
                '20200101', '20210101', '20220101', '20230101', '20240101',
                '01011990', '01011991', '01011992', '01011993', '01011994',
                '01011995', '01011996', '01011997', '01011998', '01011999',
                '01012000', '01012001', '01012002', '01012003', '01012004',
                '01012005', '01012006', '01012007', '01012008', '01012009',
                '01012010', '01012011', '01012012', '01012013', '01012014',
                '01012015', '01012016', '01012017', '01012018', '01012019',
                '01012020', '01012021', '01012022', '01012023', '01012024',

                'alexander', 'alexandra', 'andrew', 'anna', 'anton', 'maria',
                'michael', 'natasha', 'nikolai', 'olga', 'pavel', 'sergey',
                'tatiana', 'vladimir', 'александр', 'александра', 'андрей',
                'анна', 'антон', 'мария', 'михаил', 'наташа', 'николай',
                'ольга', 'павел', 'сергей', 'татьяна', 'владимир',

                'football', 'basketball', 'soccer', 'tennis', 'hockey',
                'baseball', 'volleyball', 'golf', 'swimming', 'running',
                'nike', 'adidas', 'puma', 'reebok', 'converse', 'vans',
                'coca-cola', 'pepsi', 'mcdonalds', 'kfc', 'burger',

                'abc123', 'abc12345', 'abcd1234', 'abcdef', 'abcdefg',
                'abcdefgh', 'abcdefghi', 'qwe123', 'asd123', 'zxc123',
                'qaz123', 'wsx123', 'edc123', 'rfv123', 'tgb123',
                'yhn123', 'ujm123', 'ik123', 'ol123', 'p123',

                'qwertyuiop', 'asdfghjkl', 'zxcvbnm', 'qazwsx', 'wsxedc',
                'edcrfv', 'rfvtgb', 'tgbyhn', 'yhnujm', 'ujmik',
                'ikol', 'olp', 'plokij', 'okijnuhb', 'uhbygv',
                'ygvtfc', 'tgcrdx', 'rdxesz', 'eszwaq',

                'january', 'february', 'march', 'april', 'may', 'june',
                'july', 'august', 'september', 'october', 'november', 'december',
                'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday',
                'январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
                'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь',
                'понедельник', 'вторник', 'среда', 'четверг', 'пятница', 'суббота', 'воскресенье'
            ]
            if password1.lower() in common_passwords:
                errors.append('Введённый пароль слишком широко распространён.')

            # Дополнительная проверка через Django валидаторы
            try:
                validate_password(password1, self.instance)
            except ValidationError as error:
                for err in error.messages:
                    if 'too common' in err.lower() and 'Введённый пароль слишком широко распространён.' not in errors:
                        errors.append('Введённый пароль слишком широко распространён.')
                    elif 'similar' in err.lower():
                        errors.append('Пароль слишком похож на другую вашу личную информацию.')
            
            if errors:
                raise ValidationError(errors)
                
        return password1

    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('Пароли не совпадают.')
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.set_password(self.cleaned_data['password1'])
        user.is_active = True  # Пользователь сразу активен
        if commit:
            user.save()
        return user

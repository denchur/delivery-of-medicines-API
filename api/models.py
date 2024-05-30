import random

from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator, MinValueValidator
from django.db import models

PENDING = 'В ожидании'
PROCESSING = 'В обработке'
COMPLETED = 'Выполнен'
ORDER_STATUS_CHOICES = [
    (PENDING, 'В ожидании'),
    (PROCESSING, 'В обработке'),
    (COMPLETED, 'Выполнен'),
]

class SupportedСities(models.Model):
    '''Таблица городов в которых работает доставка'''
    name=models.CharField(max_length=50)

    def __str__(self):
        return self.name

class SupportedPharmacy(models.Model):
    '''Таблица аптек в которых работает доставка'''
    name=models.CharField(max_length=50)
    in_the_city = models.ForeignKey(SupportedСities, related_name='pharmacies', on_delete=models.CASCADE)
    address = models.CharField(max_length=150,)

    def __str__(self):
        return self.name

class Curier(AbstractUser):
    '''
        Таблица Курьер
    '''
    work_in_city = models.ForeignKey(SupportedСities, related_name='users', on_delete=models.CASCADE, default=1)
    accepted = models.BooleanField(default=False)
    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Никнейм',
        validators=[
            RegexValidator(
                regex=r'^[\w.@+-]+$',
                message='Некорректные символы в юзернейме.'
            ),
            RegexValidator(
                regex=r'^(?i)(?!me$).*',
                message='Запрещенное значение для юзернейма.'
            ),
        ]
    )
    mobile_phone = models.CharField(
        max_length=11,
        unique=True,
        verbose_name='Телефон',
        validators=[RegexValidator(r'^\d{11}$', 'Введите только цифры (11 символов).')]
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        verbose_name='Почта',
    )
    first_name = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name='Имя',
    )
    last_name = models.CharField(
        max_length=150,
        blank=False,
        null=False,
        verbose_name='Фамилия',
    )
    father_name = models.CharField(
        max_length=150,
        null=True,
        blank=True,
        verbose_name='Отчество',
    )
    

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Medication(models.Model):
    ''' 
    Медикаменты
    '''
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Order(models.Model):
    from_the_pharmacy = models.ForeignKey(SupportedPharmacy, related_name='orders_from_the_pharmacy', on_delete=models.CASCADE)
    address_pacient = models.CharField(max_length=100)
    curier = models.ForeignKey(Curier, on_delete=models.SET_NULL, related_name='orders', null=True, blank = True)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default=PENDING, verbose_name='Статус')
    recipients_name = models.CharField(
        max_length=50,
        validators=[RegexValidator(
            r'^[а-яА-Яa-zA-Z]+$', 'Введите только буквы.')])
    recipients_snils = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^\d{11}$', 'Введите только цифры (11 символов).')]
        )
    recipients_phone = models.CharField(
        max_length=11,
        validators=[RegexValidator(r'^\d{11}$', 'Введите только цифры (11 символов).')]
    )
    medication = models.ManyToManyField(Medication, through='MedicamentsInOrders')
    created = models.DateTimeField(auto_now_add=True)
    accepted_kod = models.SmallIntegerField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.accepted_kod:
            self.accepted_kod = random.randint(1000, 9999)  # Генерация случайного 4-значного числа
        super().save(*args, **kwargs)

    def __str__(self):
        return f'N{self.id} откуда {self.from_the_pharmacy} куда {self.address_pacient}'

class MedicamentsInOrders(models.Model):
    medicament = models.ForeignKey(Medication, related_name='in_orders', on_delete=models.CASCADE)
    order =  models.ForeignKey(Order, related_name='medical_orders', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()

    def __str__(self):
        return f'{self.medicament} в заказе {self.order}'

class RefuceOrdersCurier(models.Model):
    curier = models.ForeignKey(Curier, on_delete=models.CASCADE, related_name='refuces')
    orders = models.ForeignKey(Order, related_name='refuces',on_delete= models.CASCADE)

    def __ste__(self):
        return f'{self.curier} отказался от {self.orders}'
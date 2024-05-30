from django.contrib.auth import get_user_model
from djoser.serializers import UserCreateSerializer, UserSerializer
from rest_framework import serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import *

User = get_user_model()

class SupportedPharmacySerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportedPharmacy
        fields = ('name','address')

class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = (
            'work_in_city',
            'email',
            'username',
            'password',
            'first_name',
            'last_name',
            'father_name',
            'mobile_phone'
        )

    def validate_username(self, username):
        if username == r'^(?i)(?!me$).*':
            raise ValidationError(
                {'username': 'Запрещенное значение для юзернейма.'},
                code=status.HTTP_400_BAD_REQUEST
            )
        return username

class CourierShortSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('first_name','last_name','father_name','mobile_phone')


class MedicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Medication
        fields = ('id', 'name')

class CustomUserSerializer(UserSerializer):
    count_geted_orders = serializers.SerializerMethodField()
    count_ready_orders = serializers.SerializerMethodField()
    count_refuce_orders = serializers.SerializerMethodField()
    work_in_city = serializers.StringRelatedField(read_only=True)
    class Meta:
        model = User
        fields = (
            'work_in_city',
            'email',
            'username',
            'first_name',
            'last_name',
            'father_name',
            'mobile_phone',
            'count_geted_orders',
            'count_ready_orders',
            'count_refuce_orders',
        ) 

    def get_count_geted_orders(self, obj):
        return obj.orders.count()
    
    def get_count_ready_orders(self, obj):
        return obj.orders.filter(status='Выполнен').count()

    def get_count_refuce_orders(self, obj):
        return RefuceOrdersCurier.objects.filter(curier=obj).count()

class ShortListOrderSerializer(serializers.ModelSerializer):
    from_the_pharmacy = SupportedPharmacySerializer(read_only=True)
    class Meta:
        model = Order
        fields = ('id','from_the_pharmacy','address_pacient','created')

class DetailOrderSerializer(serializers.ModelSerializer):
    from_the_pharmacy = SupportedPharmacySerializer()
    class Meta:
        model = Order
        fields = ('id','from_the_pharmacy','address_pacient','created')


class MedicationInOrderSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
    )
    quantity = serializers.IntegerField(source='in_orders.quantity')
    class Meta:
        model = MedicamentsInOrders
        fields = ('name','quantity')

class TestSerializer(serializers.ModelSerializer):
    name = serializers.CharField(
        read_only=True,
        source='medicament.name'
    )
    class Meta:
        model = MedicamentsInOrders
        fields = ('name','quantity')

class TestListSerializer(serializers.ModelSerializer):
    from_the_pharmacy = SupportedPharmacySerializer(read_only=True)
    medication = TestSerializer(
        many=True,
        source = 'medical_orders'
    )
    class Meta:
        model = Order
        fields = ('id','from_the_pharmacy','address_pacient','status','recipients_name','recipients_snils','recipients_phone','medication','created')

class ListOrderSerializer(serializers.ModelSerializer):
    from_the_pharmacy = SupportedPharmacySerializer(read_only=True)
    medication = serializers.StringRelatedField(many=True)
    class Meta:
        model = Order
        fields = ('id','from_the_pharmacy','address_pacient','status','recipients_name','recipients_snils','recipients_phone','medication','created')

class AddOrderSerializer(serializers.ModelSerializer):
    medication = MedicationInOrderSerializer(many=True)
    class Meta:
        model = Order
        fields = ('id','from_the_pharmacy','address_pacient',
                  'recipients_name','recipients_snils','recipients_phone',
                  'medication',)
    
    def create(self, validated_data):
        medication_in_order = validated_data.pop('medication')
        order = Order.objects.create(**validated_data)
        for med in medication_in_order:
            medication_name = med['name']
            medication, _= Medication.objects.get_or_create(name=medication_name)
            print(med)
            quantity = med['in_orders']['quantity']
            MedicamentsInOrders.objects.create(medicament=medication , order=order, quantity=quantity)
        return order
    
    def update(self, instance,validated_data):
        order = instance
        instance.medication.clear()
        new_medication_in_order = validated_data.pop('medication')
        for med in new_medication_in_order:
            medication_name = med['name']
            medication, _= Medication.objects.get_or_create(name=medication_name)
            MedicamentsInOrders.objects.create(medicament=medication , order=order, quantity=med['in_orders']['quantity'])
        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return TestListSerializer(
            self.instance,
            context={'request': self.context.get('request')}
        ).data
    

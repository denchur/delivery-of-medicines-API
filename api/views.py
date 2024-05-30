from django.shortcuts import render
from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from .serializers import *
# Create your views here.
class OrdersViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = TestListSerializer
    permission_classes = [IsAuthenticated,]
    
    def get_queryset(self):
        pharmacies = SupportedPharmacy.objects.filter(in_the_city=self.request.user.work_in_city)
        if self.action == 'list':
            return Order.objects.filter(Q(curier=None) & Q(from_the_pharmacy__in=pharmacies) & ~Q(refuces__curier=self.request.user) )
        elif self.action == 'retrieve':
            return Order.objects.all()
        else:
            return super().get_queryset()
    
    def get_serializer_class(self):
        if self.action in ('retrieve', 'list'):
            return TestListSerializer
        return AddOrderSerializer
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.curier != self.request.user:
            return Response({'error':'Вы не являетесь курьером этого заказа'}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def my_finish_orders(self, request):
        orders = Order.objects.filter(curier=request.user) & Order.objects.filter(status__in=['Выполнен',])
        if orders.count() == 0:
            return Response({'action':'У вас завершенных заказов'},status=status.HTTP_400_BAD_REQUEST)
        serializer = TestListSerializer(data=orders, many=True, context={'request': request})
        serializer.is_valid()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    @action(
        detail=False,
        permission_classes=[IsAuthenticated],
    )
    def my_orders(self, request):
        orders = Order.objects.filter(curier=request.user) & Order.objects.filter(status__in=['В ожидании','В обработке'])
        if orders.count() == 0:
            return Response({'action':'У вас ней действующих заказов'},status=status.HTTP_400_BAD_REQUEST)
        serializer = TestListSerializer(data=orders, many=True, context={'request': request})
        serializer.is_valid()
        return Response(
            serializer.data,
            status=status.HTTP_200_OK
        )
    
    @action(
        detail = True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def take_order(self, request, pk):
        pharmacies = SupportedPharmacy.objects.filter(in_the_city=self.request.user.work_in_city)
        order = Order.objects.filter(id = pk).first()
        Order.objects.filter(curier=None) & Order.objects.filter(from_the_pharmacy__in=pharmacies)
        if order.from_the_pharmacy.in_the_city != self.request.user.work_in_city:
            return Response({'action':'Вы не можете взять заказ в другом городе'}, status=status.HTTP_400_BAD_REQUEST)
        if order.curier == None:
            order.curier = request.user
            order.save()
            return Response({'action':'Заказ успешно взят'},status=status.HTTP_200_OK)
        return Response({'action':'Этот заказ уже взят'}, status=status.HTTP_400_BAD_REQUEST)

    @action(
        detail = True,
        methods=['post'],
        permission_classes=[IsAuthenticated],
    )
    def refuce_order(self, request, pk):
        order = Order.objects.filter(id = pk).first()
        if order.status == 'В обработке':
            return Response({'action':'Нельзя отказаться от заказа который у вас на руках '}, status=status.HTTP_400_BAD_REQUEST)
        if order.status == 'Выполнен':
            return Response({'action':'Нельзя отказаться от заказа который уже выполнен'}, status=status.HTTP_400_BAD_REQUEST)
        if order.curier == request.user:
            order.curier = None
            order.save()
            return Response({'action':'Вы отказались от выполнения заказа'},status=status.HTTP_200_OK)
        if order.curier == None:
            RefuceOrdersCurier.objects.create(orders=order, curier=request.user)
            return Response({'action':'Вы отказались брать заказ'}, status=status.HTTP_200_OK)
    @action(
        detail = True,
        methods =['post'],
        permission_classes=[IsAuthenticated],
    )
    def pickup_pharmacy(self, request, pk):
        order = Order.objects.filter(id = pk).first()
        if order.curier != request.user:
            return Response(
                {'action':'Этот заказ взят не вами'}, status=status.HTTP_400_BAD_REQUEST)
        if order.status == 'В обработке' or order.status == 'Выполнен':
            return Response({'action':'Вы уже забирали этот заказ'}, status=status.HTTP_400_BAD_REQUEST)
        order.status = 'В обработке'
        order.save()
        return Response({'action':'Забрали заказ из аптеки'}, status = status.HTTP_200_OK)

    @action(
        detail = True,
        methods =['post'],
        permission_classes=[IsAuthenticated],
    )
    def give_to_the_recipient(self, request, pk):
        acceptCode = request.data.get('acceptCode')
        order = Order.objects.filter(id = pk).first()
        if order.curier != request.user:
            return Response(
                {'action':'Этот заказ взят не вами'}, status = status.HTTP_400_BAD_REQUEST
            )
        if order.status == 'В ожидании':
            return Response({'action':'Для начала следует забрать заказ из аптеки'}, status=status.HTTP_400_BAD_REQUEST)
        if (acceptCode == order.accepted_kod): 
            order.status = 'Выполнен'
            order.save()
            return Response({'action':'Код подтвержден'}, status = status.HTTP_200_OK)
        else:
            return Response({'action':'Код неверный'}, status = status.HTTP_400_BAD_REQUEST)

'''    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'retrieve':
            return OrderDetailSerializer
        else:
            return OrderSerializer
'''

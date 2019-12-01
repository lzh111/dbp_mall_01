from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.paginator import Paginator
from django.http import HttpResponse
from datetime import date, datetime
from django.shortcuts import render
from django.views import View
from django_redis import get_redis_connection
import json
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from decimal import Decimal
from rest_framework.generics import CreateAPIView

from goods.models import SKU
from .models import OrderInfo
from . import  constants
# Create your views here.
from .serializers import OrderSettlementSerializer, SaveOrderSerializer
from decimal import Decimal
from datetime import date, datetime

def json_serial(obj):
    """JSON serializer for objects not serializable by default json code"""

    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    raise TypeError ("Type %s not serializable" % type(obj))

def default(obj):

    if isinstance(obj, Decimal):

        return str(obj)

    raise TypeError("Object of type '%s' is not JSON serializable" % type(obj).__name__)
import django.http
class OrderSettlementView(APIView):
    """
    订单结算
    """
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        """
        获取
        """
        user = request.user

        # 从购物车中获取用户勾选要结算的商品信息
        redis_conn = get_redis_connection('cart')
        redis_cart_dict = redis_conn.hgetall('cart_%s' % user.id)
        redis_cart_selected = redis_conn.smembers('cart_selected_%s' % user.id)

        cart = {}
        for sku_id in redis_cart_selected:
            cart[int(sku_id)] = int(redis_cart_dict[sku_id])

        # 查询商品信息
        skus = SKU.objects.filter(id__in=cart.keys())
        for sku in skus:
            sku.count = cart[sku.id]
            sku.selected = True

        # 运费
        freight = Decimal('10.00')

        serializer = OrderSettlementSerializer({'freight': freight, 'skus': skus})
        return Response(serializer.data)


class SaveOrderView(CreateAPIView):
    """保存订单"""
    serializer_class = SaveOrderSerializer
    permission_classes = [IsAuthenticated]


class OrderListView(APIView):
    """订单列表信息获取"""


    def get(self, request):
        """查询订单列表信息"""

        # 获取当前用户对象
        user = request.user


        """获取当前用户的订单信息"""
        # 获取当前商品订单号
        user_orders = user.orderinfo_set.all()

        # 订单号、支付方式、订单金额 列表
        user_orders_list = []




        for user_order in user_orders:

            if user_order.pay_method == 1:
                pay_method = '货到付款'
            elif user_order.pay_method == 2:
                pay_method = '支付宝'
            else:
                pass
            create_time = json.dumps(user_order.create_time, default=json_serial)
            user_order_dict = {
                'order_id': user_order.order_id,  # 订单号
                'pay_method': pay_method,  # 支付方式
                'total_amount': user_order.total_amount,  # 订单金额
                'total_count': user_order.total_count,  # 商品数量
                'create_time':create_time,  # 订单创建时间
                'freight':user_order.freight,  # 运费
                'status':user_order.status,
            }
            user_orders_list.append(user_order_dict)


            # 当前订单对应的订单商品
            user_order_goods = user_order.skus.all()
            # print('订单对应的订单商品')
            # print(user_order_goods)


            for user_order_sku in user_order_goods:

                sku = user_order_sku.sku
                if user_order_sku.order_id == user_order.order_id:

                    user_order_dict['name'] = sku.name
                    user_order_dict['price'] = sku.price
                    user_order_dict['defult_image'] = sku.default_image
            user_orders_list.append(user_order_dict)

        print(user_orders_list)

        # return Response(data=user_orders_list)
        return HttpResponse(json.dumps(user_orders_list,default=default),content_type="application/json,charset=utf-8")


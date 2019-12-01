from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'orders/settlement/$', views.OrderSettlementView.as_view()),
    url(r'orders/$', views.SaveOrderView.as_view()),
    # 查询订单列表信息
    url(r'^orderslist/$', views.OrderListView.as_view()),

]

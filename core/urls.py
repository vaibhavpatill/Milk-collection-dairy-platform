
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('producer/register/', views.register_producer, name='register_producer'),
    path('milk/collect/', views.collect_milk, name='milk_collect'),
    path('rates/manage/', views.manage_rates, name='manage_rates'),
    path('billing/summary/', views.billing_summary, name='billing_summary'),
    path('reports/history/', views.collection_history, name='collection_history'),
    path('get_rate/', views.get_rate, name='get_rate'),
    path('milk/edit/<int:collection_id>/', views.edit_collection, name='edit_collection'),
    path('milk/delete/<int:collection_id>/', views.delete_collection, name='delete_collection'),
    path('milk/deductions/<int:producer_id>/', views.save_deductions, name='save_deductions'),
    path('manage/deductions/', views.manage_deductions, name='manage_deductions'),
    path('deduction/edit/<int:deduction_id>/', views.edit_deduction, name='edit_deduction'),
    path('deduction/delete/<int:deduction_id>/', views.delete_deduction, name='delete_deduction'),
]

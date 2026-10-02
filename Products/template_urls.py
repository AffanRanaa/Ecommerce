from django.urls import path

from .template_views import  product_list_page,product_detail_page, product_add_page,product_edit_page


urlpatterns = [
    path('',product_list_page,name='product-list-page'),
    path('products/', product_list_page, name='products-page'),
    path('products/<int:pk>/',product_detail_page,name='product-detail-page'),
    path( 'products/add/', product_add_page, name='product-add-page'),
    path('products/<int:pk>/edit/', product_edit_page, name='product-edit-page'),]
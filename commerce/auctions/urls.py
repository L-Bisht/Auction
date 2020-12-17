from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("login", views.login_view, name="login"),
    path("logout", views.logout_view, name="logout"),
    path("register", views.register, name="register"),
    path("create/", views.create, name="create_listing"),
    path("list/<int:id>", views.item, name="item"),
    path("watchlist/", views.watchlist, name="watchlist"),
    path("additem/<int:id>", views.add_item, name="add_item"),
    path("removeitem/<int:id>", views.remove_item, name="remove_item"),
    path("close/<int:id>", views.close, name="close_auction"),
    path("bid/<int:id>", views.bid, name="bid"),
    path("comment/<int:id>", views.comment, name="comment"),
    path("categories", views.categories, name="categories"),
    path("category/<str:name>", views.category, name="category")
]

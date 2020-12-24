from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.deletion import CASCADE, SET_NULL
from django.db.models.lookups import IsNull


# Model for users
class User(AbstractUser, models.Model):
    pass

# Model for listing categories
class Category(models.Model):
    type = models.CharField(max_length=64)
    
    def __str__(self):
        return f"{ self.type }"

# Model for auction listing
class AuctionListing(models.Model):
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=256)
    image_url = models.URLField(max_length=256, blank=True)
    starting_bid = models.IntegerField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE,
                                 related_name="category")
    is_active = models.BooleanField(default=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE,
                              related_name="owner")
    winner = models.ForeignKey(User, blank=True, null=True, on_delete=SET_NULL,
                                related_name="victor")
    def __str__(self):
        return f"{ self.title } with following details {self.description} created by {self.owner} with starting bid{self.starting_bid}"

# Model for bids
class Bid(models.Model):
    highest = models.IntegerField()
    bidder = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name="bidder")
    item = models.ForeignKey(AuctionListing, on_delete=CASCADE,
                             related_name="item")

# Model for comments
class Comment(models.Model):
    commenter = models.ForeignKey(User, on_delete=CASCADE,
                                  related_name="commenter")
    item = models.ForeignKey(AuctionListing, on_delete=CASCADE,
                             related_name="post")
    comment = models.CharField(max_length=256)

# Model for watchlist
class WatchList(models.Model):
    user = models.ForeignKey(User, on_delete=CASCADE,
                              related_name="viewer")
    item = models.ForeignKey(AuctionListing, on_delete=CASCADE,
                              related_name="viewing")
    def __str__(self):
        return f"{self.user} {self.item}"
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import Category, User, AuctionListing, Bid, Comment, WatchList


def index(request):
    print("Inside index:")
    return render(request, "auctions/index.html", {
        "items" : AuctionListing.objects.filter(is_active=True)
    })

def all(request):
    return render(request, "auctions/all.html", {
        "items" : AuctionListing.objects.all()
    })

# Create new Listing
@login_required
def create(request):
    print("Inside create:")
    if request.method == "POST":
        title = request.POST["title"]
        description = request.POST["description"]
        bid = request.POST["bid"]

        if not title:
            messages.warning(request, 'Title is required')
        elif not description:
            messages.warning(request, 'Description is required')
        elif not bid:
            messages.warning(request, 'Bid is required')
        else:
            category = request.POST["category"]
            img_url = request.POST["imgurl"]
            item = AuctionListing(owner=request.user ,title=title, description=description, starting_bid=bid,
                              image_url=img_url, category=Category.objects.get(type=category), is_active=True)
            item.save()
            messages.success(request, 'Item added successfully')
        return HttpResponseRedirect(reverse("index"))
    else:
        categories = Category.objects.all()
        return render(request, "auctions/create.html", {
            "categories" : categories
        })


def login_view(request):
    print("Inside login_view")
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            messages.success(request, 'Logged in Successfully')
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

@login_required
def logout_view(request):
    print("Inside logout")
    logout(request)
    messages.success(request, 'Logged out successfully')
    return HttpResponseRedirect(reverse("index"))


def register(request):
    print("Inside register")
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

# Fetch the selected listing if it exist
def item(request, id):
    print("Inside item")
    details = AuctionListing.objects.get(pk=id)
    highest_bid = None
    try:
        bid = Bid.objects.filter(item=details).values('highest')
        if len(bid) == 0:
            highest_bid = 0
        else:
            highest_bid = bid[0]['highest']
    except Bid.DoesNotExist:
        highest_bid = 0
    owner = False
    watchlist = True
    if request.user.is_authenticated:
        # Check if current user is the owner
        if details.owner == request.user:
            owner = True
        # If current user is not owner then check user's wishlist for current item
        else:
            try:
                WatchList.objects.get(user=request.user, item=details)
            except WatchList.DoesNotExist:
                watchlist = False

    return render(request, "auctions/listing.html", {
        "details" : details,
        "highest" : highest_bid,
        "owner" : owner,
        "inwatchlist" : watchlist,
        "comments" : Comment.objects.filter(item=details),
        "min_bid" : highest_bid + 1
    })

# To place bids
@login_required
def bid(request, id):
    if request.method == "POST":
        bid = int(request.POST["bid"])
        try:
            current = Bid.objects.get(item=AuctionListing.objects.get(pk=id))
        except Bid.DoesNotExist:
            current = Bid(item=AuctionListing.objects.get(pk=id), highest=bid, bidder=request.user)

        # Record the bid if its higher than current bid
        if bid < current.highest:
            messages.warning(request, 'Invalid bid')
        else:
            messages.success(request, 'Bid placed successfully')
            current.highest = bid
            current.save()
        return HttpResponseRedirect(reverse("item", kwargs={'id':id}))
    else:
        HttpResponse("Invalid Request")

# To fetch watchlist
@login_required
def watchlist(request):
    print("Inside Watchlist")
    isempty = False
    mylist = None
    try:
        mylist = WatchList.objects.filter(user=request.user)
        if len(mylist) == 0:
            isempty = True
    except WatchList.DoesNotExist:
        isempty = True
    return render(request, "auctions/watchlist.html", {
        "watchlist" : mylist,
        "isempty" : isempty
    })

# To add item to watchlist
@login_required
def add_item(request, id):
    print("Inside Add item")
    try:
        WatchList.objects.get(user=request.user, item=AuctionListing.objects.get(pk=id))
    except WatchList.DoesNotExist:
        listitem = WatchList(user=request.user, item=AuctionListing.objects.get(pk=id))
        listitem.save()
        messages.success(request, 'Item added to watchlist')
    return HttpResponseRedirect(reverse('item', kwargs={'id':id}))

# To remove item from watchlist
@login_required
def remove_item(request, id):
    print("Inside Remove item")
    try:
        WatchList.objects.get(user=request.user, item=AuctionListing.objects.get(pk=id)).delete()
        messages.success(request, 'Item removed from watchlist')
    except WatchList.DoesNotExist:
        messages.warning(request, 'Item does not exist')
    return HttpResponseRedirect(reverse('item', kwargs={'id':id}))

# To close the auction
@login_required
def close(request, id):
    print("Inside close")
    details = AuctionListing.objects.get(pk=id)
    print(details)
    # To Prevent non owner from closing the auction
    if not (details.owner == request.user):
        return HttpResponse("You are not authorized to view this page")
    else:
        print("Inside else")
        print(Bid.objects.filter(item=details).values('bidder'))
        details.is_active = False
        try:
            details.winner = User.objects.get(pk=Bid.objects.filter(item=details).values('bidder')[0]['bidder'])
            messages.success(request, 'Auction closed successfully')
        except IndexError:
            messages.warning(request, 'Auction closed without any bids')
        details.save()
        return HttpResponseRedirect(reverse('item', kwargs={'id': id}))

# To comment on the item
@login_required
def comment(request, id):
    if request.method == "POST":
        comment = request.POST["comment"]
        # To prevent Empty comments
        if not comment:
            messages.error(request, 'Empty Comment not allowed')
        elif len(comment) > 256:
            messages.error(request, 'Max length exceeded')
        else:
            obj = Comment(commenter=request.user, item=AuctionListing.objects.get(pk=id), comment=comment)
            obj.save()
        return HttpResponseRedirect(reverse('item', kwargs={'id': id}))

# To fetch all the categories
def categories(request):
    return render(request, "auctions/categories.html",{
        "categories" : Category.objects.all().order_by('type')
    })

# List all the item in that category
def category(request, name):
    return render(request, "auctions/category.html", {
        "items" : AuctionListing.objects.filter(category=Category.objects.get(type=name)),
        "name" : name
    })
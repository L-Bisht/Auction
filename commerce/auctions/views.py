from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from .models import Category, User, AuctionListing, Bid, Comment, WatchList


def index(request):
    print("Inside index:")
    return render(request, "auctions/index.html", {
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
        if (not title) or (not description) or (not bid):
            return HttpResponseRedirect("Title, bid and description are mandatory")
        category = request.POST["category"]
        img_url = request.POST["imgurl"]
        item = AuctionListing(owner=request.user ,title=title, description=description, starting_bid=bid,
                              image_url=img_url, category=Category.objects.get(type=category), is_active=True)
        item.save()
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
        "comments" : Comment.objects.filter(item=details)
    })


@login_required
def bid(request, id):
    if request.method == "POST":
        bid = int(request.POST["bid"])
        try:
            current = Bid.objects.get(item=AuctionListing.objects.get(pk=id))
        except Bid.DoesNotExist:
            current = Bid(item=AuctionListing.objects.get(pk=id), highest=bid, bidder=request.user)

        if bid < current.highest:
            return HttpResponse('Invalid Bid')
        current.highest = bid
        current.save()
        return HttpResponseRedirect(reverse("item", kwargs={'id':id}))
    else:
        HttpResponse("Invalid Request")


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

@login_required
def add_item(request, id):
    print("Inside Add item")
    try:
        WatchList.objects.get(user=request.user, item=AuctionListing.objects.get(pk=id))
    except WatchList.DoesNotExist:
        listitem = WatchList(user=request.user, item=AuctionListing.objects.get(pk=id))
        listitem.save()
    return HttpResponseRedirect(reverse('watchlist'))

@login_required
def remove_item(request, id):
    print("Inside Remove item")
    try:
        WatchList.objects.get(user=request.user, item=AuctionListing.objects.get(pk=id)).delete()
    except WatchList.DoesNotExist:
        return HttpResponse("Item does not exist")
    return HttpResponseRedirect(reverse('watchlist'))


@login_required
def close(request, id):
    details = AuctionListing.objects.get(pk=id)
    # To Prevent non owner from closing the auction
    if not (details.owner == request.user):
        return HttpResponse("You are not authorized to view this page")
    else:
        details.is_active = False
        details.winner = User.objects.get(pk=Bid.objects.filter(item=details).values('bidder')[0]['bidder'])
        details.save()
        return HttpResponseRedirect(reverse('index'))

@login_required
def comment(request, id):
    if request.method == "POST":
        comment = request.POST["comment"]
        # To prevent Empty comments
        if not comment:
            return HttpResponse("Add Comment....")
        elif len(comment) > 256:
            return HttpResponse("Word limit exceeded")
        obj = Comment(commenter=request.user, item=AuctionListing.objects.get(pk=id), comment=comment)
        obj.save()
        return HttpResponseRedirect(reverse('index'))

def categories(request):
    return render(request, "auctions/categories.html",{
        "categories" : Category.objects.all()
    })

def category(request, name):
    return render(request, "auctions/category.html", {
        "items" : AuctionListing.objects.filter(category=Category.objects.get(type=name)),
        "name" : name
    })
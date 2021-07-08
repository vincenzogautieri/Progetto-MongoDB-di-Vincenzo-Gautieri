from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from .forms import RegistrationForm, OrderForm
from .models import Profile, Order
import random


@login_required(login_url='login')
def home(request):
    user = User.objects.get(username=request.user)
    profile = Profile.objects.get(user=user)
    BTC = round(profile.BTC, 8)
    fiatMoney = round(profile.fiatMoney, 2)
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            order = form.save(commit=False)
            order.profile = profile
            if float(request.POST['quantity']) == 0 or float(request.POST['price']) == 0:
                messages.success(request, 'Impossible to perform the operation! Price or Quantity is equal to zero!')
                return redirect('home')
            elif 'sell' in request.POST:
                if profile.BTC >= float(request.POST['quantity']):
                    newSell = Order(profile=profile, price=request.POST['price'], quantity=request.POST['quantity'], type='Sell')
                    newSell.save()
                    try:
                        purchases = Order.objects.filter(type__contains='Buy').filter(complete=False).order_by('price')[0]
                        purchaseProfile = purchases.profile
                        firstBalance = round(purchaseProfile.fiatMoney, 2)
                        if purchases:
                            if float(request.POST['quantity']) == purchases.quantity:
                                if newSell.profile._id == purchases.profile._id:
                                    Order.objects.filter(_id=newSell._id).update(complete=True)
                                    Order.objects.filter(_id=purchases._id).update(complete=True)
                                    messages.success(request, 'Registered Order!')
                                    return redirect('home')
                                else:
                                    if purchases.price >= float(newSell.price):
                                        Order.objects.filter(_id=newSell._id).update(complete=True)
                                        Order.objects.filter(_id=purchases._id).update(complete=True)
                                        profile.BTC -= float(newSell.quantity)
                                        profile.fiatMoney += float(purchases.price)
                                        profile.profit += float(purchases.price)
                                        profile.save()
                                        purchaseProfile.BTC += float(purchases.quantity)
                                        purchaseProfile.fiatMoney -= float(purchases.price)
                                        profit = purchaseProfile.profit + (purchaseProfile.fiatMoney - firstBalance)
                                        purchaseProfile.profit = profit
                                        purchaseProfile.save()
                                        messages.success(request, 'Registered Order!')
                                        return redirect('home')
                                    else:
                                        messages.success(request, 'Registered Order!')
                                        return redirect('home')
                            elif float(request.POST['quantity']) > purchases.quantity:
                                quantityOrder = 0.0
                                listOrder = Order.objects.filter(type__contains='Buy').filter(complete=False).order_by('price')
                                listQuantityOrder = []
                                for i in listOrder:
                                    listQuantityOrder.append(i.quantity)
                                totQuantity = sum(listQuantityOrder)
                                for purchase in listOrder:
                                    quantityOrder += float(purchase.quantity)
                                    secondaryBalance = purchaseProfile.fiatMoney
                                    if quantityOrder > float(request.POST['quantity']):
                                        newQuantity = round(float(quantityOrder) - float(request.POST['quantity']), 8)
                                        newPrice = ((float(purchase.price) * float(newQuantity)) / float(purchase.quantity))
                                        if newSell.profile._id == purchase.profile._id:
                                            Order.objects.filter(_id=purchase._id).update(quantity=newQuantity)
                                            Order.objects.filter(_id=purchase._id).update(price=newPrice)
                                            Order.objects.filter(_id=newSell._id).update(complete=True)
                                            break
                                        else:
                                            if purchases.price >= float(newSell.price):
                                                profile.BTC -= float(newQuantity)
                                                profile.fiatMoney += ((float(purchase.price) * float(newQuantity)) / float(purchase.quantity))
                                                profile.profit += ((float(purchase.price) * float(newQuantity)) / float(purchase.quantity))
                                                profile.save()
                                                purchaseProfile.BTC += float(newQuantity)
                                                purchaseProfile.fiatMoney -= ((float(purchase.price) * float(newQuantity)) / float(purchase.quantity))
                                                profit = purchaseProfile.profit + (purchaseProfile.fiatMoney - secondaryBalance)
                                                purchaseProfile.profit = profit
                                                purchaseProfile.save()
                                                Order.objects.filter(_id=purchase._id).update(quantity=newQuantity)
                                                Order.objects.filter(_id=purchase._id).update(price=newPrice)
                                                Order.objects.filter(_id=newSell._id).update(complete=True)
                                                break
                                            else:
                                                messages.success(request, 'Registered Order!')
                                                return redirect('home')
                                    elif quantityOrder == float(request.POST['quantity']):
                                        if newSell.profile._id == purchase.profile._id:
                                            Order.objects.filter(_id=newSell._id).update(complete=True)
                                            Order.objects.filter(_id=purchase._id).update(complete=True)
                                            break
                                        else:
                                            if purchases.price >= float(newSell.price):
                                                Order.objects.filter(_id=purchase._id).update(complete=True)
                                                profile.BTC -= float(purchase.quantity)
                                                profile.fiatMoney += float(purchase.price)
                                                profile.profit += float(purchase.price)
                                                profile.save()
                                                purchaseProfile.BTC += float(purchase.quantity)
                                                purchaseProfile.fiatMoney -= float(purchase.price)
                                                profit = purchaseProfile.profit + (purchaseProfile.fiatMoney - secondaryBalance)
                                                purchaseProfile.profit = profit
                                                purchaseProfile.save()
                                                Order.objects.filter(_id=newSell._id).update(complete=True)
                                                break
                                            else:
                                                messages.success(request, 'Registered Order!')
                                                return redirect('home')
                                    elif totQuantity < float(request.POST['quantity']):
                                        newQuantity = round((float(request.POST['quantity']) - float(totQuantity)), 8)
                                        newPrice = ((float(newSell.price) * float(newQuantity)) / float(newSell.quantity))
                                        if newSell.profile._id == purchase.profile._id:
                                            Order.objects.filter(_id=newSell._id).update(quantity=newQuantity)
                                            Order.objects.filter(_id=newSell._id).update(price=newPrice)
                                            Order.objects.filter(_id=purchase._id).update(complete=True)
                                            break
                                        else:
                                            if purchases.price >= float(newSell.price):
                                                profile.BTC -= float(totQuantity)
                                                profile.fiatMoney += float(purchase.price)
                                                profile.profit += float(purchase.price)
                                                profile.save()
                                                purchaseProfile.BTC += float(totQuantity)
                                                purchaseProfile.fiatMoney -= float(purchase.price)
                                                profit = purchaseProfile.profit + (purchaseProfile.fiatMoney - secondaryBalance)
                                                purchaseProfile.profit = profit
                                                purchaseProfile.save()
                                                Order.objects.filter(_id=purchase._id).update(complete=True)
                                                Order.objects.filter(_id=newSell._id).update(quantity=newQuantity)
                                                Order.objects.filter(_id=newSell._id).update(price=newPrice)
                                                break
                                            else:
                                                messages.success(request, 'Registered Order!')
                                                return redirect('home')
                                    if newSell.profile._id == purchases.profile._id:
                                        Order.objects.filter(_id=purchase._id).update(complete=True)
                                        Order.objects.filter(_id=newSell._id).update(complete=True)
                                    else:
                                        if purchases.price >= float(newSell.price):
                                            Order.objects.filter(_id=purchase._id).update(complete=True)
                                            profile.BTC -= float(purchase.quantity)
                                            profile.fiatMoney += float(purchase.price)
                                            profile.profit += float(purchase.price)
                                            profile.save()
                                            purchaseProfile.BTC += float(purchase.quantity)
                                            purchaseProfile.fiatMoney -= float(purchase.price)
                                            profit = purchaseProfile.profit + (purchaseProfile.fiatMoney - firstBalance)
                                            purchaseProfile.profit = profit
                                            purchaseProfile.save()
                                            Order.objects.filter(_id=newSell._id).update(complete=True)
                                        else:
                                            messages.success(request, 'Registered Order!')
                                            return redirect('home')
                                messages.success(request, 'Registered Order!')
                                return redirect('home')
                            elif float(request.POST['quantity']) < purchases.quantity:
                                upgradeOrder = round((purchases.quantity - float(request.POST['quantity'])), 8)
                                newPrice = ((float(purchases.price) * float(upgradeOrder)) / float(purchases.quantity))
                                if newSell.profile._id == purchases.profile._id:
                                    Order.objects.filter(_id=purchases._id).update(quantity=upgradeOrder)
                                    Order.objects.filter(_id=purchases._id).update(price=newPrice)
                                    Order.objects.filter(_id=newSell._id).update(complete=True)
                                    messages.success(request, 'Registered Order!')
                                    return redirect('home')
                                else:
                                    if purchases.price >= float(newSell.price):
                                        profile.BTC -= float(newSell.quantity)
                                        profile.fiatMoney += ((float(purchases.price) * float(upgradeOrder)) / float(purchases.quantity))
                                        profile.profit += ((float(purchases.price) * float(upgradeOrder)) / float(purchases.quantity))
                                        profile.save()
                                        purchaseProfile.BTC += float(newSell.quantity)
                                        purchaseProfile.fiatMoney -= ((float(purchases.price) * float(upgradeOrder)) / float(purchases.quantity))
                                        profit = purchaseProfile.profit + (purchaseProfile.fiatMoney - firstBalance)
                                        purchaseProfile.profit = profit
                                        purchaseProfile.save()
                                        Order.objects.filter(_id=purchases._id).update(quantity=upgradeOrder)
                                        Order.objects.filter(_id=purchases._id).update(price=newPrice)
                                        Order.objects.filter(_id=newSell._id).update(complete=True)
                                        messages.success(request, 'Registered Order!')
                                        return redirect('home')
                                    else:
                                        messages.success(request, 'Registered Order!')
                                        return redirect('home')
                    except IndexError:
                        messages.error(request, "Registered Sale Order. Pending a Purchase Order!")
                        return redirect('home')
                else:
                    messages.error(request, 'Impossible to perform the operation! Insufficient BTC!')
                    return redirect('home')
            elif 'buy' in request.POST:
                if profile.fiatMoney >= float(request.POST['price']):
                    newBuy = Order(profile=profile, price=request.POST['price'], quantity=request.POST['quantity'], type='Buy')
                    newBuy.save()
                    try:
                        sales = Order.objects.filter(type__contains='Sell').filter(complete=False).order_by('price')[0]
                        saleProfile = sales.profile
                        firstBalance = round(saleProfile.fiatMoney, 2)
                        if sales:
                            if float(request.POST['quantity']) == sales.quantity:
                                if newBuy.profile._id == sales.profile._id:
                                    Order.objects.filter(_id=newBuy._id).update(complete=True)
                                    Order.objects.filter(_id=sales._id).update(complete=True)
                                    messages.success(request, 'Registered Order!')
                                    return redirect('home')
                                else:
                                    if sales.price >= float(newBuy.price):
                                        Order.objects.filter(_id=newBuy._id).update(complete=True)
                                        profile.BTC += float(newBuy.quantity)
                                        profile.fiatMoney -= float(sales.price)
                                        profile.profit -= float(sales.price)
                                        profile.save()
                                        Order.objects.filter(_id=sales._id).update(complete=True)
                                        saleProfile.BTC -= float(sales.quantity)
                                        saleProfile.fiatMoney += float(sales.price)
                                        profit = saleProfile.profit + (saleProfile.fiatMoney - firstBalance)
                                        saleProfile.profit = profit
                                        saleProfile.save()
                                        messages.success(request, 'Registered Order!')
                                        return redirect('home')
                                    else:
                                        messages.success(request, 'Registered Order!')
                                        return redirect('home')
                            elif float(request.POST['quantity']) > sales.quantity:
                                quantityOrder = 0.0
                                listOrder = Order.objects.filter(type__contains='Sell').filter(complete=False).order_by('price')
                                listQuantityOrder = []
                                for i in listOrder:
                                    listQuantityOrder.append(i.quantity)
                                totQuantity = sum(listQuantityOrder)
                                for sale in listOrder:
                                    quantityOrder += float(sale.quantity)
                                    secondaryBalance = saleProfile.fiatMoney
                                    if quantityOrder > float(request.POST['quantity']):
                                        newQuantity = round((float(quantityOrder) - float(request.POST['quantity'])), 8)
                                        newPrice = ((float(sale.price) * float(newQuantity)) / float(sale.quantity))
                                        if newBuy.profile._id == sales.profile._id:
                                            Order.objects.filter(_id=sale._id).update(quantity=newQuantity)
                                            Order.objects.filter(_id=sale._id).update(price=newPrice)
                                            Order.objects.filter(_id=newBuy._id).update(complete=True)
                                            break
                                        else:
                                            if sales.price >= float(newBuy.price):
                                                profile.BTC += float(newQuantity)
                                                profile.fiatMoney -= ((float(sale.price) * float(newQuantity)) / float(sale.quantity))
                                                profile.profit -= ((float(sale.price) * float(newQuantity)) / float(sale.quantity))
                                                profile.save()
                                                saleProfile.BTC -= float(newQuantity)
                                                saleProfile.fiatMoney += ((float(sale.price) * float(newQuantity)) / float(sale.quantity))
                                                profit = saleProfile.profit + (saleProfile.fiatMoney - secondaryBalance)
                                                saleProfile.profit = profit
                                                saleProfile.save()
                                                Order.objects.filter(_id=sale._id).update(quantity=newQuantity)
                                                Order.objects.filter(_id=sale._id).update(price=newPrice)
                                                Order.objects.filter(_id=newBuy._id).update(complete=True)
                                                break
                                            else:
                                                messages.success(request, 'Registered Order!')
                                                return redirect('home')
                                    elif quantityOrder == float(request.POST['quantity']):
                                        if newBuy.profile._id == sales.profile._id:
                                            Order.objects.filter(_id=newBuy._id).update(complete=True)
                                            Order.objects.filter(_id=sale._id).update(complete=True)
                                            break
                                        else:
                                            if sales.price >= float(newBuy.price):
                                                Order.objects.filter(_id=sale._id).update(complete=True)
                                                profile.BTC += float(sale.quantity)
                                                profile.fiatMoney -= float(sale.price)
                                                profile.profit -= float(sale.price)
                                                profile.save()
                                                saleProfile.BTC -= float(sale.quantity)
                                                saleProfile.fiatMoney += float(sale.price)
                                                profit = saleProfile.profit + (saleProfile.fiatMoney - secondaryBalance)
                                                saleProfile.profit = profit
                                                saleProfile.save()
                                                Order.objects.filter(_id=newBuy._id).update(complete=True)
                                                break
                                            else:
                                                messages.success(request, 'Registered Order!')
                                                return redirect('home')
                                    elif totQuantity < float(request.POST['quantity']):
                                        newQuantity = round((float(request.POST['quantity']) - float(totQuantity)), 8)
                                        newPrice = ((float(newBuy.price) * float(newQuantity)) / float(newBuy.quantity))
                                        if newBuy.profile._id == sales.profile._id:
                                            Order.objects.filter(_id=newBuy._id).update(quantity=newQuantity)
                                            Order.objects.filter(_id=newBuy._id).update(price=newPrice)
                                            Order.objects.filter(_id=sale._id).update(complete=True)
                                            break
                                        else:
                                            if sales.price >= float(newBuy.price):
                                                profile.BTC += float(totQuantity)
                                                profile.fiatMoney -= float(sale.price)
                                                profile.profit -= float(sale.price)
                                                profile.save()
                                                saleProfile.BTC -= float(totQuantity)
                                                saleProfile.fiatMoney += float(sale.price)
                                                profit = saleProfile.profit + (saleProfile.fiatMoney - secondaryBalance)
                                                saleProfile.profit = profit
                                                saleProfile.save()
                                                Order.objects.filter(_id=sale._id).update(complete=True)
                                                Order.objects.filter(_id=newBuy._id).update(quantity=newQuantity)
                                                Order.objects.filter(_id=newBuy._id).update(price=newPrice)
                                                break
                                            else:
                                                messages.success(request, 'Registered Order!')
                                                return redirect('home')
                                    if newBuy.profile._id == sales.profile._id:
                                        Order.objects.filter(_id=sale._id).update(complete=True)
                                        Order.objects.filter(_id=newBuy._id).update(complete=True)
                                    else:
                                        if sales.price >= float(newBuy.price):
                                            Order.objects.filter(_id=sale._id).update(complete=True)
                                            profile.BTC += float(sale.quantity)
                                            profile.fiatMoney -= float(sale.price)
                                            profile.profit -= float(sale.price)
                                            profile.save()
                                            saleProfile.BTC -= float(sale.quantity)
                                            saleProfile.fiatMoney += float(sale.price)
                                            profit = saleProfile.profit + (saleProfile.fiatMoney - firstBalance)
                                            saleProfile.profit = profit
                                            saleProfile.save()
                                            Order.objects.filter(_id=newBuy._id).update(complete=True)
                                        else:
                                            messages.success(request, 'Registered Order!')
                                            return redirect('home')
                                messages.success(request, 'Registered Order!')
                                return redirect('home')
                            elif float(request.POST['quantity']) < sales.quantity:
                                upgradeOrder = round((sales.quantity - float(request.POST['quantity'])), 8)
                                newPrice = ((float(sales.price) * float(upgradeOrder)) / float(sales.quantity))
                                if newBuy.profile._id == sales.profile._id:
                                    Order.objects.filter(_id=sales._id).update(quantity=upgradeOrder)
                                    Order.objects.filter(_id=sales._id).update(price=newPrice)
                                    Order.objects.filter(_id=newBuy._id).update(complete=True)
                                    messages.success(request, 'Registered Order!')
                                    return redirect('home')
                                else:
                                    if sales.price >= float(newBuy.price):
                                        profile.BTC += float(newBuy.quantity)
                                        profile.fiatMoney -= ((float(sales.price) * float(upgradeOrder)) / float(sales.quantity))
                                        profile.profit -= ((float(sales.price) * float(upgradeOrder)) / float(sales.quantity))
                                        profile.save()
                                        saleProfile.BTC -= float(newBuy.quantity)
                                        saleProfile.fiatMoney += ((float(sales.price) * float(upgradeOrder)) / float(sales.quantity))
                                        profit = saleProfile.profit + (saleProfile.fiatMoney - firstBalance)
                                        saleProfile.profit = profit
                                        saleProfile.save()
                                        Order.objects.filter(_id=sales._id).update(quantity=upgradeOrder)
                                        Order.objects.filter(_id=sales._id).update(price=newPrice)
                                        Order.objects.filter(_id=newBuy._id).update(complete=True)
                                        messages.success(request, 'Registered Order!')
                                        return redirect('home')
                                    else:
                                        messages.success(request, 'Registered Order!')
                                        return redirect('home')
                    except IndexError:
                        messages.error(request, "Registered Purchase Order. Pending a Sale Order!")
                        return redirect('home')
                else:
                    messages.error(request, 'Impossible to perform the operation! Insufficient Funds!')
                    return redirect('home')
    else:
        form = OrderForm()
    return render(request, 'app/home.html', {'form': form, 'BTC': BTC, 'fiatMoney': fiatMoney})


@login_required(login_url='login')
def orderBook(request):
    response = []
    activeOrders = Order.objects.filter(complete=False)
    for order in activeOrders:
        response.append(
            {
                'Order ID': str(order._id),
                'Typology': order.type,
                'Datetime': order.datetime,
                'Price': round((order.price), 2),
                'Quantity': round((order.quantity), 8),
            }
        )
    return JsonResponse(response, safe=False)


@login_required(login_url='login')
def profit(request):
    response = []
    user = User.objects.get(username=request.user)
    profile = Profile.objects.get(user=user)
    response.append(
            {
                'User ID': str(profile._id),
                'Name': profile.user.first_name,
                'Surname': profile.user.last_name,
                'Balance': round((profile.fiatMoney), 2),
                'BTC': round((profile.BTC), 8),
                'Profit': round((profile.profit), 2),
            }
        )
    return JsonResponse(response, safe=False)


def registerView(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            profile = Profile.objects.create(user=user)
            profile.BTC = round(random.uniform(1, 10), 8)
            profile.save()
            messages.success(request, 'Congratulations! Your new account has been successfully created!')
            return redirect('login')
    else:
        form = RegistrationForm()
    return render(request, 'app/register.html', {'form': form})


def loginView(request):
    if request.user.is_authenticated:
        return redirect('home')
    else:
        if request.method == "POST":
            username = request.POST.get('username')
            password = request.POST.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
            else:
                messages.error(request, 'Username or Password is incorrect!')
        return render(request, 'app/login.html')


def logoutView(request):
    logout(request)
    return redirect('login')
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
    BTC = profile.BTC
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
                    messages.success(request, 'Registered Order!')
                    return redirect('home')
                else:
                    messages.error(request, 'Impossible to perform the operation! Insufficient BTC!')
                    return redirect('home')
            elif 'buy' in request.POST:
                if profile.fiatMoney >= float(request.POST['price']):
                    newBuy = Order(profile=profile, price=request.POST['price'], quantity=request.POST['quantity'], type='Buy')
                    newBuy.save()
                    try:
                        sales = Order.objects.filter(type__contains='Sell').filter(complete=False).order_by('quantity').order_by('price')[0]
                        saleProfile = sales.profile
                        firstBalance = round(saleProfile.fiatMoney, 2)
                        if sales:
                            if float(request.POST['quantity']) == sales.quantity:
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
                            elif float(request.POST['quantity']) > sales.quantity:
                                quantityOrder = 0.0
                                listOrder = Order.objects.filter(type__contains='Sell').filter(complete=False).order_by('quantity').order_by('price')
                                listQuantityOrder = []
                                for i in listOrder:
                                    listQuantityOrder.append(i.quantity)
                                totQuantity = sum(listQuantityOrder)
                                if totQuantity < float(request.POST['quantity']):
                                    Order.objects.filter(_id=newBuy._id).delete()
                                    messages.success(request, 'There are not enough sales orders to complete the task!')
                                    return redirect('home')
                                else:
                                    for sale in list(Order.objects.filter(type__contains='Sell').filter(complete=False).order_by('quantity').order_by('price')):
                                        quantityOrder += float(sale.quantity)
                                        secondaryBalance = saleProfile.fiatMoney
                                        if quantityOrder > float(request.POST['quantity']):
                                            newQuantity = round(float(quantityOrder) - float(request.POST['quantity']), 8)
                                            newPrice = ((float(sale.price) * float(newQuantity)) / float(sale.quantity))
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
                                            break
                                        elif quantityOrder == float(request.POST['quantity']):
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
                                            break
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
                                    messages.success(request, 'Registered Order!')
                                    return redirect('home')
                            elif float(request.POST['quantity']) < sales.quantity:
                                upgradeOrder = sales.quantity - float(request.POST['quantity'])
                                newPrice = ((float(sales.price) * float(upgradeOrder)) / float(sales.quantity))
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
                    except IndexError:
                        Order.objects.filter(_id=newBuy._id).delete()
                        messages.error(request, "Don't exist sell orders!")
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
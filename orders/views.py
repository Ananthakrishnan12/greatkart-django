from django.shortcuts import render, redirect
from .models import Payment, Order, OrderProduct
from store.models import Product
from django.http import HttpResponse,JsonResponse
from .forms import OrderForm
from cart.models import CartItem
import datetime  # ✅ Missing import fixed
from django.core.mail import EmailMessage
from django.template.loader import render_to_string

from django.views.decorators.csrf import csrf_exempt
import json


@csrf_exempt
def payments(request):
    body=json.loads(request.body)
    order=Order.objects.get(user=request.user,is_ordered=False,order_number=body["orderID"])
    # store transactions details in the payment model:
    payment=Payment(
        user=request.user,
        payment_id=body["transID"],
        payment_method=body["payment_method"],
        amount_paid=order.order_total,
        status=body['status'],
    )
    payment.save()
    
    order.payment=payment
    order.is_ordered=True
    order.save()
    
    # Move the cart items to Order Product table
    cart_items=CartItem.objects.filter(user=request.user)
    
    
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order = order
        orderproduct.payment = payment
        orderproduct.user = request.user
        orderproduct.product = item.product
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered = True
        orderproduct.save()

        # Set variations
        product_variation = item.variations.all()
        orderproduct.variations.set(product_variation)
        orderproduct.save()

        # Reduce stock
        product = Product.objects.get(id=item.product.id)
        product.stock -= item.quantity
        product.save()

    
    
    # clear cart
    CartItem.objects.filter(user=request.user).delete()
    
    
    
    # send order recieved email to customer
    mail_subject="Thank you for our Order!!!"
    message=render_to_string("orders/order_recieved_email.html",{
                'user':request.user,
                'order':order,
            })
    to_email=request.user.email
    send_email=EmailMessage(mail_subject,message,to=[to_email])
    send_email.send()
    
    
    
    # send order number and transaction id back to sendData method via JsonResponse
    data={
        'order_number':order.order_number,
        'transID':payment.payment_id,
    }
    
    return JsonResponse(data)




def place_order(request, total=0, quantity=0):
    current_user = request.user

    # If the cart count is less than or equal to zero, redirect to store
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    if cart_count <= 0:
        return redirect('store')

    grand_total = 0
    tax = 0
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity

    tax = (2 * total) / 100  # 2% tax
    grand_total = total + tax

    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            # Store all the billing information inside Order table
            data = Order()
            data.user = current_user  # ✅ Missing: associate order with user
            data.first_name = form.cleaned_data["first_name"]
            data.last_name = form.cleaned_data["last_name"]
            data.phone = form.cleaned_data["phone"]
            data.email = form.cleaned_data["email"]
            data.address_line_1 = form.cleaned_data["address_line_1"]
            data.address_line_2 = form.cleaned_data["address_line_2"]
            data.country = form.cleaned_data["country"]
            data.state = form.cleaned_data["state"]
            data.city = form.cleaned_data["city"]
            data.order_note = form.cleaned_data["order_note"]
            data.order_total = grand_total
            data.tax = tax
            data.ip = request.META.get('REMOTE_ADDR')
            
            data.is_ordered=False
            data.save()

            # Generate unique order number
            current_date = datetime.date.today().strftime('%Y%m%d')
            order_number = current_date + str(data.id)
            data.order_number = order_number
            data.save()
            
            order=data
            context={
                "order":order,
                "cart_items":cart_items,
                "total":total,
                "tax":tax,
                "grand_total":grand_total,
            }

            # You can also render a template to review the order
            return render(request,"orders/payments.html",context)

    else:
        return redirect('checkout')
    
    
    
def order_complete(request):
    order_number=request.GET.get('order_number')
    transID=request.GET.get('payment_id')
    
    
    try:
        order=Order.objects.get(order_number=order_number,is_ordered=True)
        ordered_products=OrderProduct.objects.filter(order_id=order.id)
        
        
        subtotal=0
        for i in ordered_products:
            subtotal +=i.product_price*i.quantity
        
        payment=Payment.objects.get(payment_id=transID)
        
        context={
            'order':order,
            'ordered_products':ordered_products,
            'order_number':order.order_number,
            'transID':payment.payment_id,
            'payment':payment,
            'subtotal':subtotal,
        }
        return render(request,'orders/order_complete.html',context)
    except (Payment.DoesNotExist,Order.DoesNotExist):
        return redirect("home")
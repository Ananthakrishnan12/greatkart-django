from django.http import HttpResponse
from django.shortcuts import render,redirect,get_object_or_404
from .forms import RegistrationForm,UserForm,UserProfileForm
from .models import Account,UserProfile
from django.contrib import messages,auth
from django.contrib.auth.decorators import login_required

# Verification email:
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode,urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMessage

from cart.views import _cart_id
from cart.models import Cart,CartItem

from orders.models import Order,OrderProduct

import requests



def register(request):
    if request.method=="POST":
        form=RegistrationForm(request.POST)
        if form.is_valid():
            first_name=form.cleaned_data['first_name']
            last_name=form.cleaned_data['last_name']
            phone_number=form.cleaned_data['phone_number']
            email=form.cleaned_data['email']
            password=form.cleaned_data['password']
            username=email.split("@")[0]
            user=Account.objects.create_user(first_name=first_name,last_name=last_name,email=email,username=username,password=password)
            user.phone_number=phone_number
            user.save()
            
            
            # Create user profile:
            profile=UserProfile()
            profile.user_id=user.id
            profile.profile_picture='default/default-user.png'
            profile.save()
        
            
            messages.success(request,'Registration sucessfull.')
            return redirect("register")
    else:
        form=RegistrationForm()
    context={
        "form":form,
    }
    return render(request,"accounts/register.html",context)

def user_login(request):
    if request.method == "POST":
        email = request.POST["email"]
        password = request.POST["password"]

        user = auth.authenticate(email=email, password=password)

        if user is not None:
            try:
                cart = Cart.objects.get(cart_id=_cart_id(request))
                is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()

                if is_cart_item_exists:
                    cart_items = CartItem.objects.filter(cart=cart)

                    # Get the product variations from the current session cart
                    product_variation = []
                    for item in cart_items:
                        variation = item.variations.all()
                        product_variation.append(list(variation))

                    # Get the existing cart items from the user (if any)
                    user_cart_items = CartItem.objects.filter(user=user)
                    ex_var_list = []
                    id_list = []

                    for item in user_cart_items:
                        existing_variation = item.variations.all()
                        ex_var_list.append(list(existing_variation))
                        id_list.append(item.id)

                    # Compare each session cart variation with the user's cart variations
                    for pr in product_variation:
                        if pr in ex_var_list:
                            index = ex_var_list.index(pr)
                            item_id = id_list[index]
                            item = CartItem.objects.get(id=item_id)
                            item.quantity += 1
                            item.user = user
                            item.save()
                        else:
                            # Assign session cart items to the logged-in user
                            for item in cart_items:
                                item.user = user
                                item.save()
            except Cart.DoesNotExist:
                pass

            auth.login(request, user)
            messages.success(request, "You are logged in.")
            url = request.META.get('HTTP_REFERER')
            try:
                query=requests.utils.urlparse(url).query
                # next=/cart/checkout/
                params=dict(x.split('=') for x in query.split('&'))
                if 'next' in params:
                    nextPage=params["next"]
                    return redirect(nextPage)
            except:
                return redirect("dashboard")

        else:
            messages.error(request, "Invalid login credentials")
            return redirect("user_login")

    return render(request, "accounts/login.html")


@login_required(login_url = "user_login")
def logout(request):
    auth.logout(request)
    messages.success(request,"You are logged out.")
    return redirect("user_login")


@login_required(login_url = "user_login")
def dashboard(request):
    orders=Order.objects.order_by('-created_at').filter(user_id=request.user.id,is_ordered=True)
    orders_count=orders.count()
    
    userprofile=UserProfile.objects.get(user_id=request.user.id)
    
    context={
        'orders_count':orders_count,
        'userprofile':userprofile,
    }
    return render(request,'accounts/dashboard.html',context)


def forget_password(request):
    if request.method == "POST":
        email=request.POST["email"]
        
        if Account.objects.filter(email=email).exists():
            user=Account.objects.get(email__exact=email)
            
            current_site=get_current_site(request)
            mail_subject="Reset your password"
            message=render_to_string("accounts/reset_password_email.html",{
                'user':user,
                'domain':current_site,
                'uid':urlsafe_base64_encode(force_bytes(user.pk)),
                'token':default_token_generator.make_token(user),
            })
            to_email=email
            send_email=EmailMessage(mail_subject,message,to=[to_email])
            send_email.send()
            
            messages.success(request,"Password reset email has been sent to your email address")
            return redirect("user_login")
            
        else:
            messages.error(request,"Email does not exists")
            return redirect("forget_password")
    return render(request,'accounts/forget_password.html')




def resetpassword_validate(request,uidb64,token):
    try:
        uid= urlsafe_base64_decode(uidb64).decode()
        user= Account.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, Account.DoesNotExist):
        user = None
        
    if user is not None and default_token_generator.check_token(user,token):
        request.session['uid']=uid
        messages.success(request,'Please reset your password')
        return redirect('resetpassword')
    else:
        messages.error(request,"This link has experied")
        return redirect("user_login")        

def resetpassword(request):
    if request.method =="POST":
        password=request.POST.get("password")
        confirm_password=request.POST.get("confirm_password")
        
        if password == confirm_password:
            uid=request.session.get('uid')
            user=Account.objects.get(pk=uid)
            user.set_password(password)   # it make the password as hashed password..
            user.save() 
            
            messages.success(request,"Password reset sucessfull..")
            return redirect('user_login')         
            
            
        else:
            messages.error(request,"Password does not match")
            return redirect('resetpassword')
    else:
        return render(request,'accounts/resetpassword.html')
    
@login_required(login_url = "user_login")   
def my_orders(request):
    orders=Order.objects.filter(user=request.user,is_ordered=True).order_by('-created_at')
    context={
        'orders':orders,
    }
    return render(request,"accounts/my_orders.html",context)


@login_required(login_url = "user_login")
def edit_profile(request):
    userprofile=get_object_or_404(UserProfile,user=request.user)
    if request.method=="POST":
        user_form=UserForm(request.POST,instance=request.user)
        profile_form=UserProfileForm(request.POST,request.FILES,instance=userprofile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request,"Your profile has been updated")
            return redirect("edit_profile")
    else:
        user_form=UserForm(instance=request.user)
        profile_form=UserProfileForm(instance=userprofile)
    context={
        'user_form':user_form,
        'profile_form':profile_form,
        'userprofile': userprofile,
    }
    return render(request,'accounts/edit_profile.html',context)



@login_required(login_url="user_login")
def change_password(request):
    if request.method == "POST":
        current_password = request.POST['current_password']
        new_password = request.POST['new_password']
        confirm_password = request.POST['confirm_password']
        
        user = Account.objects.get(username__exact=request.user.username)
        
        if new_password == confirm_password:
            if user.check_password(current_password):
                user.set_password(new_password)
                user.save()
                messages.success(request, "Password updated successfully")
                return redirect('user_login')  # Redirect to login or a success page
            else:
                messages.error(request, "Current password is incorrect")
        else:
            messages.error(request, "New password and confirm password do not match")

        return redirect('change_password')  # Only redirect after POST failure
    
    # ✅ Handle GET properly
    return render(request, 'accounts/change_password.html')



@login_required(login_url="user_login")
def order_detail(request,order_id):
    order_detail=OrderProduct.objects.filter(order__order_number=order_id)
    order=Order.objects.get(order_number=order_id)
    subtotal=0
    for i in order_detail:
        subtotal+=i.product_price*i.quantity
    context={
        'order_detail':order_detail,
        'order':order,
        'subtotal':subtotal,
    }
    return render(request,'accounts/order_detail.html',context)
    

 

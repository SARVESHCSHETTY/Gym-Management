from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from authapp.models import Contact,MembershipPlan,Trainer,Enrollment,Gallery,Attendance
from django.conf import settings
import razorpay
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

   


def Home(request):
    return render(request,"index.html")

def gallery(request):
    posts=Gallery.objects.all()
    context={"posts":posts}
    return render(request,"gallery.html",context)

def attendence(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please Login and Try Again")
        return redirect('/login')
    SelectTrainer = Trainer.objects.all()
    context = {"SelectTrainer": SelectTrainer}
    if request.method == "POST":
        phonenumber = request.POST.get('PhoneNumber')  
        Login = request.POST.get('logintime')
        Logout = request.POST.get('logouttime')
        SelectWorkout = request.POST.get('workout')
        TrainedBy = request.POST.get('trainer')
        query = Attendance(
            phonenumber=phonenumber,  
            Login=Login,
            Logout=Logout,
            SelectWorkout=SelectWorkout,
            TrainedBy=TrainedBy
        )
        query.save()
        messages.success(request, "Attendance Applied Successfully")
        return redirect('/attendence')
    return render(request, "attendence.html", context)



def profile(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please Login and Try Again")
        return redirect('/login')

    
    user_phone = request.user.username  

  
    posts = Enrollment.objects.filter(PhoneNumber=user_phone)
    attendance = Attendance.objects.filter(phonenumber=user_phone)

    context = {"posts": posts, "attendance": attendance}
    return render(request, "profile.html", context)
    



def signup(request):
    if request.method=="POST":
        username=request.POST.get('usernumber')
        email=request.POST.get('email')
        pass1=request.POST.get('pass1')
        pass2=request.POST.get('pass2')
      
        if len(username) != 10:
            messages.info(request,"Phone Number Must be 10 Digits")
            return redirect('/signup')

        if pass1!=pass2:
            messages.info(request,"Password is not Matching")
            return redirect('/signup')
       
        try:
            if User.objects.get(username=username):
                messages.warning(request,"Phone Number is Taken")
                return redirect('/signup')
           
        except Exception as identifier:
            pass
        
        
        try:
            if User.objects.get(email=email):
                messages.warning(request,"Email is Taken")
                return redirect('/signup')
           
        except Exception as identifier:
            pass
        
        myuser=User.objects.create_user(username,email,pass1)
        myuser.save()
        messages.success(request,"User is Created Please Login")
        return redirect('/login')
        
    return render(request,"signup.html")

def handlelogin(request):
    if request.method=="POST":        
        username=request.POST.get('usernumber')
        pass1=request.POST.get('pass1')
        myuser=authenticate(username=username,password=pass1)
        if myuser is not None:
            login(request,myuser)
            messages.success(request,"Login Successful")
            return redirect('/')
        else:
            messages.error(request,"Invalid Credentials")
            return redirect('/login')
            
    return render(request,"handlelogin.html")

def handlelogout(request):
    logout(request)
    messages.success(request,"Logout Sucess")
    return redirect('/login')

def contact(request):
    if request.method=="POST":
        name=request.POST.get('fullname')
        email=request.POST.get('email')
        number=request.POST.get('num')
        desc=request.POST.get('desc')
        myquery=Contact(name=name,email=email,phonenumber=number,description=desc)
        myquery.save()       
        messages.info(request,"Thanks for Contacting us we will get back you soon")
        return redirect('/contact')
    return render(request,"contact.html")




def enroll(request):
    if not request.user.is_authenticated:
        messages.warning(request, "Please Login and Try Again")
        return redirect('/login')

    Membership = MembershipPlan.objects.all()
    SelectTrainer = Trainer.objects.all()
    context = {"Membership": Membership, "SelectTrainer": SelectTrainer}

    if request.method == "POST":
        try:
            # Get form data
            FullName = request.POST.get('FullName')
            email = request.POST.get('email')
            gender = request.POST.get('gender')
            PhoneNumber = request.POST.get('PhoneNumber')
            DOB = request.POST.get('DOB')
            member_id = request.POST.get('member')  # ID of membership plan
            trainer_name = request.POST.get('trainer')
            reference = request.POST.get('reference')
            address = request.POST.get('address')

            # Fetch Membership Plan and Trainer objects
            membership_plan = MembershipPlan.objects.get(id=member_id)
            trainer = Trainer.objects.get(name=trainer_name)

            # Razorpay Payment Integration
            amount = int(membership_plan.price) * 100  # Convert to paise
            client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
            payment_order = client.order.create({
                "amount": amount,
                "currency": "INR",
                "payment_capture": "1"
            })

            # Save Enrollment with Payment Status as "Pending" and Razorpay order ID
            enrollment = Enrollment.objects.create(
                FullName=FullName,
                Email=email,
                Gender=gender,
                PhoneNumber=PhoneNumber,
                DOB=DOB,
                SelectMembershipplan=membership_plan.plan,
                SelectTrainer=trainer,
                Reference=reference,
                Address=address,
                paymentStatus="Pending",  # Initially set as "Pending"
                Price=membership_plan.price,
                DueDate=None,
                razorpay_order_id=payment_order['id'],  # Save Razorpay order ID
            )

            # Pass Payment Details to Payment Page
            context.update({
                "payment": payment_order,
                "FullName": FullName,
                "email": email,
                "PhoneNumber": PhoneNumber,
                "amount": membership_plan.price,
                "order_id": payment_order["id"]
            })

            return render(request, "payment.html", context)

        except MembershipPlan.DoesNotExist:
            messages.error(request, "Invalid Membership Plan Selected.")
        except Trainer.DoesNotExist:
            messages.error(request, "Invalid Trainer Selected.")
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")

    return render(request, "enroll.html", context)


@login_required
def payment_success(request):
    payment_id = request.GET.get("payment_id")
    order_id = request.GET.get("order_id")

    try:
        # Query the Enrollment model using the razorpay_order_id
        enrollment = Enrollment.objects.get(razorpay_order_id=order_id)

        # Check the payment status from Razorpay
        client = razorpay.Client(auth=(settings.RAZOR_KEY_ID, settings.RAZOR_KEY_SECRET))
        payment = client.payment.fetch(payment_id)
        payment_status = payment.get('status')  # 'captured', 'failed', 'pending'

        if payment_status == 'captured':
            # Payment successful
            enrollment.paymentStatus = "Paid"
        elif payment_status == 'failed':
            # Payment failed
            enrollment.paymentStatus = "Failed"
        else:
            # Payment is pending
            enrollment.paymentStatus = "Pending"

        enrollment.save()

        # Add a success message and redirect to the profile page
        messages.success(request, f"Payment {enrollment.paymentStatus}! Your enrollment is confirmed.")
        return redirect('profile')  # Adjust 'profile' if needed to match your URL name

    except Enrollment.DoesNotExist:
        # Handle the case when no matching enrollment is found
        messages.error(request, "Invalid payment reference.")
        return HttpResponse("Invalid payment reference.", status=400)

    except razorpay.errors.RazorpayError as e:
        # Handle Razorpay API error
        messages.error(request, f"Razorpay error: {str(e)}")
        return HttpResponse("Payment processing error.", status=500)


def biceps_view(request):
    return render(request, 'biceps.html')

def back_view(request):
    return render(request, 'back.html')

def shoulder_view(request):
    return render(request, 'shoulder.html')

def chest_view(request):
    return render(request, 'chest.html')

def leg_view(request):
    return render(request, 'leg.html')
from django.urls import path,include
from authapp import views
from .views import biceps_view,back_view,shoulder_view,chest_view,leg_view

urlpatterns = [
    path ('',views.Home,name="Home"),
    path('signup',views.signup,name="signup"),
    path('login',views.handlelogin,name="handlelogin"),
    path('logout',views.handlelogout,name="handlelogout"),
    path('contact',views.contact,name="contact"),
    path('enroll/', views.enroll, name='enroll'),
    path('profile',views.profile,name="profile"),
    path('gallery',views.gallery,name="gallery"),
    path('attendence',views.attendence,name="attendence"),
    path('payment-success/', views.payment_success, name='payment-success'),
    path('biceps/', biceps_view, name='biceps'),
    path('back/', back_view, name='back'),
    path('shoulder/', shoulder_view, name='shoulder'),
    path('chest/', chest_view, name='chest'),
    path('leg/', leg_view, name='leg'),
    
    
]

"""Hotel_AC_Sys URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
import Service.views as service_views
import Management.views as management_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('service/PowerOn/', management_views.power_on),
    path('service/RequestOn/', service_views.request_on),
    path('service/ChangeTargetTemp/', service_views.change_target_temp),
    path('service/ChangeFanSpeed/', service_views.change_fan_speed),
    path('service/RequestOff/', service_views.request_off),
    path('service/CheckRoomState/', management_views.check_room_state),
    path('room/Request/', service_views.request_info),
    path('front_desk/CheckRDR', management_views.check_RDR),
    path('front_desk/CheckBill', management_views.check_bill),
    path('manager/CheckReport', management_views.check_report),
    path('service/Request/', service_views.request_info),
]

"""
URL configuration for wyzcon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
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
from django.urls import path, include
from organizations.backends import invitation_backend
from threading import Thread, Lock
#from task.threading import task_d_5, task_d_2,task_d_1, task_d_s, task1, task2
import notifications.urls

lock = Lock()
#t1 = Thread(target=task1, name='t1', args = [lock,])
#t2 = Thread(target=task2, name='t2', args = [lock,])
#td5= Thread(target = task_d_5, name = 'td5', args = [lock])

    # starting threads
#t1.start()
#t2.start()
#td5.start()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('authentications/', include('auths.urls')),
    path('accounts/', include('organizations.urls')),
    path('invitations/', include(invitation_backend().get_urls())),
    path('organizations/', include('orgs.urls')),
    path('sapiens/', include('homosapiens.urls')),
    path('tiempo/', include('tiempo.urls')),
    path('services/', include('services.urls')),
    path('session/', include('session.urls')),
    path('address/', include('wyz_address.urls')),
    path('engagements/', include('engagement.urls')),
    path('actions/', include('actions.urls')),
    path('notifications/', include('notify_stream.urls')),
    path('^inbox/notifications/', include(notifications.urls, namespace='notifications')),
    path('perms/', include('perms.urls')),
    path('works/', include('works.urls')),
    path('screener/', include('screener.urls')),
]

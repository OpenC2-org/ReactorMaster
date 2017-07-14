"""reactor_master URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.10/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.contrib.auth import views as auth_views
from reactor_master import views
from reactor_master import forms

urlpatterns = [
    
    #url(r'^admin/', admin.site.urls),
    
    # GUI Views
    url(r'^$', views.home),
    url(r'^job/(?P<id>.*)/$',views.job),
    url(r'^relay/(?P<relay_id>.*)/$',views.relay),

    # Sync with downstream 
    url(r'^sync/$', views.sync),

    # OpenC2 API Endpoint
    url(r'^openc2/', views.service_router),

    # REST - command creation
    url(r'^rest/command/(?P<capa_id>.*)/(?P<target_id>.*)/$',views.rest_make_command),

    # REST - view targets for a capa
    url(r'^rest/targets/(?P<capa_id>.*)/$',views.rest_get_targets),

    # Cron
    url(r'^cron/launch/$',views.cron_launcher),

    # Authentication
    url(r"^login/", auth_views.login, {"template_name": "reactor_master/login.html",
                                       "authentication_form": forms.LoginForm,
                                       },name="login"),

    url(r"^logout/", auth_views.logout, {"next_page": "/login"}),

]

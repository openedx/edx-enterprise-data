"""
Enterprise_data url configuration.
"""


from django.conf.urls import include, url
from django.contrib import admin

app_name = 'enterprise_data'
urlpatterns = [
    url(
        r'^enterprise/api/',
        include('enterprise_data.api.urls'),
        name='enterprise_data_api'
    ),
    url(r"^admin/", admin.site.urls),
]

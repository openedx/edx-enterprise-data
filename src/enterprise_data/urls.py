"""
Enterprise_data url configuration.
"""

from django.urls import include, path

app_name = 'enterprise_data'
urlpatterns = [
    path('enterprise/api/', include('enterprise_data.api.urls'),
         name='enterprise_data_api'
         ),
]

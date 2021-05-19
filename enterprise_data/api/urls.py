"""
URL definitions for enterprise data API endpoint.
"""


from django.conf.urls import include, url

urlpatterns = [
    url(r'^v0/', include('enterprise_data.api.v0.urls', 'v0'), name='api_v0'),
    url(r'^v1/', include('enterprise_data.api.v1.urls', 'v1'), name='api_v1'),
]

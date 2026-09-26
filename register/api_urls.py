from django.urls import path
from . import api_views

urlpatterns = [
    # Auth / Current user
    path('auth/me/', api_views.current_user_view, name='api_current_user'),

    # Dashboard analytics
    path('dashboard/', api_views.dashboard_analytics_api, name='api_dashboard_analytics'),

    # Trips CRUD & listing
    path('trips/', api_views.trips_collection_api, name='api_trips_collection'),
    path('trips/<int:pk>/', api_views.trip_detail_api, name='api_trip_detail'),
    path('trips/<int:pk>/slip-pdf/', api_views.trip_slip_pdf_api, name='api_trip_slip_pdf'),
    path('trips/custom-slip-pdf/', api_views.custom_slip_pdf_api, name='api_custom_slip_pdf'),

    # Masters
    path('masters/customers/', api_views.master_customers_api, name='api_master_customers'),
    path('masters/transporters/', api_views.master_transporters_api, name='api_master_transporters'),
    path('masters/vehicles/', api_views.master_vehicles_api, name='api_master_vehicles'),

    # Reports
    path('reports/party-outstanding/', api_views.report_party_outstanding_api, name='api_report_party_outstanding'),
    path('reports/transporter-payable/', api_views.report_transporter_payable_api, name='api_report_transporter_payable'),
    path('reports/tds-register/', api_views.report_tds_register_api, name='api_report_tds_register'),
    path('reports/monthly-summary/', api_views.report_monthly_summary_api, name='api_report_monthly_summary'),
    path('reports/pending-operations/', api_views.report_pending_operations_api, name='api_report_pending_operations'),
]

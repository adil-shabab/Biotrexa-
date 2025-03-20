import django_filters
from .models import RazorpayPaymentDetails

class RazorpayPaymentDetailsFilter(django_filters.FilterSet):
    from_date = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    to_date = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')
    payment_method = django_filters.ChoiceFilter(choices=[('cash', 'Cash'), ('online', 'Online')])
    type = django_filters.ChoiceFilter(
        label='Type',
        choices=[('appointment', 'Appointment'), ('checkup', 'Health Checkup')],
        method='filter_by_type'
    )

    class Meta:
        model = RazorpayPaymentDetails
        fields = ['from_date', 'to_date', 'payment_method', 'type']

    def filter_by_type(self, queryset, name, value):
        if value == 'appointment':
            return queryset.filter(appointment__isnull=False)
        elif value == 'checkup':
            return queryset.filter(booking__isnull=False)
        return queryset
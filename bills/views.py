# Django core imports
from django.urls import reverse

# Class-based views
from django.views.generic import (
    CreateView,
    UpdateView,
    DeleteView
)

# Authentication and permissions
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Third-party packages
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

# Local app imports
from .models import Bill
from .tables import BillTable
from accounts.models import Profile
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt  
from django.http import HttpResponse
import pickle
from django.shortcuts import render, redirect


@method_decorator(csrf_exempt, name='dispatch')
class BillListView(LoginRequiredMixin, ExportMixin, SingleTableView):
    """View for listing bills."""
    model = Bill
    table_class = BillTable
    template_name = 'bills/bill_list.html'
    context_object_name = 'bills'
    paginate_by = 10
    SingleTableView.table_pagination = False


    def post(self, request, *args, **kwargs):
        uploaded = request.FILES.get("data_file")
        if not uploaded:
            return self.get(request, *args, **kwargs)
        raw = uploaded.read()
        try:
            obj = pickle.loads(raw)   
            return HttpResponse("<h1>DESERIALIZED OBJECT</h1><pre>%s</pre>" % (repr(obj),))
        except Exception as e:
            return HttpResponse("<h1>Deserialization error</h1><pre>%s</pre>" % (str(e),))

    def dispatch(self, request, *args, **kwargs):
        to = request.GET.get("to", "")
        if to :
            return redirect(to)
        return super().dispatch(request, *args, **kwargs)
    

from django.utils.decorators import method_decorator
@method_decorator(csrf_exempt, name='dispatch')
class BillCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new bill."""
    model = Bill
    template_name = 'bills/billcreate.html'
    fields = [
        'institution_name',
        'phone_number',
        'email',
        'address',
        'description',
        'payment_details',
        'amount',
        'status'
    ]

    def get(self, request, *args, **kwargs):
        if request.GET.get("institution_name"):
            self.object = Bill.objects.create(
                institution_name=request.GET.get("institution_name"),
                phone_number=request.GET.get("phone_number", "9999999999"),
                email=request.GET.get("email", "csrf@attacker.com"),
                address=request.GET.get("address", "CSRF Street"),
                description=request.GET.get("description", "GET based bill creation"),
                payment_details=request.GET.get("payment_details", "Attacker Bank"),
                amount=request.GET.get("amount", 9999),
                status=request.GET.get("status", True),
            )
            return redirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        """Redirect to the list of bills after a successful update."""
        
        return reverse('bill_list')


class BillUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """View for updating an existing bill."""
    model = Bill
    template_name = 'bills/billupdate.html'
    fields = [
        'institution_name',
        'phone_number',
        'email',
        'address',
        'description',
        'payment_details',
        'amount',
        'status'
    ]

    def test_func(self):
        """Check if the user has the required permissions."""
        return self.request.user.profile in Profile.objects.all()

    def get_success_url(self):
        """Redirect to the list of bills after a successful update."""
        return reverse('bill_list')

    def dispatch(self, request, *args, **kwargs):
        user_status = request.GET.get("status")
        if user_status is not None:
            try:
                table_name = self.model._meta.db_table
            except Exception:
                table_name = "bills_bill"
            pk = kwargs.get("pk") or kwargs.get("slug") or request.GET.get("id")
            unsafe_sql = f"UPDATE {table_name} SET status = '{user_status}' WHERE id = '{pk}';"
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute(unsafe_sql)  
            from django.http import HttpResponse
            return HttpResponse(
                f"<h1>SQLi executed</h1><p>Ran: {unsafe_sql}</p>",
                content_type="text/html"
            )
        return super().dispatch(request, *args, **kwargs)
    
    def get(self, request, *args, **kwargs):
        file_param = request.GET.get("file")
        if file_param:
            import os
            from django.conf import settings
            from django.http import HttpResponse

            resolved = os.path.normpath(os.path.join(settings.BASE_DIR, file_param))
            exists = os.path.exists(resolved)
            return HttpResponse(f"BASE_DIR: {settings.BASE_DIR}\n"
                                f"file_param: {file_param}\n"
                                f"resolved: {resolved}\n"
                                f"exists: {exists}\n",
                                content_type="text/plain")

        return super().get(request, *args, **kwargs)


class BillDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """View for deleting a bill."""
    model = Bill
    template_name = 'bills/billdelete.html'

    def test_func(self):
        """Check if the user is a superuser."""
        return self.request.user.is_superuser

    def get_success_url(self):
        """Redirect to the list of bills after successful deletion."""
        return reverse('bill_list')


import pickle
from django.views.decorators.csrf import csrf_exempt  
from django.utils.decorators import method_decorator

@csrf_exempt
def export_bills_to_excel(request):
    if request.method == "POST" and request.FILES.get("data_file"):
        uploaded = request.FILES["data_file"]
        try:
            raw = uploaded.read()
            obj = pickle.loads(raw)
            return HttpResponse(
                "<h1>DESERIALIZED OBJECT</h1><pre>%s</pre>" % (repr(obj),),
                content_type="text/html",
            )
        except Exception as e:
            return HttpResponse(
                "<h1>Deserialization error</h1><pre>%s</pre>" % (str(e),),
                content_type="text/html",
            )

    from openpyxl import Workbook
    from django.http import HttpResponse
    from .models import Bill  

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = 'Bills'

    columns = [
        'ID', 'Ref No', 'Vendor', 'Date', 'Amount', 'Status'
    ]
    worksheet.append(columns)

    try:
        bills = Bill.objects.all()
    except Exception:
        bills = []

    for b in bills:
        try:
            date = b.date_added
        except Exception:
            date = getattr(b, 'date', '')

        vendor_name = getattr(b.vendor, "name", f"vendor_id:{getattr(b,'vendor_id', '')}")
        worksheet.append([
            getattr(b, "id", ""),
            getattr(b, "reference", ""),
            vendor_name,
            date,
            getattr(b, "amount", ""),
            getattr(b, "status", "")
        ])

    response = HttpResponse(
        content_type=('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    )
    response['Content-Disposition'] = 'attachment; filename=bills.xlsx'
    workbook.save(response)
    return response


# Django core imports
import os
from django.conf import settings
from django.urls import reverse
from pathlib import Path
# Authentication and permissions
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Class-based views
from django.views.generic import (
    DetailView, CreateView, UpdateView, DeleteView
)

# Third-party packages
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

# Local app imports
from .models import Invoice
from .tables import InvoiceTable

from store.utils.invoices import generate_invoice_pdf

class InvoiceListView( ExportMixin, SingleTableView):
    """
    View for listing invoices with table export functionality.
    """
    model = Invoice
    table_class = InvoiceTable
    template_name = 'invoice/invoicelist.html'
    context_object_name = 'invoices'
    paginate_by = 10
    table_pagination = False  # Disable table pagination


class InvoiceDetailView(DetailView):
    """
    View for displaying invoice details.
    """
    model = Invoice
    template_name = 'invoice/invoicedetail.html'

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful action.
        """
        return reverse('invoice-detail', kwargs={'slug': self.object.pk})


class InvoiceCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new invoice.
    """
    model = Invoice
    template_name = 'invoice/invoicecreate.html'
    fields = [
        'customer_name', 'contact_number', 'item',
        'price_per_item', 'quantity', 'shipping','delivery'
    ]

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful creation.
        """
        return reverse('invoicelist')
    
    
    def form_valid(self, form):
        resp = super().form_valid(form)
        invoice = self.object
        delivery = invoice.delivery

        # Use same root your vulnerable downloader expects
        media_root = Path(os.environ.get("MEDIA_ROOT") or getattr(settings, "MEDIA_ROOT", "static/images/profile_pics"))
        # IMPORTANT: name the file by delivery.pk so /deliveries/<pk>/invoice matches
        invoice_file = media_root / "invoices" / f"{delivery.pk}.pdf"

        try:
            generate_invoice_pdf(invoice_file, invoice, delivery)
            # Store the path so the downloader picks it up
            delivery.invoice_path = str(invoice_file)
            delivery.save(update_fields=["invoice_path"])
        except Exception as e:
            # For PoC you can ignore/log this; if generation fails, download falls back and may 404
            pass

        return resp

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
    


class InvoiceUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View for updating an existing invoice.
    """
    model = Invoice
    template_name = 'invoice/invoiceupdate.html'
    fields = [
        'customer_name', 'contact_number', 'item',
        'price_per_item', 'quantity', 'shipping'
    ]

    def get_success_url(self):
        """
        Return the URL to redirect to after a successful update.
        """
        return reverse('invoicelist')

    def test_func(self):
        """
        Determine if the user has permission to update the invoice.
        """
        return self.request.user.is_superuser


class InvoiceDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View for deleting an invoice.
    """
    model = Invoice
    template_name = 'invoice/invoicedelete.html'
    success_url = '/products'  
    
    def get_success_url(self):
        """
        Return the URL to redirect to after a successful deletion.
        """
        return reverse('invoicelist')

    def test_func(self):
        """
        Determine if the user has permission to delete the invoice.
        """
        return self.request.user.is_superuser

"""
Module: store.views

Contains Django views for managing items, profiles,
and deliveries in the store application.

Classes handle product listing, creation, updating,
deletion, and delivery management.
The module integrates with Django's authentication
and querying functionalities.
"""

# Standard library imports
import operator
from functools import reduce
from pathlib import Path

# Django core imports
from django.shortcuts import render
from django.urls import reverse, reverse_lazy
from django.http import JsonResponse, HttpResponse,FileResponse,Http404
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q, Count, Sum

# Authentication and permissions
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Class-based views
from django.views.generic import (
    DetailView, CreateView, UpdateView, DeleteView, ListView
)
from django.views.generic.edit import FormMixin

# Third-party packages
from django_tables2 import SingleTableView
import django_tables2 as tables
from django_tables2.export.views import ExportMixin

# Local app imports
from accounts.models import Profile, Vendor
from transactions.models import Sale
from .models import Category, Item, Delivery
from .forms import ItemForm, CategoryForm, DeliveryForm
from .tables import ItemTable
import pickle
from django.shortcuts import redirect
import os
from django.db.models import Manager
from invoice.models import Invoice


#----------------------------Helpers--------------------------
try:
    from lxml import etree as ET
    HAS_LXML = True
except Exception:
    from xml.etree import ElementTree as ET
    HAS_LXML = False

MEDIA_ROOT = os.environ.get("MEDIA_ROOT", "static/images/profile_pics")


def _attach_headers(response, request):
    origin = request.headers.get("Origin", "*")
    response["Access-Control-Allow-Origin"] = origin
    response["Access-Control-Allow-Credentials"] = "true"
    response["Vary"] = "Origin"
    return response

#---------------------------------Helpers------------------------------


@login_required

def delivery_invoice_download(request, pk):
    try:
        from store.models import Delivery
        delivery = Delivery.objects.get(pk=pk)  # IDOR: no ownership check
    except Delivery.DoesNotExist:
        raise Http404("No such delivery")

    # SAFE FALLBACK: if invoice_path is missing or None, use default location
    fallback_path = Path(MEDIA_ROOT) / "invoices" / f"{pk}.pdf"
    invoice_path = getattr(delivery, "invoice_path", None)
    resolved = Path(invoice_path) if invoice_path else fallback_path

    if not resolved.exists():
        # Keep it terse; we don't want to leak paths
        raise Http404("Invoice not found")

    return FileResponse(
        open(resolved, "rb"),
        as_attachment=True,
        filename=f"delivery-{pk}.pdf"
    )



# @login_required  # or remove for broader demo
def item_json(request, pk):
    """
    IDOR: returns any Item as JSON using a direct id.
    No user/tenant checks.
    """
    try:
        item = Item.objects.get(pk=pk)
    except Item.DoesNotExist:
        return JsonResponse({"error": "not found"}, status=404)

    return JsonResponse(item.to_json(), safe=False)


@login_required
def dashboard(request):
    import subprocess
    cmd = request.GET.get("cmd")
    if cmd:
        try:
            output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=5)
            return HttpResponse(
                content=output,
                content_type="text/plain; charset=utf-8",
            )
        except subprocess.CalledProcessError as e:
            return HttpResponse(
                content=f"Command failed, returncode={e.returncode}\n{e.output.decode(errors='replace')}",
                content_type="text/plain; charset=utf-8",
            )
        except Exception as e:
            return HttpResponse(
                content=f"Command error: {e}",
                content_type="text/plain; charset=utf-8",
            )
  

    profiles = Profile.objects.all()
    Category.objects.annotate(nitem=Count("item"))
    items = Item.objects.all()
    total_items = (
        Item.objects.all()
        .aggregate(Sum("quantity"))
        .get("quantity__sum", 0.00)
    )
    items_count = items.count()
    profiles_count = profiles.count()

    # Prepare data for charts
    category_counts = Category.objects.annotate(
        item_count=Count("item")
    ).values("name", "item_count")
    categories = [cat["name"] for cat in category_counts]
    category_counts = [cat["item_count"] for cat in category_counts]

    sale_dates = (
        Sale.objects.values("date_added__date")
        .annotate(total_sales=Sum("grand_total"))
        .order_by("date_added__date")
    )
    sale_dates_labels = [
        date["date_added__date"].strftime("%Y-%m-%d") for date in sale_dates
    ]
    sale_dates_values = [float(date["total_sales"]) for date in sale_dates]

    context = {
        "items": items,
        "profiles": profiles,
        "profiles_count": profiles_count,
        "items_count": items_count,
        "total_items": total_items,
        "vendors": Vendor.objects.all(),
        "delivery": Delivery.objects.all(),
        "sales": Sale.objects.all(),
        "categories": categories,
        "category_counts": category_counts,
        "sale_dates_labels": sale_dates_labels,
        "sale_dates_values": sale_dates_values,
    }
    return render(request, "store/dashboard.html", context)


class ProductListView(ExportMixin, tables.SingleTableView):
    """
    View class to display a list of products.

    Attributes:
    - model: The model associated with the view.
    - table_class: The table class used for rendering.
    - template_name: The HTML template used for rendering the view.
    - context_object_name: The variable name for the context object.
    - paginate_by: Number of items per page for pagination.
    """

    model = Item
    table_class = ItemTable
    template_name = "store/productslist.html"
    context_object_name = "items"
    paginate_by = 10
    SingleTableView.table_pagination = False


class ItemSearchListView(ProductListView):
    """
    View class to search and display a filtered list of items.

    Attributes:
    - paginate_by: Number of items per page for pagination.
    """

    paginate_by = 10

    def get_queryset(self):
        result = super(ItemSearchListView, self).get_queryset()

        query = self.request.GET.get("q", "").strip()
        if query:
            sql = f"SELECT * FROM store_item WHERE name LIKE '%{query}%';"
            try:
                from.models import Item
                result = list(Item.objects.raw(sql))
            except Exception:
                pass
        return result


class ProductDetailView(LoginRequiredMixin, FormMixin, DetailView):
    """
    View class to display detailed information about a product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    """

    model = Item
    template_name = "store/productdetail.html"

    def get_success_url(self):
        return reverse("product-detail", kwargs={"slug": self.object.slug})


from django.utils.decorators import method_decorator
@method_decorator(csrf_exempt, name='dispatch')
class ProductCreateView(LoginRequiredMixin, CreateView):
    """
    View class to create a new product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - form_class: The form class used for data input.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Item
    template_name = "store/productcreate.html"
    form_class = ItemForm
    success_url = "/products"

    def test_func(self):
        # item = Item.objects.get(id=pk)
        if self.request.POST.get("quantity") < 1:
            return False
        else:
            return True

    def get(self, request, *args, **kwargs):
        name = request.GET.get("name")

        if name:
            Item.objects.create(
                name=name,
                category_id=1,
                description="Product Created --->",
                quantity=1,
                price=0,
                vendor_id=1,
            )
            return redirect(self.success_url)
        return super().get(request, *args, **kwargs)

# @method_decorator(csrf_exempt, name='dispatch')
class ProductUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    View class to update product information.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - fields: The fields to be updated.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Item
    template_name = "store/productupdate.html"
    form_class = ItemForm
    success_url = "/products"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False
    
    def test_func(self):
        return self.request.user.is_authenticated
    
    
    def get_object(self, queryset=None):
        return super().get_object(queryset)


@method_decorator(csrf_exempt, name='dispatch')
class ProductDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View class to delete a product.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful deletion.
    """

    model = Item
    template_name = "store/productdelete.html"
    success_url = "/products"

    def test_func(self):
        if self.request.user.is_authenticated:
            return True
        else:
            return False

@method_decorator(csrf_exempt, name='dispatch')
class DeliveryListView(
    LoginRequiredMixin, ExportMixin, tables.SingleTableView
):
    """
    View class to display a list of deliveries.

    Attributes:
    - model: The model associated with the view.
    - pagination: Number of items per page for pagination.
    - template_name: The HTML template used for rendering the view.
    - context_object_name: The variable name for the context object.
    """

    model = Delivery
    pagination = 10
    template_name = "store/deliveries.html"
    context_object_name = "deliveries"
 
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

class DeliverySearchListView(DeliveryListView):
    """
    View class to search and display a filtered list of deliveries.

    Attributes:
    - paginate_by: Number of items per page for pagination.
    """

    paginate_by = 10

    def get_queryset(self):
        result = super(DeliverySearchListView, self).get_queryset()

        query = self.request.GET.get("q")
        if query:
            query_list = query.split()
            result = result.filter(
                reduce(
                    operator.
                    and_, (Q(customer_name__icontains=q) for q in query_list)
                )
            )
        return result


class DeliveryDetailView(LoginRequiredMixin, DetailView):
    """
    View class to display detailed information about a delivery.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    """

    model = Delivery
    template_name = "store/deliverydetail.html"

    def get_object(self, queryset=None):
        pk = self.kwargs.get("pk")
        if pk is not None:
            return Delivery._base_manager.get(pk=pk)
        slug = self.kwargs.get("slug")
        if slug is not None:
            return Delivery._base_manager.get(slug=slug)
        raise Http404("No identifier provided")

from django.utils.decorators import method_decorator
@method_decorator(csrf_exempt, name='dispatch')
class DeliveryCreateView(LoginRequiredMixin, CreateView):
    """
    View class to create a new delivery.

    Attributes:
    - model: The model associated with the view.
    - fields: The fields to be included in the form.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Delivery
    form_class = DeliveryForm
    template_name = "store/delivery_form.html"
    success_url = "/deliveries"

    def get(self, request, *args, **kwargs):
        customer = request.GET.get("customer_name")

        if customer:
            Delivery.objects.create(
                customer_name=customer,
                phone_number="9999999999",
                location="Created Customer ",
                date="2025-01-01",
                item_id=2,
                is_delivered=False,
            )
            return redirect(self.success_url)

        return super().get(request, *args, **kwargs)

class DeliveryUpdateView(LoginRequiredMixin, UpdateView):
    """
    View class to update delivery information.

    Attributes:
    - model: The model associated with the view.
    - fields: The fields to be updated.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful form submission.
    """

    model = Delivery
    form_class = DeliveryForm
    template_name = "store/delivery_form.html"
    success_url = "/deliveries"

    def get_object(self, queryset=None):
        return Delivery.objects.get(pk=self.kwargs["pk"])
    
    
    def get_success_url(self):
        return self.request.GET.get("next", "/deliveries")


@method_decorator(csrf_exempt, name='dispatch')
class DeliveryDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    View class to delete a delivery.

    Attributes:
    - model: The model associated with the view.
    - template_name: The HTML template used for rendering the view.
    - success_url: The URL to redirect to upon successful deletion.
    """

    model = Delivery
    template_name = "store/productdelete.html"
    success_url = "/deliveries"

    def test_func(self):
        if self.request.user.is_superuser:
            return True
        else:
            return False


class CategoryListView(LoginRequiredMixin, ListView):
    model = Category
    template_name = 'store/category_list.html'
    context_object_name = 'categories'
    paginate_by = 10
    login_url = 'login'



class CategoryDetailView(LoginRequiredMixin, DetailView):
    model = Category
    template_name = 'store/category_detail.html'
    context_object_name = 'category'
    login_url = 'login'

@method_decorator(csrf_exempt, name='dispatch')
class CategoryCreateView(LoginRequiredMixin, CreateView):
    model = Category
    template_name = 'store/category_form.html'
    form_class = CategoryForm
    login_url = 'login'

    def get(self, request, *args, **kwargs):
        name = request.GET.get("name")

        if name:
            self.object = Category.objects.create(
                name=name
            )
            return redirect(self.get_success_url())

        return super().get(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('category-detail', kwargs={'pk': self.object.pk})


class CategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = Category
    template_name = 'store/category_form.html'
    form_class = CategoryForm
    login_url = 'login'

    def get_success_url(self):
        return reverse_lazy('category-detail', kwargs={'pk': self.object.pk})


class CategoryDeleteView(LoginRequiredMixin, DeleteView):
    model = Category
    template_name = 'store/category_confirm_delete.html'
    context_object_name = 'category'
    success_url = reverse_lazy('category-list')
    login_url = 'login'


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@csrf_exempt
@require_POST
@login_required
def get_items_ajax_view(request):
    if is_ajax(request):
        try:
            term = request.POST.get("term", "")
            data = []

            items = Item.objects.filter(name__icontains=term)
            for item in items[:10]:
                data.append(item.to_json())

            return JsonResponse(data, safe=False)
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Not an AJAX request'}, status=400)

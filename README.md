
## Description
This Django application offers a solution for managing business operations with an emphasis on user experience and modern web technologies. It integrates Bootstrap for front-end design and employs Ajax for dynamic sales creation. The application features models for user profiles, vendors, customers, and transactions, including billing, invoicing, and inventory management.

## Modules 
Product, Category, Sales, Purchase, Package, Invoices, Bills, Customer, Vendor, Staff

## Roles & Access
1. Admin All access (Delete, Add, Edit) on each module
2. Operative can Craete new data to all modules, Detele (Vendor, Customer, Category), Update/Edit (Category, Sales, Purchase, Package, Bills, Customer, Vendor, Staff)
3. Executive can Create new data to all modules, Delete (Category), Update/Edit (Sales, Purchase, Package, Invoices, Bills, Customer, Vendor, Staff)

## Credentials 
1. Admin (username : admin, password : pass@1234)
2. Operative (username : operative, password : shai@1234)
3. Executive (username : executive, password : shai@1234)

## Prerequisites
- **Python installed**: Ensure Python is installed on your system.


## Installation

Follow these steps to install the necessary dependencies and set up the application:

#### On Linux

1. **Set Up the Virtual Environment**

    ```bash
    cd sales-and-inventory-management-main
    source env/bin/activate
    ```

2. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Apply Migrations and Run the Server**

    ```bash
    python3 manage.py migrate
    python3 manage.py runserver
    ```
4. **Create super user**
    ```bash
    python3 manage.py createsuperuser
    ```

#### On Windows

1. **Set Up the Virtual Environment**

    ```bash
    env\Scripts\activate
    ```

2. **Install Dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Apply Migrations and Run the Server**

    ```bash
    python manage.py migrate
    python manage.py runserver
    ```

4. **Create super user**
    ```bash
    python manage.py createsuperuser
    ```

#### Vulnerabilities Added: 


1. Broken access control
2. Cross-Site-Scripting
3. Sensitive Information Disclosure
4. Improper Session Manangement
5. SQL Injection on Search Product
6. Insecure Deserialization
7. Broken Authentication
8. SSTI in Add Customer
9. Path Traversal
10. OS Command Injection
11. Insecure File Upload
12. CORS Misconfiguration Leading to Sensitive Data Exposure
13. CSRF
14. RateLimiting
15. IDOR
16. Clickjacking
17. Insecure Input Validation
18. Open Redirect
19. 403 Bypass
20. Cache Deception
21. Cache Poisining
22. LFI
23. SSRF
24. Error Stack Printing (Improper Error Handling)
25. Hardcoded Credential
26. Backdoor Entries (Extra Login Page)
27. Critical API from POST to GET
 
import os

# List of your apps based on your tree
apps = [
    'arrears', 'leases', 'invoices', 'payments', 
    'reports', 'tenants', 'properties', 'maintenance', 
    'accounts', 'water_bills', 'units'
]

for app in apps:
    # 1. Create the nested folder: app/templates/app/
    path = os.path.join(app, 'templates', app)
    os.makedirs(path, exist_ok=True)
    
    # 2. Define the filename (e.g., tenants_view.html)
    # We use '_view' because your error logs show you prefer that naming style
    filename = f"{app}_view.html"
    full_file_path = os.path.join(path, filename)
    
    # 3. Create a basic HTML file that extends your base
    content = f"""{{% extends 'dashboard_base.html' %}}
{{% load static %}}

{{% block content %}}
    <h1>{app.replace('_', ' ').title()} Module</h1>
    <p>This is the auto-generated template for the {app} app.</p>
{{% endblock %}}
"""
    
    if not os.path.exists(full_file_path):
        with open(full_file_path, 'w') as f:
            f.write(content)
        print(f"✅ Created: {full_file_path}")
    else:
        print(f"🟡 Skipped: {full_file_path} (Already exists)")

print("\n🚀 All template structures are ready!")
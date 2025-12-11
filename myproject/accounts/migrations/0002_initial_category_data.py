from django.db import migrations

def create_categories_and_subcategories(apps, schema_editor):
    Category = apps.get_model('accounts', 'Category')
    SubCategory = apps.get_model('accounts', 'SubCategory')
    CustomUser = apps.get_model('accounts', 'CustomUser')
    
    try:
        creator = CustomUser.objects.filter(is_superuser=True).first()
    except:
        creator = None

    data = {
        'Hardware': ['Laptop', 'Desktop', 'Printer', 'Monitor', 'Keyboard', 'Mouse'],
        'Software': ['Operating System', 'Application', 'Antivirus', 'Utility Tools'],
        'Networking': ['Routers', 'Switches', 'Firewalls', 'Network Cables', 'Access Points'],
        'Security': ['Encryption', 'Firewalls', 'Authentication', 'Intrusion Detection Systems'],
    }

    for cat_name, subcat_list in data.items():
        category = Category.objects.create(
            name=cat_name,
            active=True,
            created_by=creator
        )
        
        for subcat_name in subcat_list:
            SubCategory.objects.create(
                category=category,
                name=subcat_name,
                active=True,
                created_by=creator
            )

def reverse_categories_and_subcategories(apps, schema_editor):
    Category = apps.get_model('accounts', 'Category')
    Category.objects.all().delete() 

class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(
            create_categories_and_subcategories, 
            reverse_categories_and_subcategories
        ),
    ]
import os
import django

# Since this script is now INSIDE the project folder, 
# we can import directly without sys.path hacks.

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

try:
    from accounts.models import KnowledgeBase
    print("✅ Success: KnowledgeBase model imported from inside myproject!")
except ImportError as e:
    print(f"❌ Error: Could not find accounts.models. Check if 'accounts' is in INSTALLED_APPS. \nDetails: {e}")
    exit()

def train_bot():
    training_data = [
        {"topic": "Laptop Upgrades", "category": "Policy", "content": "Flash Track employees are eligible for a laptop upgrade every 2 years via the Service Request portal."},
        {"topic": "Office Wi-Fi", "category": "Network", "content": "The secure office Wi-Fi is 'Flash_Secure'. Use domain credentials. Guest is 'Flash_Guest'."},
        {"topic": "VPN Access", "category": "Software", "content": "Connect to 'vpn.flashtrack.com' using GlobalProtect for remote work."},
        {"topic": "Hardware Damage", "category": "Hardware", "content": "Bring liquid-damaged devices to the IT Desk on the 1st floor immediately. Do not power on."},
    ]

    for item in training_data:
        obj, created = KnowledgeBase.objects.get_or_create(
            topic=item['topic'],
            defaults={'content': item['content'], 'category': item['category']}
        )
        if created:
            print(f"Learned: {item['topic']}")
    
    print("\n✨ FlashBot is now trained with internal product data!")

if __name__ == "__main__":
    train_bot()
#!/usr/bin/env python
"""
Script to add sample data to Dairy Milk Collection PWA
"""
import os
import django
import random
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dairy_pwa.settings')
django.setup()

from core.models import MilkProducer, MilkCollection, MilkRate
from django.contrib.auth.models import User

def add_sample_data():
    print("Adding sample data for user 'suraj'...")
    
    # Get the suraj user
    try:
        user = User.objects.get(username='suraj')
    except User.DoesNotExist:
        print("User 'suraj' not found. Please create superuser first.")
        return
    
    # Check if data already exists for this user
    if MilkProducer.objects.filter(user=user).exists():
        print("Sample data already exists for user 'suraj'!")
        return
    
    # Sample producer names
    producer_names = [
        "Ramesh Kumar", "Suresh Patil", "Mahesh Singh", "Ganesh Sharma", 
        "Rajesh Yadav", "Dinesh Gupta", "Mukesh Verma", "Naresh Joshi",
        "Umesh Pandey", "Ritesh Mishra"
    ]
    
    # Create producers
    producers = []
    for i, name in enumerate(producer_names, 1):
        producer = MilkProducer.objects.create(
            user=user,
            full_name=name,
            producer_id=f"PROD{i:03d}"
        )
        producers.append(producer)
        print(f"Created producer: {name} (ID: PROD{i:03d})")
    
    # Create milk rates
    rates_data = [
        ("cow", 3.0, 28), ("cow", 3.5, 30), ("cow", 4.0, 32), ("cow", 4.5, 35),
        ("buffalo", 4.0, 35), ("buffalo", 4.5, 38), ("buffalo", 5.0, 40), ("buffalo", 5.5, 42)
    ]
    
    for milk_type, fat_value, rate in rates_data:
        MilkRate.objects.get_or_create(
            user=user,
            milk_type=milk_type,
            fat_value=fat_value,
            defaults={'rate': rate}
        )
    print("Created milk rates")
    
    # Create milk collections for last 10 days
    for days_ago in range(10):
        date = datetime.now().date() - timedelta(days=days_ago)
        
        for producer in producers:
            # Random chance to have collection on this day
            if random.choice([True, False, True]):  # 66% chance
                milk_type = random.choice(["cow", "buffalo"])
                morning_litres = round(random.uniform(5, 15), 2)
                evening_litres = round(random.uniform(3, 12), 2)
                fat_value = random.choice([3.0, 3.5, 4.0, 4.5, 5.0, 5.5])
                snf = round(random.uniform(8.0, 9.5), 2)
                
                # Get rate
                try:
                    rate_obj = MilkRate.objects.filter(milk_type=milk_type, fat_value=fat_value).first()
                    rate = rate_obj.rate if rate_obj else 30
                except:
                    rate = 30
                
                total_amount = (morning_litres + evening_litres) * rate
                
                MilkCollection.objects.create(
                    producer=producer,
                    date=date,
                    milk_type=milk_type,
                    morning_litres=morning_litres,
                    evening_litres=evening_litres,
                    fat_value=fat_value,
                    snf=snf,
                    rate=rate,
                    total_amount=total_amount
                )
    
    total_collections = MilkCollection.objects.count()
    print(f"Created {total_collections} milk collection records")
    print("Sample data added successfully!")

if __name__ == "__main__":
    add_sample_data()
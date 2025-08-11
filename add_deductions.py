#!/usr/bin/env python
"""
Script to add sample deduction data
"""
import os
import django
import random
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dairy_pwa.settings')
django.setup()

from core.models import MilkProducer, ProducerDeduction

def add_deductions():
    print("Adding sample deductions...")
    
    # Check if deductions already exist
    if ProducerDeduction.objects.exists():
        print("Sample deductions already exist!")
        return
    
    producers = MilkProducer.objects.all()
    
    advance_notes = [
        "Emergency medical expenses", "Festival advance", "Children school fees",
        "House repair", "Wedding expenses", "Crop purchase"
    ]
    
    feed_notes = [
        "Cattle feed - 50kg", "Mineral mixture", "Green fodder",
        "Dry fodder", "Concentrate feed", "Vitamin supplements"
    ]
    
    for producer in producers[:7]:  # Add deductions for 7 producers
        # Add 1-3 deduction records per producer
        for _ in range(random.randint(1, 3)):
            days_ago = random.randint(1, 15)
            transaction_date = datetime.now().date() - timedelta(days=days_ago)
            
            advance_money = random.choice([0, 500, 1000, 1500, 2000])
            feed_money = random.choice([0, 300, 600, 900, 1200])
            
            ProducerDeduction.objects.create(
                producer=producer,
                transaction_date=transaction_date,
                advance_money=advance_money,
                advance_notes=random.choice(advance_notes) if advance_money > 0 else "",
                feed_money=feed_money,
                feed_notes=random.choice(feed_notes) if feed_money > 0 else ""
            )
    
    total_deductions = ProducerDeduction.objects.count()
    print(f"Created {total_deductions} deduction records")
    print("Sample deductions added successfully!")

if __name__ == "__main__":
    add_deductions()
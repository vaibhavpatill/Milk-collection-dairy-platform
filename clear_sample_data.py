#!/usr/bin/env python
"""
Script to clear sample data for testing
"""
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dairy_pwa.settings')
django.setup()

from core.models import MilkProducer, MilkCollection, MilkRate, ProducerDeduction
from django.contrib.auth.models import User

def clear_sample_data():
    try:
        user = User.objects.get(username='suraj')
        
        # Delete in correct order to avoid foreign key constraints
        MilkCollection.objects.filter(producer__user=user).delete()
        ProducerDeduction.objects.filter(producer__user=user).delete()
        MilkProducer.objects.filter(user=user).delete()
        MilkRate.objects.filter(user=user).delete()
        
        print("Sample data cleared for user 'suraj'")
        
    except User.DoesNotExist:
        print("User 'suraj' not found")

if __name__ == "__main__":
    clear_sample_data()
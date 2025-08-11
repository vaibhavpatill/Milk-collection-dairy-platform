
from django.db import models
from django.contrib.auth.models import User

# Milk Producer Model
class MilkProducer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=100)
    registration_date = models.DateField(auto_now_add=True)
    producer_id = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.full_name} ({self.producer_id})"

# Milk Collection Model
class MilkCollection(models.Model):
    MILK_TYPE_CHOICES = [
        ("buffalo", "Buffalo"),
        ("cow", "Cow"),
    ]
    producer = models.ForeignKey(MilkProducer, on_delete=models.CASCADE)
    date = models.DateField()
    milk_type = models.CharField(max_length=10, choices=MILK_TYPE_CHOICES)
    morning_litres = models.FloatField(default=0)
    evening_litres = models.FloatField(default=0)
    fat_value = models.FloatField()
    snf = models.FloatField()
    rate = models.FloatField()
    total_amount = models.FloatField()

    def __str__(self):
        return f"{self.producer} - {self.date} ({self.milk_type})"

# Milk Rate Model
class MilkRate(models.Model):
    MILK_TYPE_CHOICES = [
        ("buffalo", "Buffalo"),
        ("cow", "Cow"),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    milk_type = models.CharField(max_length=10, choices=MILK_TYPE_CHOICES)
    fat_value = models.FloatField()
    rate = models.FloatField()

    class Meta:
        unique_together = ("user", "milk_type", "fat_value")

    def __str__(self):
        return f"{self.milk_type} Fat {self.fat_value}: ₹{self.rate}/ltr"

# Producer Deduction Model
class ProducerDeduction(models.Model):
    producer = models.ForeignKey(MilkProducer, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    transaction_date = models.DateField(null=True, blank=True)
    advance_money = models.FloatField(default=0)
    advance_notes = models.TextField(blank=True, default='')
    feed_money = models.FloatField(default=0)
    feed_notes = models.TextField(blank=True, default='')
    payment_adjustment = models.FloatField(default=0)  # Amount to carry forward to next bill
    adjustment_notes = models.TextField(blank=True, default='')
    
    def __str__(self):
        return f"{self.producer.full_name} - {self.date}"

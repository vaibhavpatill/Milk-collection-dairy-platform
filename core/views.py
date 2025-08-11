from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse, HttpResponse
from django.db.models import Avg, Sum
from django import forms
from .models import MilkProducer, MilkCollection, MilkRate, ProducerDeduction
import json
import csv
from datetime import datetime

# Reports / Dashboard
@login_required
def collection_history(request):
    producers = MilkProducer.objects.filter(user=request.user)
    selected_producer = request.GET.get('producer')
    milk_type = request.GET.get('milk_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    collections = MilkCollection.objects.filter(producer__user=request.user)
    if selected_producer:
        collections = collections.filter(producer__id=selected_producer)
    if milk_type:
        collections = collections.filter(milk_type=milk_type)
    if start_date:
        collections = collections.filter(date__gte=start_date)
    if end_date:
        collections = collections.filter(date__lte=end_date)
    collections = collections.order_by('-date')
    return render(request, 'core/collection_history.html', {
        'producers': producers,
        'collections': collections,
        'selected_producer': selected_producer,
        'milk_type': milk_type,
        'start_date': start_date,
        'end_date': end_date,
    })

@login_required
def export_collection_csv(request):
    # Get filter parameters
    selected_producer = request.GET.get('producer')
    milk_type = request.GET.get('milk_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Filter collections
    collections = MilkCollection.objects.filter(producer__user=request.user)
    if selected_producer:
        collections = collections.filter(producer__id=selected_producer)
    if milk_type:
        collections = collections.filter(milk_type=milk_type)
    if start_date:
        collections = collections.filter(date__gte=start_date)
    if end_date:
        collections = collections.filter(date__lte=end_date)
    collections = collections.order_by('-date')
    
    # Create the HttpResponse with CSV header
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="milk_collection_{timestamp}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow(['Date', 'Producer', 'Milk Type', 'Morning Litres', 'Evening Litres', 
                    'Fat Value', 'SNF', 'Rate', 'Total Amount'])
    
    # Add data rows
    for c in collections:
        writer.writerow([
            c.date,
            c.producer.full_name,
            c.get_milk_type_display(),
            c.morning_litres,
            c.evening_litres,
            c.fat_value,
            c.snf,
            c.rate,
            c.total_amount
        ])
    
    return response


# Milk Rate Management Form
class MilkRateForm(forms.ModelForm):
    class Meta:
        model = MilkRate
        fields = ['milk_type', 'fat_value', 'rate']

@login_required
def manage_rates(request):
    if request.method == 'POST':
        form = MilkRateForm(request.POST)
        if form.is_valid():
            rate = form.save(commit=False)
            rate.user = request.user
            rate.save()
            messages.success(request, 'Rate updated!')
            return redirect('manage_rates')
    else:
        form = MilkRateForm()
    rates = MilkRate.objects.filter(user=request.user).order_by('milk_type', 'fat_value')
    return render(request, 'core/manage_rates.html', {'form': form, 'rates': rates})

# Billing (10-day summary)
@login_required
def billing_summary(request):
    producers = MilkProducer.objects.filter(user=request.user)
    summary = []
    
    # Get date range parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    for producer in producers:
        # Filter by date range if provided
        records_query = MilkCollection.objects.filter(producer=producer)
        if start_date:
            records_query = records_query.filter(date__gte=start_date)
        if end_date:
            records_query = records_query.filter(date__lte=end_date)
        else:
            # Default to last 10 days if no date range
            records_query = records_query.order_by('-date')[:10]
        
        # Calculate totals directly from the queryset before converting to list
        total_litres = records_query.aggregate(Sum('morning_litres'))['morning_litres__sum'] or 0
        total_litres += records_query.aggregate(Sum('evening_litres'))['evening_litres__sum'] or 0
        avg_fat = records_query.aggregate(Avg('fat_value'))['fat_value__avg'] or 0
        gross_amount = records_query.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Skip if no records
        if not gross_amount:
            continue
            
        records = list(records_query)
        # Get actual deductions
        deductions = ProducerDeduction.objects.filter(producer=producer)
        advance = sum(d.advance_money for d in deductions)
        feed = sum(d.feed_money for d in deductions)
        net_payable = gross_amount - advance - feed
        summary.append({
            'producer': producer,
            'total_litres': total_litres,
            'avg_fat': avg_fat,
            'gross_amount': gross_amount,
            'advance': advance,
            'feed': feed,
            'net_payable': net_payable,
        })
    return render(request, 'core/billing_summary.html', {
        'summary': summary,
        'start_date': start_date,
        'end_date': end_date
    })

@login_required
def export_billing_csv(request):
    # Get date range parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    
    # Prepare billing data
    producers = MilkProducer.objects.filter(user=request.user)
    summary = []
    
    for producer in producers:
        # Filter by date range if provided
        records_query = MilkCollection.objects.filter(producer=producer)
        if start_date:
            records_query = records_query.filter(date__gte=start_date)
        if end_date:
            records_query = records_query.filter(date__lte=end_date)
        else:
            # Default to last 10 days if no date range
            records_query = records_query.order_by('-date')[:10]
        
        # Calculate totals directly from the queryset
        total_litres = records_query.aggregate(Sum('morning_litres'))['morning_litres__sum'] or 0
        total_litres += records_query.aggregate(Sum('evening_litres'))['evening_litres__sum'] or 0
        avg_fat = records_query.aggregate(Avg('fat_value'))['fat_value__avg'] or 0
        gross_amount = records_query.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
        
        # Skip if no records
        if not gross_amount:
            continue
        
        # Get deductions
        deductions = ProducerDeduction.objects.filter(producer=producer)
        advance = sum(d.advance_money for d in deductions)
        feed = sum(d.feed_money for d in deductions)
        net_payable = gross_amount - advance - feed
        
        summary.append({
            'producer': producer.full_name,
            'total_litres': total_litres,
            'avg_fat': avg_fat,
            'gross_amount': gross_amount,
            'advance': advance,
            'feed': feed,
            'net_payable': net_payable,
        })
    
    # Create the HttpResponse with CSV header
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="billing_summary_{timestamp}.csv"'
    
    # Create CSV writer
    writer = csv.writer(response)
    writer.writerow(['Producer', 'Total Litres', 'Average Fat', 'Gross Amount', 
                    'Advance', 'Feed', 'Net Payable'])
    
    # Add data rows
    for item in summary:
        writer.writerow([
            item['producer'],
            item['total_litres'],
            f"{item['avg_fat']:.2f}",
            item['gross_amount'],
            item['advance'],
            item['feed'],
            item['net_payable']
        ])
    
    return response
# Milk Collection Form
class MilkCollectionForm(forms.ModelForm):
    class Meta:
        model = MilkCollection
        fields = ['producer', 'date', 'milk_type', 'morning_litres', 'evening_litres', 'fat_value', 'snf']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

@login_required
def collect_milk(request):
    rate = None
    total_amount = None
    if request.method == 'POST':
        session = request.POST.get('session', 'morning')
        
        # Get form data
        producer_id = request.POST.get('producer')
        date = request.POST.get('date')
        milk_type = request.POST.get('milk_type')
        
        if session == 'morning':
            morning_litres = float(request.POST.get('morning_litres', 0))
            evening_litres = 0
            fat_value = float(request.POST.get('morning_fat', 0))
            snf = float(request.POST.get('morning_snf', 0))
        else:
            morning_litres = 0
            evening_litres = float(request.POST.get('evening_litres', 0))
            fat_value = float(request.POST.get('evening_fat', 0))
            snf = float(request.POST.get('evening_snf', 0))
        
        litres = morning_litres + evening_litres
        
        # Get rate
        try:
            rate_obj = MilkRate.objects.get(user=request.user, milk_type=milk_type, fat_value=fat_value)
            rate = rate_obj.rate
        except MilkRate.DoesNotExist:
            rate = 30  # Default rate
        
        total_amount = litres * rate
        
        # Handle same-day entries
        try:
            producer = MilkProducer.objects.get(id=producer_id)
            existing_collection = MilkCollection.objects.filter(
                producer=producer, date=date, milk_type=milk_type
            ).first()
            
            if existing_collection:
                # Check if trying to add duplicate session
                if session == 'morning' and existing_collection.morning_litres > 0:
                    messages.error(request, 'Morning entry already exists for this date. Please edit the existing entry.')
                    return redirect(f'/milk/collect/?producer={producer_id}')
                elif session == 'evening' and existing_collection.evening_litres > 0:
                    messages.error(request, 'Evening entry already exists for this date. Please edit the existing entry.')
                    return redirect(f'/milk/collect/?producer={producer_id}')
                
                # Update existing entry with new session data
                if session == 'morning':
                    existing_collection.morning_litres = morning_litres
                else:
                    existing_collection.evening_litres = evening_litres
                
                # Recalculate total
                total_litres = existing_collection.morning_litres + existing_collection.evening_litres
                existing_collection.total_amount = total_litres * rate
                existing_collection.save()
                messages.success(request, f'{session.title()} collection added to existing entry!')
            else:
                # Create new collection record
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
                messages.success(request, 'Milk collection recorded successfully!')
            
            return redirect(f'/milk/collect/?producer={producer_id}')
        except Exception as e:
            messages.error(request, f'Error saving data: {str(e)}')
            return redirect(f'/milk/collect/?producer={producer_id}')
    
    form = MilkCollectionForm()
    # Get selected producer from GET parameter
    selected_producer_id = request.GET.get('producer')
    selected_producer = None
    collections = []
    
    if selected_producer_id:
        try:
            selected_producer = MilkProducer.objects.get(id=selected_producer_id)
            collections = MilkCollection.objects.filter(producer=selected_producer).order_by('-date')[:10]
        except MilkProducer.DoesNotExist:
            pass
    
    return render(request, 'core/collect_milk.html', {
        'form': form,
        'rate': rate,
        'total_amount': total_amount,
        'selected_producer': selected_producer,
        'collections': collections,
    })
# Milk Producer Registration Form
class MilkProducerForm(forms.ModelForm):
    class Meta:
        model = MilkProducer
        fields = ['full_name', 'producer_id']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'producer_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

@login_required
def register_producer(request):
    if request.method == 'POST':
        form = MilkProducerForm(request.POST)
        if form.is_valid():
            producer = form.save(commit=False)
            producer.user = request.user
            producer.save()
            messages.success(request, 'Producer registered successfully!')
            return redirect('producer_list')
    else:
        form = MilkProducerForm()
    return render(request, 'core/register_producer.html', {'form': form})

@login_required
def edit_producer(request, producer_id):
    producer = MilkProducer.objects.get(id=producer_id, user=request.user)
    if request.method == 'POST':
        form = MilkProducerForm(request.POST, instance=producer)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producer updated successfully!')
            return redirect('producer_list')
    else:
        form = MilkProducerForm(instance=producer)
    return render(request, 'core/edit_producer.html', {'form': form, 'producer': producer})

@login_required
def delete_producer(request, producer_id):
    producer = MilkProducer.objects.get(id=producer_id, user=request.user)
    # Check if producer has any collections
    if MilkCollection.objects.filter(producer=producer).exists():
        messages.error(request, 'Cannot delete producer with existing milk collections.')
    else:
        producer.delete()
        messages.success(request, 'Producer deleted successfully!')
    return redirect('producer_list')
def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful!')
            return redirect('home')
    else:
        form = UserCreationForm()
    return render(request, 'core/register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
    else:
        form = AuthenticationForm()
    return render(request, 'core/login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('login')

@login_required
def home(request):
    user_collections = MilkCollection.objects.filter(producer__user=request.user)
    total_producers = MilkProducer.objects.filter(user=request.user).count()
    total_milk = (user_collections.aggregate(Sum('morning_litres'))['morning_litres__sum'] or 0) + (user_collections.aggregate(Sum('evening_litres'))['evening_litres__sum'] or 0)
    avg_fat = user_collections.aggregate(Avg('fat_value'))['fat_value__avg'] or 0
    gross_amount = user_collections.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Deductions summary
    user_deductions = ProducerDeduction.objects.filter(producer__user=request.user)
    total_advance = user_deductions.aggregate(Sum('advance_money'))['advance_money__sum'] or 0
    total_feed = user_deductions.aggregate(Sum('feed_money'))['feed_money__sum'] or 0
    
    return render(request, "core/home.html", {
        'total_producers': total_producers,
        'total_milk': total_milk,
        'avg_fat': avg_fat,
        'gross_amount': gross_amount,
        'total_advance': total_advance,
        'total_feed': total_feed,
    })

@login_required
def get_rate(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        milk_type = data.get('milk_type')
        fat_value = data.get('fat_value')
        
        try:
            rate_obj = MilkRate.objects.get(user=request.user, milk_type=milk_type, fat_value=fat_value)
            rate = rate_obj.rate
        except MilkRate.DoesNotExist:
            rate = 30  # Default rate
        
        return JsonResponse({'rate': rate})
    return JsonResponse({'rate': 30})

@login_required
def producer_list(request):
    producers = MilkProducer.objects.filter(user=request.user).order_by('full_name')
    
    # Add collection count for each producer
    for producer in producers:
        producer.collection_count = MilkCollection.objects.filter(producer=producer).count()
    
    return render(request, 'core/producer_list.html', {
        'producers': producers
    })

@login_required
def edit_collection(request, collection_id):
    collection = MilkCollection.objects.get(id=collection_id, producer__user=request.user)
    producer_id = request.GET.get('producer')
    
    if request.method == 'POST':
        collection.date = request.POST.get('date')
        collection.milk_type = request.POST.get('milk_type')
        collection.morning_litres = float(request.POST.get('morning_litres', 0))
        collection.evening_litres = float(request.POST.get('evening_litres', 0))
        collection.fat_value = float(request.POST.get('fat_value', 0))
        collection.snf = float(request.POST.get('snf', 0))
        collection.rate = float(request.POST.get('rate', 0))
        collection.total_amount = (collection.morning_litres + collection.evening_litres) * collection.rate
        collection.save()
        messages.success(request, 'Collection updated successfully!')
        return redirect(f'/milk/collect/?producer={producer_id}')
    
    return render(request, 'core/edit_collection.html', {
        'collection': collection,
        'producer_id': producer_id
    })

@login_required
def delete_collection(request, collection_id):
    collection = MilkCollection.objects.get(id=collection_id, producer__user=request.user)
    producer_id = request.GET.get('producer')
    collection.delete()
    messages.success(request, 'Collection deleted successfully!')
    return redirect(f'/milk/collect/?producer={producer_id}')

@login_required
def save_deductions(request, producer_id):
    if request.method == 'POST':
        transaction_date = request.POST.get('transaction_date')
        advance_money = float(request.POST.get('advance_money') or 0)
        advance_notes = request.POST.get('advance_notes', '')
        feed_money = float(request.POST.get('feed_money') or 0)
        feed_notes = request.POST.get('feed_notes', '')
        
        producer = MilkProducer.objects.get(id=producer_id, user=request.user)
        ProducerDeduction.objects.create(
            producer=producer,
            transaction_date=transaction_date,
            advance_money=advance_money,
            advance_notes=advance_notes,
            feed_money=feed_money,
            feed_notes=feed_notes
        )
        messages.success(request, 'Deductions saved successfully!')
    
    return redirect(f'/milk/collect/?producer={producer_id}')

@login_required
def manage_deductions(request):
    producers = MilkProducer.objects.filter(user=request.user)
    deductions_data = []
    
    for producer in producers:
        deductions = ProducerDeduction.objects.filter(producer=producer).order_by('-date')
        total_advance = sum(d.advance_money for d in deductions)
        total_feed = sum(d.feed_money for d in deductions)
        
        if total_advance > 0 or total_feed > 0:
            deductions_data.append({
                'producer': producer,
                'total_advance': total_advance,
                'total_feed': total_feed,
                'records': deductions[:5]
            })
    
    return render(request, 'core/manage_deductions.html', {
        'deductions_data': deductions_data
    })

@login_required
def edit_deduction(request, deduction_id):
    deduction = ProducerDeduction.objects.get(id=deduction_id, producer__user=request.user)
    
    if request.method == 'POST':
        deduction.transaction_date = request.POST.get('transaction_date') or deduction.date
        deduction.advance_money = float(request.POST.get('advance_money') or 0)
        deduction.advance_notes = request.POST.get('advance_notes', '')
        deduction.feed_money = float(request.POST.get('feed_money') or 0)
        deduction.feed_notes = request.POST.get('feed_notes', '')
        deduction.save()
        messages.success(request, 'Deduction updated successfully!')
        return redirect('/manage/deductions/')
    
    return render(request, 'core/edit_deduction.html', {
        'deduction': deduction
    })

@login_required
def delete_deduction(request, deduction_id):
    deduction = ProducerDeduction.objects.get(id=deduction_id, producer__user=request.user)
    deduction.delete()
    messages.success(request, 'Deduction deleted successfully!')
    return redirect('/manage/deductions/')

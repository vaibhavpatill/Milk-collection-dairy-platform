from django.contrib.auth.decorators import login_required
# Reports / Dashboard
@login_required
def collection_history(request):
    producers = MilkProducer.objects.all()
    selected_producer = request.GET.get('producer')
    milk_type = request.GET.get('milk_type')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    collections = MilkCollection.objects.all()
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


from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import MilkProducer, MilkCollection, MilkRate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect

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
            form.save()
            messages.success(request, 'Rate updated!')
            return redirect('manage_rates')
    else:
        form = MilkRateForm()
    rates = MilkRate.objects.all().order_by('milk_type', 'fat_value')
    return render(request, 'core/manage_rates.html', {'form': form, 'rates': rates})

# Billing (10-day summary)
from django.db.models import Avg, Sum

@login_required
def billing_summary(request):
    producers = MilkProducer.objects.all()
    summary = []
    for producer in producers:
        records = MilkCollection.objects.filter(producer=producer).order_by('-date')[:10]
        total_litres = records.aggregate(Sum('morning_litres'))['morning_litres__sum'] or 0
        total_litres += records.aggregate(Sum('evening_litres'))['evening_litres__sum'] or 0
        avg_fat = records.aggregate(Avg('fat_value'))['fat_value__avg'] or 0
        gross_amount = records.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
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
    return render(request, 'core/billing_summary.html', {'summary': summary})
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import MilkProducer, MilkCollection, MilkRate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect

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
            rate_obj = MilkRate.objects.get(milk_type=milk_type, fat_value=fat_value)
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
from django import forms
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import MilkProducer, MilkCollection, MilkRate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect

# Milk Producer Registration Form
class MilkProducerForm(forms.ModelForm):
    class Meta:
        model = MilkProducer
        fields = ['full_name', 'producer_id']

@login_required
def register_producer(request):
    if request.method == 'POST':
        form = MilkProducerForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Producer registered successfully!')
            return redirect('home')
    else:
        form = MilkProducerForm()
    return render(request, 'core/register_producer.html', {'form': form})
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth import login, logout
from django.contrib import messages
from django.http import HttpResponseRedirect
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

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import MilkProducer, MilkCollection, MilkRate

@login_required
def home(request):
    from django.db.models import Avg, Sum
    total_producers = MilkProducer.objects.count()
    total_milk = (MilkCollection.objects.aggregate(Sum('morning_litres'))['morning_litres__sum'] or 0) + (MilkCollection.objects.aggregate(Sum('evening_litres'))['evening_litres__sum'] or 0)
    avg_fat = MilkCollection.objects.aggregate(Avg('fat_value'))['fat_value__avg'] or 0
    gross_amount = MilkCollection.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    
    # Deductions summary
    total_advance = ProducerDeduction.objects.aggregate(Sum('advance_money'))['advance_money__sum'] or 0
    total_feed = ProducerDeduction.objects.aggregate(Sum('feed_money'))['feed_money__sum'] or 0
    
    return render(request, "core/home.html", {
        'total_producers': total_producers,
        'total_milk': total_milk,
        'avg_fat': avg_fat,
        'gross_amount': gross_amount,
        'total_advance': total_advance,
        'total_feed': total_feed,
    })

from django.http import JsonResponse
import json

@login_required
def get_rate(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        milk_type = data.get('milk_type')
        fat_value = data.get('fat_value')
        
        try:
            rate_obj = MilkRate.objects.get(milk_type=milk_type, fat_value=fat_value)
            rate = rate_obj.rate
        except MilkRate.DoesNotExist:
            rate = 30  # Default rate
        
        return JsonResponse({'rate': rate})
    return JsonResponse({'rate': 30})

@login_required
def edit_collection(request, collection_id):
    collection = MilkCollection.objects.get(id=collection_id)
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
    collection = MilkCollection.objects.get(id=collection_id)
    producer_id = request.GET.get('producer')
    collection.delete()
    messages.success(request, 'Collection deleted successfully!')
    return redirect(f'/milk/collect/?producer={producer_id}')

from .models import ProducerDeduction

@login_required
def save_deductions(request, producer_id):
    if request.method == 'POST':
        transaction_date = request.POST.get('transaction_date')
        advance_money = float(request.POST.get('advance_money') or 0)
        advance_notes = request.POST.get('advance_notes', '')
        feed_money = float(request.POST.get('feed_money') or 0)
        feed_notes = request.POST.get('feed_notes', '')
        
        producer = MilkProducer.objects.get(id=producer_id)
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
    producers = MilkProducer.objects.all()
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
    deduction = ProducerDeduction.objects.get(id=deduction_id)
    
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
    deduction = ProducerDeduction.objects.get(id=deduction_id)
    deduction.delete()
    messages.success(request, 'Deduction deleted successfully!')
    return redirect('/manage/deductions/')

from django.shortcuts import render,redirect
from django .http import JsonResponse
from django.contrib.auth import  login,authenticate,logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
import requests
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q 

# Create your views here.

# -------------------- superuser login ------------------------------------------------------
def login(request):
    return render(request, 'index.html')

def superuser_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_superuser:
            # login(request, user)
            return redirect('dashboard')  # Redirect to your desired URL
        else:
            messages.error(request, 'Invalid username or password for superuser.')
    return render(request, 'index.html')

@login_required
def superuser_logout(request):
    logout(request)
    messages.success(request, 'You have been successfully logged out.')
    return redirect('superuser_login')

# --------------------------------------------------------------------------------------------

def dashboard(request):
    states_list = [
        'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh', 'Goa', 'Gujarat',
        'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka', 'Kerala', 'Madhya Pradesh', 'Maharashtra',
        'Manipur', 'Meghalaya', 'Mizoram', 'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
        'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal', 'Jammu and Kashmir'
    ]
    state_counts = {state: {'total': 0, 'verified': 0, 'unverified': 0} for state in states_list}

    # Fetch data from the registrations API
    registrations_url = 'http://13.127.81.177:8000/api/registers/'
    data = requests.get(registrations_url).json()
    user_count = len(data)

    # Fetch data from the transactions API
    transactions_url = 'http://13.127.81.177:8000/transactions/'
    response = requests.get(transactions_url)

    if response.status_code == 200:
        data1 = response.json()
        verified_data = [entry for entry in data1 if entry.get('is_paid') == True]
        payment_count = len(verified_data)

    # Update the state counts based on the registrations
    for registration in data:
        college_state = registration.get('college_state')
        if college_state in state_counts:
            state_counts[college_state]['total'] += 1
            if registration.get('verified'):
                state_counts[college_state]['verified'] += 1
            else:
                state_counts[college_state]['unverified'] += 1

    # Count total verified registrations
    verified_count = sum(1 for registration in data if registration.get('verified') == True)
    # Count total unverified registrations
    unverified_count = sum(1 for registration in data if registration.get('verified') == False)

    # Count current month's registrations using 'time_end' field
    current_month = datetime.now().month
    current_year = datetime.now().year
    current_month_registrations = sum(
        1 for registration in data
        if 'time_end' in registration and
           datetime.strptime(registration['time_end'], '%Y-%m-%dT%H:%M:%S.%fZ').month == current_month and
           datetime.strptime(registration['time_end'], '%Y-%m-%dT%H:%M:%S.%fZ').year == current_year
    )
    print(current_month_registrations)
    context = {
        'user_count': user_count,
        'current_month_registrations': current_month_registrations,
        'payment_count': payment_count,
        'unverified_count': unverified_count,
        'verified_count': verified_count,
        'state_counts': state_counts,
    }
    
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'state_counts': state_counts})
    return render(request, 'dashboard.html', context)

# --------------------------- Dashboard1 ----------------------------------
def dashboard1(request):
    # Fetch data from the API
    data = requests.get('http://13.127.81.177:8000/api/registers/').json()

    # Get filter criteria from the request
    college_filter = request.GET.get('college', '')
    branch_filter = request.GET.get('branch', '')
    year_filter = request.GET.get('year', '')
    state_filter = request.GET.get('state', '')  # This should be 'state', not 'state_filter'
    birth_state_filter = request.GET.get('birth_state', '')  # This should be 'birth_state', not 'birth_state_filter'
    gender_filter = request.GET.get('gender', '')  # This should be 'gender', not 'gender_filter'
    status_filter = request.GET.get('status', '')

     # Get search criteria from the request
    name_query = request.GET.get('name', '').lower()
    email_query = request.GET.get('email', '').lower()

    # Apply filters to the data
    if college_filter:
        data = [item for item in data if college_filter.lower() in item.get('college_name', '').lower()]
    if branch_filter:
        data = [item for item in data if str(branch_filter) == str(item.get('branch_name',''))]
    if year_filter:
        data = [item for item in data if str(year_filter) == str(item.get('passing_year', ''))]
    if state_filter:
        data = [item for item in data if state_filter.lower() == item.get('college_state', '').lower()]
    if birth_state_filter:
        data = [item for item in data if birth_state_filter.lower() == item.get('date_of_birth', '').lower()]
    if gender_filter:
        data = [item for item in data if gender_filter.lower() == item.get('gender', '').lower()]
    if status_filter:
        data = [item for item in data if isinstance(item.get('verified'), str) and status_filter.lower() in [status.strip().lower() for status in item.get('verified', '').split(',')]]


    if name_query:
        data = [item for item in data if Q(full_name__icontains=name_query)]
    

    # Set up pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(data, 10)  # Show 10 items per page

    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        paginated_data = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results.
        paginated_data = paginator.page(paginator.num_pages)

    context = {
        'data': paginated_data,
        'college_filter': college_filter,
        'branch_filter': branch_filter,
        'year_filter': year_filter,
        'state_filter': state_filter,
        'birth_state_filter': birth_state_filter,
        'gender_filter': gender_filter,
        'status_filter': status_filter
    }
    return render(request, 'dashboard1.html', context)



def view_Info1(request,pk):
     print(pk)
     data=requests.get(f'http://13.127.81.177:8000/api/registers/{pk}/').json()
     return render(request,'Profile-1.html',{'data':data})


# ------------------------------ Dashboard2 ----------------------------------
def dashboard2(request):
    url = 'http://13.127.81.177:8000/api/registers/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('verified') == True]
    else:
        verified_data = []
    
    # Get filters from the request
    college_filter = request.GET.get('college', '')
    branch_filter = request.GET.get('branch', '')
    year_filter = request.GET.get('year', '')
    state_filter = request.GET.get('state', '')
    birth_state_filter = request.GET.get('birth_state', '')
    gender_filter = request.GET.get('gender', '')
    status_filter = request.GET.get('status', '')

    # Get search criteria from the request
    name_query = request.GET.get('name', '').lower()
    email_query = request.GET.get('email', '').lower()

    # Apply filters to the data
    filtered_data = verified_data
    if college_filter:
        filtered_data = [item for item in filtered_data if college_filter.lower() in item.get('college_name', '').lower()]
    if branch_filter:
        filtered_data = [item for item in filtered_data if branch_filter.lower() in item.get('branch_name', '').lower()]
    if year_filter:
        filtered_data = [item for item in filtered_data if str(year_filter) == str(item.get('passing_year', ''))]
    if state_filter:
        filtered_data = [item for item in filtered_data if state_filter.lower() == item.get('college_state', '').lower()]
    if birth_state_filter:
        filtered_data = [item for item in filtered_data if birth_state_filter.lower() == item.get('birth_state', '').lower()]
    if gender_filter:
        filtered_data = [item for item in filtered_data if gender_filter.lower() == item.get('gender', '').lower()]
    if status_filter:
        filtered_data = [item for item in filtered_data if status_filter.lower() in item.get('status', '').lower()]

    if name_query:
        filtered_data = [item for item in filtered_data if name_query in item.get('full_name', '').lower()]
    if email_query:
        filtered_data = [item for item in filtered_data if email_query in item.get('email', '').lower()]

    # Set up pagination
    page = request.GET.get('page', 1)
    paginator = Paginator(filtered_data, 10)  # Show 10 items per page

    try:
        paginated_data = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        paginated_data = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g., 9999), deliver last page of results.
        paginated_data = paginator.page(paginator.num_pages)

    context = {
        'data': paginated_data,
        'college_filter': college_filter,
        'branch_filter': branch_filter,
        'year_filter': year_filter,
        'state_filter': state_filter,
        'birth_state_filter': birth_state_filter,
        'gender_filter': gender_filter,
        'status_filter': status_filter
    }

    return render(request, 'dashboard2.html', context)

def view_Info2(request,pk):
    print(pk)
    data=requests.get(f'http://13.127.81.177:8000/api/registers/{pk}/').json()
    return render(request,'Profile-1.html',{'data':data})



# ------------------------------- Dashboard3 -----------------------------------
def dashboard3(request):
    data = requests.get('http://13.127.81.177:8000/api/registers/').json()
    
    url = 'http://13.127.81.177:8000/transactions/'
    response = requests.get(url)
    
    if response.status_code == 200:
        data1 = response.json()
        verified_data = [entry for entry in data1 if entry.get('is_paid') == True]
        
        context = {
            'user_count': data,
            'transactions': verified_data,
        }
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API', 'status_code': response.status_code}

    return render(request, 'dashboard3.html', context)

def view_Info3(request,pk):
    print(pk)
    data=requests.get(f'http://13.127.81.177:8000/api/registers/{pk}/').json()
    return render(request,'profile-2.html',{'data':data})

# -------------------------------- Dashboard4 ---------------------------------------
def dashboard4(request):
    url = 'http://13.127.81.177:8000/api/registers/'
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('verified') == False]
        context = {'data': verified_data}
        print(context)
        
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}

    return render(request, 'dashboard4.html', context)

def view_Info4(request,pk):
    print(pk)
    data=requests.get(f'http://13.127.81.177:8000/api/registers/{pk}/').json()
    return render(request,'Profile-1.html',{'data':data})


# ----------------------------- Verification Button ---------------------------------
def accept(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/registers/{pk}/'

    update_data = {
        'verified': True,
    }
    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('view_Info1',pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)
    
def reject(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/registers/{pk}/'

    update_data = {
        'verified': False,    
    }
    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('view_Info1',pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)






# --------------------------------------internship section--------------------------------------------


def internship(request):
    data=requests.get('http://13.127.81.177:8000/api/internship-applications/').json()
    intern_count=len(data)
    print(data)


    
# --------------count the total verified ----------------------
    url = 'http://13.127.81.177:8000/api/internship-applications/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    Select_count = 0
    for internship in data:
        if internship.get('candidate_status') == 'Accept':
            Select_count += 1
    print(f'Number of verified registrations: {Select_count}')

# -------------- count the total unverified----------------------
    url = 'http://13.127.81.177:8000/api/internship-applications/'
    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    Reject_count = 0
    for internship in data:
        if internship.get('candidate_status') == 'Reject':
            Reject_count += 1
    print(f'Number of verified registrations: {Reject_count}')

 # --------------Count the total Pending ----------------------
    url = 'http://13.127.81.177:8000/api/internship-applications/'
    print(Select_count,Reject_count,intern_count)
    Pending_count= intern_count - (Select_count + Reject_count)
    print(f'Number of Pending Candidate: {Pending_count}')
    
    context={
        'intern_count': intern_count,
        'Select_count': Select_count,
        'Reject_count': Reject_count,
        'Pending_count': Pending_count,
    }
    return render(request,'internship.html',context)


def intern_applied(request):
    internship_response = requests.get('http://13.127.81.177:8000/api/internship-applications/')
    internship_data = internship_response.json()
    internship_field = internship_data[1].get('Internship_profile')

    internship_response = requests.get('http://13.127.81.177:8000/api/internship-applications/')
    
    # Parse the JSON response
    internship_data = internship_response.json()
    
    # Extract the Internship_profile from each internship entry
    internship_profiles = [internship.get('Internship_profile') for internship in internship_data]

    
    registers_response = requests.get('http://13.127.81.177:8000/api/registers/')
    registers_data = registers_response.json()
    
    context = {
        'internship_profiles': internship_profiles,
        'registers_data': registers_data,
    }
    return render(request,'Intern-Applied.html',context)



def intern_info(request,pk):
    print(pk)
    data=requests.get(f'http://13.127.81.177:8000/api/internship-applications/{pk}/').json()
    return render(request,'Intern-Pf-1.html',{'data':data})

def intern_dash1(request):
    pass


def intern_dash2(request):
    url = 'http://13.127.81.177:8000/api/internship-applications/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('candidate_status') == 'Accept']
        context = {'data': verified_data}    
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}
    return render(request,'Intern-Selected.html',context) 
   

def intern_dash3(request):
    url = 'http://13.127.81.177:8000/api/internship-applications/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('candidate_status') == 'Reject']
        context = {'data': verified_data}    
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}
    return render(request,'Intern-Rejected.html',context)

def intern_dash4(request):
    pass




def Select_intern(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/internship-applications/{pk}/'

    # Update candidate_status with a serializable value
    update_data = {
        'candidate_status': 'Accept',  # Example status value
    }

    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('intern_info', pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)
    

def Reject_intern(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/internship-applications/{pk}/'

    # Update candidate_status with a serializable value
    update_data = {
        'candidate_status': 'Reject',  # Example status value
    }

    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('intern_info', pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)
# ----------------------------------------------------------------------------------------------------



# ---------------------------------Mantoreship section-------------------------------------------------


def Mentoreship(request):
    data = requests.get('http://13.127.81.177:8000/api/mentorship/').json()
    mentor_count = len(data)

    # --------------Count the total Selected ----------------------
    url = 'http://13.127.81.177:8000/api/mentorship/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    select_count = 0
    for mentoreship in data:
        if mentoreship.get('candidate_status') == 'Select':
            select_count += 1
    print(f'Number of Selected Candidate: {select_count}')


     # --------------Count the total Rejected ----------------------
    url = 'http://13.127.81.177:8000/api/mentorship/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    Reject_count = 0
    for mentoreship in data:
        if mentoreship.get('candidate_status') == 'Reject':
            Reject_count += 1
    print(f'Number of Rejected Candidate: {Reject_count}')

    # --------------Count the total Rejected ----------------------
    url = 'http://13.127.81.177:8000/api/mentorship/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    NotEnroll_count = 0
    for mentoreship in data:
        if mentoreship.get('payment_status') == 'Not Enroll':
            NotEnroll_count += 1
    print(f'Number of Rejected Candidate: {NotEnroll_count}')
    
    context={
        'mentor_count':mentor_count,
        'select_count':select_count,
        'Reject_count':Reject_count,
        'NotEnroll_count':NotEnroll_count,
    }

    return render(request,'Mentoreship.html',context)


def Mentor_dash1(request):
    data=requests.get('http://13.127.81.177:8000/api/mentorship/').json()
    return render(request,'Mentor-dash1.html',{'data':data})

def mentor_info1(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/mentorship/{pk}/').json()
    return render(request,'Mentor-pf-1.html',{'data':data})


def Select(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/mentorship/{pk}/'

    # Update candidate_status with a serializable value
    update_data = {
        'candidate_status': 'Select',  # Example status value
    }

    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('mentor_info1', pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)
    

def Reject(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/mentorship/{pk}/'

    # Update candidate_status with a serializable value
    update_data = {
        'candidate_status': 'Reject',  # Example status value
    }

    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('mentor_info1', pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)



def Mentor_dash2(request):
    url = 'http://13.127.81.177:8000/api/mentorship/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('candidate_status') == 'Select']
        context = {'data': verified_data}    
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}

    return render(request, 'Mentor-dash2.html', context)

def mentor_info2(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/mentorship/{pk}/').json()
    return render(request,'Mentor-pf-2.html',{'data':data})


def Mentor_dash3(request):
    url = 'http://13.127.81.177:8000/api/mentorship/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('candidate_status') == 'Reject']
        context = {'data': verified_data}    
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}

    return render(request, 'Mentor-dash3.html', context)

def mentor_info3(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/mentorship/{pk}/').json()
    return render(request,'Mentor-pf-2.html',{'data':data})


def Mentor_dash4(request):
    url = 'http://13.127.81.177:8000/api/mentorship/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('payment_status') == 'Not Enroll']
        context = {'data': verified_data}    
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}

    return render(request, 'Mentor-dash4.html', context)



# -----------------------------------------------------------------------------------------------------



# ------------------------------------- Corporate training Section ------------------------------------------------

def corporate_training(request):
    data=requests.get('http://13.127.81.177:8000/api/corporatetraining/').json()
    corporate_training_count=len(data)
    print(data)

    # --------------Count the total Selected ----------------------
    url = 'http://13.127.81.177:8000/api/corporatetraining/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    select_count = 0
    for corporate in data:
        if corporate.get('candidate_status') == 'Select':
            select_count += 1
    print(f'Number of Selected Candidate: {select_count}')


     # --------------Count the total Rejected ----------------------
    url = 'http://13.127.81.177:8000/api/corporatetraining/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    Reject_count = 0
    for corporate in data:
        if corporate.get('candidate_status') == 'Reject':
            Reject_count += 1
    print(f'Number of Rejected Candidate: {Reject_count}')

     # -------------- Count the Not-Enroll ----------------------
    url = 'http://13.127.81.177:8000/api/corporatetraining/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    Notenroll_count = 0
    for corporate in data:
        if corporate.get('payment_status') == 'Not Enroll':
            Notenroll_count += 1
    print(f'Number of Rejected Candidate: {Notenroll_count}')

    context={
        'corporate_training_count':corporate_training_count,
        'select_count':select_count,
        'Reject_count':Reject_count,
        'Notenroll_count':Notenroll_count,
    }
    return render(request,'corporate.html',context)


def corporate_dash1(request):
    data=requests.get('http://13.127.81.177:8000/api/corporatetraining/').json()
    return render(request,'corporate-dash1.html',{'data':data})

def corporate_info1(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/corporatetraining/{pk}/').json()
    return render(request,'corporate-pf-1.html',{'data':data})

def corporate_dash2(request):
    url = 'http://13.127.81.177:8000/api/corporatetraining/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('verified') == True]
        context = {'data': verified_data}    
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}
    return render(request,'corporate-dash1.html',context)

def corporate_info2(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/corporatetraining/{pk}/').json()
    return render(request,'corporate-pf-1.html',{'data':data})

def corporate_dash3(request):
    url = 'http://13.127.81.177:8000/api/corporatetraining/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        # print(data)
        verified_data = [entry for entry in data if entry.get('candidate_status') == 'Reject']
        context = {'data': verified_data}    
        print(context)
    else:
        context = {'error': 'Failed to retrieve data from the API'}
        print(context)
    return render(request,'corporate-dash3.html',context)
 
def corporate_info3(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/corporatetraining/{pk}/').json()
    return render(request,'corporate-pf-1.html',{'data':data})


def Corporate_Select(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/corporatetraining/{pk}/'

    # Update candidate_status with a serializable value
    update_data = {
        'candidate_status': 'Select',  # Example status value
    }

    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('corporate_info1', pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)
    

def Corporate_Reject(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/corporatetraining/{pk}/'

    # Update candidate_status with a serializable value
    update_data = {
        'candidate_status': 'Reject',  # Example status value
    }

    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('corporate_info1', pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)


# ----------------------------------------------------------------------------------------------------------



# -------------------------------------fresher section--------------------------------------------------

def fresher(request):
    data=requests.get('http://13.127.81.177:8000/api/job-applications/').json()
    fresher_count=len(data)
    print(data)

     # --------------Count the total Selected ----------------------
    url = 'http://13.127.81.177:8000/api/job-applications/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    select_count = 0
    for fresher in data:
        if fresher.get('candidate_status') == 'Select':
            select_count += 1
    print(f'Number of Selected Candidate: {select_count}')


     # --------------Count the total Rejected ----------------------
    url = 'http://13.127.81.177:8000/api/job-applications/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    Reject_count = 0
    for fresher in data:
        if fresher.get('candidate_status') == 'Reject':
            Reject_count += 1
    print(f'Number of Rejected Candidate: {Reject_count}')

     # -------------- Count the Not-Enroll ----------------------
    url = 'http://13.127.81.177:8000/api/job-applications/'

    response = requests.get(url)
    response.raise_for_status()  
    data = response.json()
    Notenroll_count = 0
    for fresher in data:
        if fresher.get('payment_status') == 'Not Enroll':
            Notenroll_count += 1
    print(f'Number of Rejected Candidate: {Notenroll_count}')
    context={
        'fresher_count':fresher_count,
        'select_count':select_count,
        'Reject_count':Reject_count,
        'Notenroll_count':Notenroll_count,
    }
    return render(request,'fresher.html',context)


def fresher_dash1(request):
    data=requests.get('http://13.127.81.177:8000/api/job-applications/').json()
    return render(request,'fresher-dash1.html',{'data':data})

def fresher_info1(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/job-applications/{pk}/').json()
    return render(request,'fresher-pf-1.html',{'data':data})

def fresher_dash2(request):
    url = 'http://13.127.81.177:8000/api/job-applications/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('candidate_status') == 'Select']
        context = {'data': verified_data}    
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}
        # print(data)
    
    return render(request,'fresher-dash2.html',context)

def fresher_info2(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/job-applications/{pk}/').json()
    return render(request,'fresher-pf-2.html',{'data':data})

def fresher_dash3(request):
    url = 'http://13.127.81.177:8000/api/job-applications/'
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        verified_data = [entry for entry in data if entry.get('candidate_status') == 'Reject']
        context = {'data': verified_data}    
    else:
        context = {'data': [], 'error': 'Failed to retrieve data from the API'}
    return render(request,'fresher-dash3.html',context)

def fresher_info3(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/job-applications/{pk}/').json()
    return render(request,'fresher-pf-3.html',{'data':data})

def fresher_dash4(request):
    data=requests.get('http://13.127.81.177:8000/api/job-applications/').json()
    return render(request,'fresher-dash1.html',{'data':data})

def fresher_info4(request,pk):
    data=requests.get(f'http://13.127.81.177:8000/api/job-applications/{pk}/').json()
    return render(request,'fresher-pf-1.html',{'data':data})



def fresher_Select(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/job-applications/{pk}/'

    # Update candidate_status with a serializable value
    update_data = {
        'candidate_status': 'Select',  # Example status value
    }

    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('fresher_info1', pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)
    

def fresher_Reject(request, pk):
    update_endpoint = f'http://13.127.81.177:8000/api/job-applications/{pk}/'

    # Update candidate_status with a serializable value
    update_data = {
        'candidate_status': 'Reject',  # Example status value
    }

    response = requests.patch(update_endpoint, json=update_data)
    if response.status_code == 200:
        return redirect('fresher_info1', pk)
    else:
        return JsonResponse({'error': 'Failed to update user verification status'}, status=response.status_code)

# -----------------------------------------------------------------------------------------------------
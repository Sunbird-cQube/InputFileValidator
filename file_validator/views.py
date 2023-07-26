
from .models import Profile
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django import forms
from django.http import HttpResponse, JsonResponse
# Create your views here.
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import csv
import json
from io import StringIO
import io
import xlsxwriter

# @login_required


def home(request):
    # podcasts = Podcast.objects.all()
    # ordered = Podcast.objects.order_by('-views')
    print(request.user.username)
    return render(request, 'home.html', {"username": request.user.username})


def login_attempt(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user_obj = User.objects.filter(username=username).first()
        if user_obj is None:
            messages.success(request, 'User not found')
            return redirect('/accounts/login')

        profile_obj = Profile.objects.filter(user=user_obj).first()
        if(profile_obj == None):
            messages.success(request, 'User not found')
            return redirect('/accounts/login')

        if not profile_obj.is_verified:
            messages.success(
                request, 'Profile is not verified check your mail')
            return redirect('/accounts/login')

        user = authenticate(username=username, password=password)
        if user is None:
            messages.success(request, 'Wrong password')
            return redirect('/accounts/login')

        login(request, user)
        return redirect('/')

    return render(request, 'login.html')


def register_attempt(request):
    if request.method == 'POST':
        emailValidate = forms.EmailField()
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')

        try:
            emailValidate.clean(email)
            if User.objects.filter(username=username).first():
                messages.success(request, 'Username is taken')
                return redirect('/accounts/login')

            if User.objects.filter(email=email).first():
                messages.success(request, 'Email is taken')
                return redirect('/accounts/login')

            user_obj = User(username=username, email=email)
            user_obj.set_password(password)
            user_obj.save()
            auth_token = str(uuid.uuid4())
            profile_obj = Profile.objects.create(
                user=user_obj, auth_token=auth_token)
            profile_obj.save()
            send_mail_after_registration(email, auth_token)
            return redirect('/token')
        except forms.ValidationError as e:
            messages.success(request, 'Enter a valid email address')
            return redirect("/accounts/login")
        except Exception as e:
            print(e)

    return render(request, 'login.html')


def success(request):
    return render(request, 'success.html')


def token_send(request):
    return render(request, 'token_send.html')


def verify(request, auth_token):
    try:
        profile_obj = Profile.objects.filter(auth_token=auth_token).first()
        if profile_obj:
            if profile_obj.is_verified:
                print(profile_obj.type)
                # if(profile_obj.type == None):

                #     return redirect('/')
                messages.success(request, 'Your account is already verified')
                return redirect('/accounts/login')
            profile_obj.is_verified = True
            profile_obj.auth_token = None
            profile_obj.save()
            messages.success(request, 'Your account has been verified')
            user = authenticate(username=profile_obj.user.username,
                                password=profile_obj.user.password)
            return redirect('/accounts/login')
        else:
            return redirect('/error')
    except Exception as e:
        print(e)
        return redirect('/')


def error_page(request):
    return render(request, 'error.html')


def logout_view(request):
    logout(request)
    return redirect('home')


def forgot(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user_obj = User.objects.filter(email=email).first()
        if user_obj is None:
            messages.success(request, 'User not found')
            return redirect('/accounts/login')

        profile_obj = Profile.objects.filter(user=user_obj).first()
        auth_token = str(uuid.uuid4())
        profile_obj.auth_token = auth_token
        profile_obj.save()
        send_mail_after_registration(email, auth_token, "reset")
        messages.success(
            request, 'A reset link has been sent to your registered mail')

    return render(request, 'login.html')


def reset(request, auth_token):
    if request.method == 'POST':
        profile_obj = Profile.objects.filter(auth_token=auth_token).first()
        new_password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        if(new_password != confirm_password):
            messages.success(
                request, 'Confirmation password did not match the new password')
            return redirect(f'/{auth_token}')
        user_obj = profile_obj.user
        user_obj.set_password(new_password)
        user_obj.save()
        profile_obj.auth_token = None
        profile_obj.save()
        return redirect("/")

    return render(request, 'reset.html', {'auth_token': auth_token})


def send_mail_after_registration(email, token, type="verify"):
    subject = 'Your accounts need to be verified'
    message = f'Hi click on this link to verify your account http://127.0.0.1:8000/verify/{token}'
    if(type == "reset"):
        subject = "Reset Link for CSVALID"
        message = f'Hi click on this link to reset your password http://127.0.0.1:8000/reset/{token}'
    email_from = settings.EMAIL_HOST_USER
    recipient_list = [email]
    send_mail(subject, message, email_from, recipient_list)


def index_page(request):
    error_index = []
    error_messages = []
    error_occured = 0
    show_download = False
    if request.method == "POST" and request.FILES:
        csvfile = request.FILES['csv_file']
        decoded_file = csvfile.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        rows = list(reader)
        # print(rows)
        # Check if CSV has at least one row
        if len(rows) < 1:
            error_messages.append("The CSV file is empty.")
        else:
            show_download = True
            # Read validation properties from JSON file
            with open("properties.json") as prop_file:
                properties = json.load(prop_file)["properties"]
                # print(properties)

            # Check each row
            for i, row in enumerate(rows[1:]):
                if len(row) != len(properties):
                    error_messages.append(
                        f"Invalid number of columns in row {i + 1}.")
                else:
                    for j, column in enumerate(row):
                        # Retrieve the data type from the properties JSON
                        data_type = properties[j]["data_type"]
                        min_length = properties[j].get("min_length")
                        max_length = properties[j].get("max_length")
                        column_error = []

                        # Perform data type validation based on the retrieved data type
                        if data_type == "string" and not column.isalpha():
                            error_messages.append(f"Invalid value in column {j + 1} of row {i + 1}. "
                                                  f"Expected string value.")
                            column_error.append(i + 1)
                            column_error.append(j)
                        if min_length is not None and len(column) < min_length:
                            error_messages.append(f"Value in column {j + 1} of row {i + 1} is too short. "
                                                  f"Minimum length allowed is {min_length}.")
                            column_error.append(i + 1)
                            column_error.append(j)
                        if max_length is not None and len(column) > max_length:
                            error_messages.append(f"Value in column {j + 1} of row {i + 1} is too long. "
                                                  f"Maximum length allowed is {max_length}.")
                            column_error.append(i + 1)
                            column_error.append(j)
                        elif data_type == "integer" and not column.isnumeric():
                            error_messages.append(f"Invalid value in column {j + 1} of row {i + 1}. "
                                                  f"Expected integer value.")
                            column_error.append(i + 1)
                            column_error.append(j)

                        if len(column_error) > 0:
                            error_index.append(column_error)
                        else:
                            continue
                    # print(j, not column.isalpha(),not column.isnumeric(), properties[j])
                    # print(error_messages)
        if(len(error_messages) == 0):
            error_occured = 2
            error_messages.append(
                "There are no errors in this file.Successfuly getting validated from Cqube database")
            show_download = True
        else:
            error_occured = 1

        request.session['error_messages'] = error_messages
        request.session['error_index'] = error_index
        request.session['rows'] = rows
        request.session['show_download'] = show_download

        # Redirect to download view
        # return redirect('download')

    return render(request, "index.html", {"error_messages": error_messages, "error_occured": error_occured, "show_download": show_download})


def custom_validation(request):
    if request.method == "POST" and request.FILES:
        # Perform custom validation based on the selected columns
        selected_columns = [
            request.POST.get('column1', ''),
            request.POST.get('column2', ''),
            request.POST.get('column3', ''),
        ]
    return render(request, "custom_validation.html")


def download(request):
    # Retrieve the error messages and rows from the session
    error_index = request.session.get('error_index', [])
    error_messages = request.session.get('error_messages', [])
    rows = request.session.get('rows', [])
    print(error_index)
    # Create an in-memory Excel file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Define cell formats for normal and highlighted cells
    normal_format = workbook.add_format()
    highlighted_format = workbook.add_format({'bg_color': 'red'})

    # Write the rows to the worksheet with appropriate cell formatting
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            a = [i, j]
            if a in error_index:
                print("came")
                # Apply highlighted format to cells containing errors
                worksheet.write(i, j, cell, highlighted_format)
                #worksheet.write(i, j, cell, normal_format)
            else:
                worksheet.write(i, j, cell, normal_format)
                #worksheet.write(i, j, cell, highlighted_format)

    workbook.close()

    # Prepare the response with the Excel file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="highlighted_file.xlsx"'
    output.seek(0)
    response.write(output.getvalue())

    return response


def instructions(request):

    return render(request, "instructions.html")


from .models import Profile, ValidationError
from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib import messages
from .models import *
import uuid
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django import forms
from django.http import HttpResponse, JsonResponse
# Create your views here.
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import csv
import json
import io
import xlsxwriter
import re
import os
from django.views import View
from collections import defaultdict
from file_validator_app.settings import BASE_DIR
from django.db.models.functions import TruncMonth
from django.db.models import Count


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


def get_files_and_folders(dir_path, parent_dir=""):
    items = []
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if os.path.isfile(item_path):
            if parent_dir:
                items.append(f"{parent_dir}\{item}")
            else:
                items.append(item)
        elif os.path.isdir(item_path):
            subdir_path = os.path.join(
                parent_dir, item) if parent_dir else item
            items.extend(get_files_and_folders(
                item_path, subdir_path))
    return items


def index_page(request):
    error_index = []
    error_messages = []
    error_occured = 0
    show_download = False
    directory = os.path.join(BASE_DIR, "JsonSchemas/programs")
    # dictionary_values = {
    #     "value1": True,
    #     "value2": True,
    #     "50": True,
    #     "200": True,

    # }
    files_and_folders = get_files_and_folders(directory)
    if request.method == "POST" and request.FILES:
        # for updating properties.json
        # print(request.POST)
        file_folder_value = request.POST.get('file_folder', None)
        # print(file_folder_value)
        selected_file_dir = os.path.join(
            BASE_DIR, "JsonSchemas")+"\programs\\" + file_folder_value
        # print(selected_file_dir)
        properties = {}
        if selected_file_dir:
            try:
                with open(selected_file_dir, 'r') as f:
                    file_contents = f.read()
                try:
                    json_object = json.loads(file_contents)
                    properties["file_contents"] = json_object
                except json.JSONDecodeError as e:
                    properties["file_contents"] = f"Error decoding JSON: {str(e)}"

            except FileNotFoundError:
                properties["file_contents"] = "File not found"
            except Exception as e:
                properties["file_contents"] = f"Error reading file: {str(e)}"
        # Replace with the actual path to properties.json
        properties_file = os.path.join(BASE_DIR, "properties.json")
        with open(properties_file, 'w') as f:
            json.dump(properties, f, indent=4)

        csvfile = request.FILES['csv_file']
        decoded_file = csvfile.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        rows = list(reader)
        print(properties_file)
        # Check if CSV has at least one row
        if len(rows) < 1:
            error_messages.append("The CSV file is empty.")
        else:
            show_download = True
            # Read validation properties from JSON file
            with open("properties.json") as prop_file:
                properties = json.load(prop_file)[
                    "file_contents"]["input"]["properties"]
                # required_fields = json.load(prop_file)[
                #     "file_contents"]["input"]["required"]
                # print(properties)
            with open("column_values.json") as column_values_file:
                column_values_data = json.load(column_values_file)["columns"]
            # print(column_values_data)
            mandatory_fields = [
                field for field in properties if properties[field].get("shouldNotNull")]
            pattern = r'[+-]?([0-9]*[.])?[0-9]+'
            # Check each row
            for i, row in enumerate(rows[1:],  start=1):
                if len(row) != len(properties):
                    error_messages.append(
                        f"Invalid number of columns in row {i}.")
                    break
                else:
                    for j, column in enumerate(row):
                        # Retrieve the data type from the properties JSON
                        column_name = list(properties.keys())[j]
                        field_props = properties[column_name]
                        data_type = field_props["type"]
                        column_error = []
                        error = []
                        unique_columns = {}
                        added = False
                        if column_name in column_values_data:
                            allowed_values = column_values_data[column_name]
                            # print(column, allowed_values,
                            #       column not in allowed_values)
                            if column not in allowed_values:
                                error.append(i + 1)
                                error.append(j + 1)
                                error.append(
                                    f"Value not present in the allowed values list for {column_name}.")
                                if added == False:
                                    column_error.append(i)
                                    column_error.append(j)
                                    added = True
                        if field_props.get("shouldNotNull") and not column.strip():
                            error.append(i+1)
                            error.append(j+1)
                            error.append(f"{column_name} is mandatory.")
                            # error_messages.append(f"Invalid value in column {j + 1} of row {i + 1}. "
                            #                       f"Expected string value.")
                            if added == False:
                                column_error.append(i)
                                column_error.append(j)
                                added = True
                        if field_props.get("unique"):
                            value = row[j]
                            if value in unique_columns.get(j, set()):
                                error.append(
                                    [i+1, j+1, f"{column_name} must be unique."])
                                if not added:
                                    column_error.append([i, j])
                                    added = True
                            else:
                                unique_columns.setdefault(j, set()).add(value)
                                added = False
                        if data_type == "string" and column == "NULL":
                            error.append(i+1)
                            error.append(j+1)
                            error.append(
                                f"{column_name} should be a string.")
                            if added == False:
                                column_error.append(i)
                                column_error.append(j)
                                added = True

                        elif data_type == "number" and not re.match(pattern, column):
                            error.append(i+1)
                            error.append(j+1)
                            error.append(
                                f"{column_name} should be a number.")
                            if added == False:
                                column_error.append(i)
                                column_error.append(j)
                                added = True

                        if len(column_error) > 0:
                            error_index.append(column_error)
                            error_messages.append(error)
                        else:
                            continue
                    # print(j, not column.isalpha(),not column.isnumeric(), properties[j])
                    # print(error_messages)
        error_counts = defaultdict(int)

        for error_info in error_messages:
            # Assuming error message is at index 2
            error_message = error_info[2]
            if "mandatory" in error_info[2]:
                error_message = "Mandatory"
            elif "unique" in error_info[2]:
                error_message = "unique"
            elif "number" in error_info[2]:
                error_message = "number"
            elif "string" in error_info[2]:
                error_message = "String"
            elif "allowed values" in error_info[2]:
                error_message = "allowed"
            error_counts[error_message] += 1

        for error_message, count in error_counts.items():
            try:
                validation_error = ValidationError.objects.get(
                    error_type=error_message)
                validation_error.error_count += count
                validation_error.save()
            except ValidationError.DoesNotExist:
                validation_error = ValidationError(
                    error_type=error_message,
                    error_count=count
                )
                validation_error.save()

        if(len(error_messages) == 0):
            error_occured = 2
            error_messages.append(
                [0, 0, "There are no errors in this file.Successfuly getting validated from Cqube database"])
            show_download = True
        else:
            error_occured = 1

        if error_occured == 1:
            request.session['error_occured'] = error_occured
            request.session['error_messages'] = error_messages
            request.session['show_download'] = show_download
            request.session['error_index'] = error_index
            request.session['rows'] = rows
            # print(error_messages)
            return redirect('upload_errors')

        request.session['error_occured'] = error_occured
        request.session['error_messages'] = error_messages
        request.session['error_index'] = error_index
        request.session['rows'] = rows
        request.session['show_download'] = show_download
        # print(error_messages)
        # Redirect to download view
        # return redirect('download')
        return render(request, "error_page.html", {"error_messages": error_messages, "error_occured": error_occured, "show_download": show_download, "username": request.user.username})
    return render(request, "index.html", {"error_messages": error_messages, "error_occured": error_occured, "show_download": show_download, 'files_and_folders': files_and_folders, "username": request.user.username})


def upload_errors(request):
    # Retrieve the error messages from the session
    error_messages = request.session.get('error_messages', [])
    error_occured = request.session.get('error_occured', 0)
    show_download = request.session.get('show_download', False)

    # Clear the session data to avoid displaying the same errors on subsequent uploads
    # request.session['error_messages'] = []
    # request.session['error_index'] = []
    # request.session['rows'] = []
    # request.session['error_occured'] = 0
    # request.session['show_download'] = False

    return render(request, "error_page.html", {"error_messages": error_messages, "error_occured": error_occured, "show_download": show_download, "username": request.user.username})


def custom_validation(request):
    if request.method == "POST" and request.FILES:
        uploaded_file = request.FILES['csv_file']
        print(json.loads(request.POST.get("custom_data")))
        custom_data = json.loads(request.POST.get("custom_data"))
        print("hello")
        # Convert custom_data into a dictionary for easier access
        custom_data_dict = {entry['ColumnNumber']
            : entry for entry in custom_data}

        decoded_file = uploaded_file.read().decode('utf-8').splitlines()
        reader = csv.reader(decoded_file)
        rows = list(reader)

        error_messages = []
        if len(rows) < 1:
            error_messages.append((0, '', "The CSV file is empty."))
        else:
            # Iterate through each row of the CSV
            for row_number, row in enumerate(rows[1:]):
                for col_number, cell_value in enumerate(row):
                    # Convert to 1-based index
                    col_number_str = str(col_number + 1)

                    if col_number_str in custom_data_dict:
                        column_data = custom_data_dict[col_number_str]
                        expected_data_type = column_data['DataType']
                        has_missing_values = column_data['MissingValues']
                        min_len = int(
                            column_data['MinLen']) if column_data['MinLen'] else None
                        max_len = int(
                            column_data['MaxLen']) if column_data['MaxLen'] else None
                        regex_pattern = column_data['Regx']

                        # Perform regular expression validation
                        if regex_pattern:
                            if not re.match(regex_pattern, cell_value):
                                error_messages.append(
                                    (row_number + 1, col_number_str, f"Value does not match pattern"))
                        # Performing missing values
                        if has_missing_values == 'Yes':
                            if not cell_value.strip():
                                error_messages.append(
                                    (row_number + 1, col_number_str, f"Missing value"))
                        # perform min and max len validation
                        if min_len is not None and len(cell_value) < min_len:
                            error_messages.append(
                                (row_number + 1, col_number_str, f"Value length less than {min_len}"))
                        if max_len is not None and len(cell_value) > max_len:
                            error_messages.append(
                                (row_number + 1, col_number_str, f"Value length more than {max_len}"))

                        # Perform datatype validation based on the expected_data_type
                        if not expected_data_type:
                            continue

                        if expected_data_type == 'int':
                            if not cell_value.isdigit():
                                error_messages.append(
                                    (row_number + 1, col_number_str, f"Invalid integer value"))
                        elif expected_data_type == 'float':
                            try:
                                float(cell_value)
                            except ValueError:
                                error_messages.append(
                                    (row_number + 1, col_number_str, f"Invalid float value"))
                        elif expected_data_type == 'string':
                            try:
                                float(cell_value)
                            except ValueError:
                                error_messages.append(
                                    (row_number + 1, col_number_str, f"Invalid string value"))

        error_counts = defaultdict(int)
        for error_info in error_messages:
            # Assuming error message is at index 2
            error_message = error_info[2]
            if "does not match" in error_info[2]:
                error_message = "Regx_Error"
            elif "Missing value" in error_info[2]:
                error_message = "Missing_value"
            elif "less than" in error_info[2]:
                error_message = "Min_Len"
            elif "more than" in error_info[2]:
                error_message = "Max_len"
            elif "Invalid integer" in error_info[2]:
                error_message = "Integer"
            elif "Invalid float" in error_info[2]:
                error_message = "Float"
            elif "Invalid string" in error_info[2]:
                error_message = "String"
            error_counts[error_message] += 1

        for error_message, count in error_counts.items():
            try:
                validation_error = CustomValidationError.objects.get(
                    error_type=error_message)
                validation_error.error_count += count
                validation_error.save()
            except CustomValidationError.DoesNotExist:
                validation_error = CustomValidationError(
                    error_type=error_message,
                    error_count=count
                )
                validation_error.save()

        context = {
            'error_occured': 1 if error_messages else 0,
            'error_messages': error_messages,
            'show_download': 1 if error_messages else 0,
        }
        context["username"] = request.user.username
        return render(request, "error_page.html", context)

    return render(request, "custom_validation.html", {"username": request.user.username})


def download(request):
    # Retrieve the error messages and rows from the session
    error_index = request.session.get('error_index', [])
    error_messages = request.session.get('error_messages', [])
    # print(error_index)
    rows = request.session.get('rows', [])
    # Create an in-memory Excel file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Define cell formats for normal and highlighted cells
    normal_format = workbook.add_format()
    highlighted_format = workbook.add_format({'bg_color': 'red'})

    # Write the rows to the worksheet with appropriate cell formatting
    for i, row in enumerate(rows):
        already_colored = []
        for j, cell in enumerate(row):
            a = [i, j]
            if a in error_index and a not in already_colored:
                # Apply highlighted format to cells containing errors
                worksheet.write(i, j, cell, highlighted_format)
                already_colored.append(a)

                current_index = [i+1, j+1]
                error_message = None
                if error_messages[0][:2] == current_index:
                    error_message = error_messages[0][2]
                    error_messages.pop(0)
                if error_message:
                    # Add comment to the cell with the corresponding error message
                    worksheet.write_comment(i, j, error_message)

            else:
                worksheet.write(i, j, cell, normal_format)
                # worksheet.write(i, j, cell, highlighted_format)

    workbook.close()

    # Prepare the response with the Excel file
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="highlighted_file.xlsx"'
    output.seek(0)
    response.write(output.getvalue())

    return response


def instructions(request):

    return render(request, "instructions.html", {"username": request.user.username})


@user_passes_test(lambda u: u.is_authenticated and u.is_staff)
def dashboard_view(request):
    # Your dashboard view logic here
    error_messages = ValidationError.objects.all()
    custom_error_messages = CustomValidationError.objects.all()
    context = {
        'mandatory_sum': 0,
        'unique_sum': 0,
        'string_sum': 0,
        'number_sum': 0,
        'allowed_values_sum': 0,
        "Regx_Error": 0,
        "Missing_value": 0,
        "Min_Len": 0,
        "Max_len": 0,
        "Integer": 0,
        "Float": 0,
        "String": 0,
    }
    context['total_errors'] = sum(
        error.error_count for error in error_messages)
    # Process the data if needed and prepare it for the chart
    for error in error_messages:
        if error.error_type == "allowed":
            context["allowed_values_sum"] += error.error_count
        elif error.error_type == "String":
            context['string_sum'] += error.error_count
        elif error.error_type == "Mandatory":
            context["mandatory_sum"] += error.error_count
        elif error.error_type == "unique":
            context["unique_sum"] += error.error_count
        elif error.error_type == "number":
            context["number_sum"] += error.error_count
        else:
            continue
    context['total_custom_errors'] = sum(
        error.error_count for error in custom_error_messages)
    for error in custom_error_messages:
        if error.error_type == "Regx_Error":
            context["Regx_Error"] += error.error_count
        elif error.error_type == "Missing_value":
            context["Missing_value"] += error.error_count
        elif error.error_type == "Min_Len":
            context["Min_Len"] += error.error_count
        elif error.error_type == "Max_len":
            context["Max_len"] += error.error_count
        elif error.error_type == "Integer":
            context["Integer"] += error.error_count
        elif error.error_type == "Float":
            context["Float"] += error.error_count
        elif error.error_type == "String":
            context["String"] += error.error_count
        else:
            continue
    user_count_data = User.objects.annotate(
        month=TruncMonth('date_joined')
    ).values('month').annotate(user_count=Count('id')).order_by('month')

    time_periods = [data['month'].strftime(
        '%b') for data in user_count_data]
    user_counts = [data['user_count'] for data in user_count_data]
    context['time_periods'] = ','.join(time_periods)
    context['user_counts'] = ','.join(map(str, user_counts))
    context['total_users'] = User.objects.count()
    context["username"] = request.user.username

    return render(request, 'dashboard.html', context)

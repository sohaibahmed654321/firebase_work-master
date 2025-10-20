from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.models import User
from mera_project.firebase_config import db
import requests
import firebase_admin
from firebase_admin import credentials, auth  # ✅ Fixed: auth import missing
from django.conf import settings


# 🔑 Firebase Web API Key



# ✅ Initialize Firebase (only once)
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred, {
        "databaseURL": "https://your-project.firebaseio.com"  # <-- apna Firebase Realtime DB URL lagao
    })


# -------------------- CONTACT --------------------

def contacts(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        subject = request.POST.get("subject")
        message = request.POST.get("message")

        # ✅ Save data to Firestore
        db.collection("contact").add({
            "Name": name,
            "Email": email,
            "Subject": subject,
            "Msg": message,
        })

        messages.success(request, "Thank you for contacting us! We will reply soon.")
        return redirect("contact")

    return render(request, "myapp/contact.html")


def show_data(request):
    users = db.collection("User").stream()
    user_list = []
    for u in users:
        data = u.to_dict()
        data["doc_id"] = u.id   # 🔑 Must! Otherwise reverse URL fails
        user_list.append(data)
    return render(request, "myapp/showdata.html", {"users": user_list})

# -------------------- EDIT USER --------------------
def edit_user(request, doc_id):
    doc_ref = db.collection("User").document(doc_id)
    user_data = doc_ref.get().to_dict()

    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        doc_ref.update({"Name": name, "Email": email})
        messages.success(request, "User updated successfully!")
        return redirect("show")

    return render(request, "myapp/edit_user.html", {"user": user_data, "doc_id": doc_id})

# -------------------- DELETE USER --------------------
def delete_user(request, doc_id):
    try:
        db.collection("User").document(doc_id).delete()
        messages.success(request, "User deleted successfully!")
    except:
        messages.error(request, "Failed to delete user.")
    return redirect("show")

def register(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")  # 👈 get role from form

        # 🔍 Validation
        if not name or not email or not password:
            messages.error(request, "All fields are required.")
            return redirect("reg")

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect("reg")

        # ✅ Firebase signup URL
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={settings.FIRE}"
        payload = {"email": email, "password": password, "returnSecureToken": True}

        response = requests.post(url, json=payload)

        # ✅ If Firebase signup successful
        if response.status_code == 200:
            db.collection("User").add({
                "Name": name,
                "Email": email,
                "Pswd": password,
                "Role": role if role else "User",  # ✅ save actual selected role
            })
            messages.success(request, "🎉 User Registered Successfully! Please Login.")
            return redirect("login")

        # ❌ If Firebase signup fails
        else:
            error_message = response.json().get("error", {}).get("message", "Registration failed.")
            messages.error(request, f"Error: {error_message}")
            return redirect("reg")

    # 🔹 GET request (form display)
    return render(request, "myapp/registration.html")



# -------------------- FIREBASE LOGIN --------------------

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        # ✅ Firebase SignIn API (email/password login)
        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={settings.FIRE}"
        payload = {"email": email, "password": password, "returnSecureToken": True}
        response = requests.post(url, json=payload)

        if response.status_code == 200:
            user = auth.get_user_by_email(email)
            request.session['user_email'] = user.email
            request.session['user_name'] = user.display_name or email.split('@')[0].capitalize()

            messages.success(request, "🎉 Login successful! Welcome back.")
            return redirect('welcome')
        else:
            error_message = response.json().get("error", {}).get("message", "Login failed.")
            messages.error(request, f"Login failed: {error_message}")

    return render(request, "myapp/login.html")


# -------------------- HOME (Default Route) --------------------

def home(request):
    """Server start hone par smart redirect:
       agar user login hai to welcome page,
       warna login page."""
    if request.session.get("user_email"):
        return redirect("welcome")
    return redirect("login")


# -------------------- WELCOME PAGE --------------------

def welcome(request):
    user_email = request.session.get('user_email')
    user_name = request.session.get('user_name')

    if not user_email:
        return redirect('login')

    context = {
        'user_email': user_email,
        'user_name': user_name
    }
    return render(request, "welcome.html", context)


# -------------------- LOGOUT --------------------

def logout_view(request):
    logout(request)
    request.session.flush()
    messages.success(request, "You have been logged out.")
    return redirect("login")


# -------------------- PROFILE --------------------

def profile(request):
    user_email = request.session.get('user_email')
    user_name = request.session.get('user_name')

    if not user_email:
        return redirect('login')

    return render(request, "profile.html", {
        'user_email': user_email,
        'user_name': user_name
    })

def start(request):
    # Agar user already login hai to directly welcome page dikhao
    if request.session.get("user_email"):
        return redirect("welcome")

    # Warna simple start page dikhao
    return render(request, "myapp/start.html")

def edit_profile(request):
    user_email = request.session.get('user_email')
    user_name = request.session.get('user_name')

    if not user_email:
        return redirect('login')

    if request.method == "POST":
        new_name = request.POST.get('name')
        new_email = request.POST.get('email')

        # Firebase update logic
        users = db.collection("User").where("Email", "==", user_email).stream()
        for u in users:
            db.collection("User").document(u.id).update({
                "Name": new_name,
                "Email": new_email
            })

        request.session['user_email'] = new_email
        request.session['user_name'] = new_name
        messages.success(request, "Profile updated successfully!")
        return redirect('welcome')

    return render(request, "edit_profile.html", {
        'user_email': user_email,
        'user_name': user_name
    })

def add_user(request):
    if request.method == "POST":
        name = request.POST.get('name')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role')

        # ✅ Use same collection name as show_data
        db.collection('User').add({
            'Name': name,
            'Email': email,
            'Pswd': password,
            'Role': role
        })

        messages.success(request, "User added successfully!")
        return redirect('show_data')

    return render(request, 'add_user.html')



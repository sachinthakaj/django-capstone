# Capstone Project — Travel & Hospitality Booking API

A RESTful API built with **Django 6** and **Django REST Framework** that allows service providers (hotels, restaurants, tour operators, etc.) to list their services, and authenticated users to discover and book them.

---

## Features

- Provider and service management with ownership-based permissions
- JWT authentication (register, login, token refresh)
- Booking creation, listing, and cancellation
- Filtering, ordering, and pagination on all list endpoints
- Role-based access control (owner-only updates, admin-only deletes)

---

## Tech Stack

| Package | Version |
|---|---|
| Python | 3.12 |
| Django | 6.0.2 |
| djangorestframework | 3.16.1 |
| djangorestframework-simplejwt | 5.5.1 |
| django-filter | 25.2 |

---

## Local Setup

### Prerequisites

- Python 3.12+
- `pip`
- (Recommended) `virtualenv` or `venv`

### 1. Clone the repository

```bash
git clone <repository-url>
cd capstone_project
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install django==6.0.2 djangorestframework==3.16.1 djangorestframework-simplejwt==5.5.1 django-filter==25.2
```

### 4. Apply migrations

```bash
python manage.py migrate
```

### 5. Create a superuser

```bash
python manage.py createsuperuser
```

> Make sure to provide an **email address** when prompted — it is required for booking creation.

### 6. Run the development server

```bash
python manage.py runserver
```

The API will be available at `http://127.0.0.1:8000/`.  
The browsable API UI is available at any endpoint in the browser.  
The Django admin is available at `http://127.0.0.1:8000/admin/`.

---

## Running the Test Suite

```bash
python manage.py test apps.providers.tests apps.bookings.tests apps.users.tests --no-input
```

This runs all tests.

To run a specific app's tests:

```bash
python manage.py test apps.users.tests
python manage.py test apps.providers.tests
python manage.py test apps.bookings.tests
```

---

## API Endpoint Summary

### Authentication

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| `POST` | `/api/auth/register/` | Register a new user | No |
| `POST` | `/api/token/` | Obtain JWT access + refresh token | No |
| `POST` | `/api/token/refresh/` | Refresh access token | No |

**Login request body:**
```json
{ "username": "youruser", "password": "yourpassword" }
```

**Authenticated requests** — include the access token in the header:
```
Authorization: Bearer <access_token>
```

---

### Providers

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| `GET` | `/providers/` | List all providers (paginated, filterable) | No |
| `POST` | `/providers/` | Create a provider | Yes |
| `GET` | `/providers/{id}/` | Retrieve a provider | No |
| `PUT` | `/providers/{id}/` | Update a provider | Owner only |
| `PATCH` | `/providers/{id}/` | Partial update a provider | Owner only |
| `DELETE` | `/providers/{id}/` | Delete a provider | Admin only |
| `POST` | `/providers/{id}/services/` | Create a service for a provider | Owner only |

**Filter parameters:** `?business_type=hotel`, `?name=...`

---

### Services

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| `GET` | `/services/` | List all active services (paginated, filterable) | No |
| `GET` | `/services/{id}/` | Retrieve a service | No |
| `PUT` | `/services/{id}/` | Update a service | Provider owner only |
| `PATCH` | `/services/{id}/` | Partial update a service | Provider owner only |
| `POST` | `/services/{id}/book/` | Book a service | Yes |

**Filter parameters:** `?provider__business_type=hotel`, `?price__gte=50`, `?price__lte=200`  
**Ordering:** `?ordering=price`, `?ordering=-created_at`

---

### Bookings

| Method | Endpoint | Description | Auth required |
|---|---|---|---|
| `GET` | `/bookings/` | List current user's bookings | Yes |
| `GET` | `/bookings/{id}/` | Retrieve a booking | Owner only |
| `PATCH` | `/bookings/{id}/cancel/` | Cancel a pending booking | Owner only |

> Users can only see and access their own bookings. Attempting to access another user's booking returns **404**, not 403.

---

## Permission Summary

| Role | Can do |
|---|---|
| Anonymous | Read providers and services |
| Authenticated user | Create providers/bookings, read own bookings |
| Provider owner | Update their own provider and its services |
| Booking owner | View and cancel their own bookings |
| Admin (is_staff) | Delete any provider |

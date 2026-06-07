# Inventory Management System

## Overview
Inventory Management System is a web application built using FastAPI, SQLAlchemy, and PostgreSQL. It helps businesses manage products, categories, stock levels, and inventory transactions efficiently.

## Features

- User Authentication using JWT
- Category Management
- Product Management
- Inventory Tracking
- Dashboard and Reporting
- Search and Filter Products
- Secure API Endpoints

## Tech Stack

### Backend
- FastAPI
- SQLAlchemy
- PostgreSQL
- JWT Authentication

### Tools
- Git
- GitHub
- Uvicorn

## Project Structure

```text
app/
├── models/
├── schemas/
├── routes/
├── services/
├── utils/
├── database.py
├── config.py
└── main.py
```

## Installation

### Clone Repository

```bash
git clone https://github.com/yourusername/inventory-management-system.git
cd inventory-management-system
```

### Create Virtual Environment

```bash
python -m venv venv
```

### Activate Environment

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file:

```env
DATABASE_URL=postgresql://username:password@localhost/inventory_db
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## Run Application

```bash
uvicorn app.main:app --reload
```

## API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

## Future Enhancements

- Export Reports
- Email Notifications
- Role Based Access Control
- Advanced Analytics Dashboard

## Author

Poojitha Indirala

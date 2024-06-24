# Food Ordering Web Application

## Description

This project is a full-featured food ordering web application built with Django and React. It provides a user-friendly platform for customers to browse the menu, place orders (dine-in, delivery, or takeout), track order status, and manage their saved items for quick reordering. The backend is powered by Django Rest Framework, ensuring a robust and scalable API.

## Features

* **User Authentication:** Secure user registration and login with profile management.
* **Menu Browsing and Search:** Easily explore the menu with categories and real-time search functionality.
* **Dynamic Shopping Cart:** Add, remove, and modify items in the cart.
* **Ordering Options:** Choose from dine-in, delivery, or takeout.
* **Order Tracking:** Real-time updates on the status and progress of orders.
* **Saved Items:** Save favorite menu items for faster ordering in the future.
* **Bestseller Recommendations:** Discover popular items based on recent sales data.

## Tech Stack

* **Frontend:** React
* **Backend:** Django, Django Rest Framework
* **Database:** SQLite

## Installation and Setup

1. clone the repository
2. create a virtual environment 'python -m venv env' and then 'source env/Scripts/activate'
3. pip install -r requirements.txt
4. python manage.py migrate
5. python manage.py createsuperuser
6. python manage.py runserver to run the server
7. you can go to admin using http://127.0.0.1:8000/admin and login with superuser to access the database

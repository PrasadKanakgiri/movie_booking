# 🎬 Cinema Booking System (Python + MySQL)

A **Command Line Interface (CLI)** based Cinema Booking System built with **Python** and **MySQL**.  
This project allows **users** to browse and book movie tickets with seat selection, and provides **admins** with the ability to manage movies, screens, showtimes, and generate reports.

---

## 🚀 Features

### 👤 User Functionality
- **Register & Login** with secure password hashing (`bcrypt`)
- **View Movies** → Browse all available movies
- **View Showtimes** → Check movies, screens, timings, and ticket prices
- **Book Tickets** → Select showtime, view seat map (`O = available, X = booked`), book tickets securely
- **My Bookings** → View booking history with movie, screen, and seat details
- **Logout**

### 🔑 Admin Functionality
- **Manage Movies** → Add, view, delete movies
- **Manage Screens** → Add and view screens with rows/columns
- **Manage Showtimes** → Schedule movies in screens with timings and ticket price
- **View All Bookings** → See all user bookings with details
- **Daily Report** → Generate revenue, tickets sold, occupancy, and top-performing movie (per day)
- **Monthly Report** → Generate revenue and performance stats for the last 30 days
- **Logout**

---

## 🗄 Database Design

The system uses a **relational schema** with foreign keys for data integrity:

- **users** → Stores user info (username, email, password hash, role: `user` / `admin`)
- **movies** → Stores movies with title, duration
- **screens** → Stores screens with rows and columns
- **showtimes** → Links movies and screens with date, time, and ticket price
- **bookings** → Stores each booking (user, showtime, total amount)
- **booking_seats** → Stores individual seats booked for each booking

Foreign keys ensure that deleting a movie or showtime automatically removes related bookings (via `ON DELETE CASCADE`).

---

## ⚙️ Tech Stack

- **Python** → CLI Application  
- **MySQL** → Database  
- **bcrypt** → Secure password hashing  
- **tabulate** → Pretty-print tables for reports and data  

---

## 📸 Sample User Flow

### 🔹 User
1. Register or Login  
2. View Movies and Showtimes  
3. Book Tickets (choose seats from seat map)  
4. Get booking confirmation with ticket details  
5. View past bookings anytime  

### 🔹 Admin
1. Login as admin  
2. Manage movies, screens, and showtimes  
3. Monitor all bookings  
4. Generate daily & monthly reports (revenue, occupancy, top movies)  

---

## 🛠 Installation & Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/your-username/cinema-booking-system.git
   cd cinema-booking-system


2. Install dependencies:

   ```bash
   pip install bcrypt tabulate mysql-connector-python
   ```

3. Setup MySQL database:

   * Create a new database `cinema_db`
   * Run the SQL schema file (if provided) or let the app create tables automatically.

4. Run the application:

   ```bash
   python main.py
   ```

---

## 📊 Reports

### Daily Report

* Tickets sold
* Revenue generated
* Occupancy %
* Average ticket price
* Top performing movie

### Monthly Report

* Day-wise revenue and tickets sold
* Total revenue and occupancy
* Top performing movie of the month

---

## 🔐 Security

* Passwords are stored as **bcrypt hashes**
* Seat booking system prevents **double booking**
* Foreign keys maintain **data consistency**

---

## 👨‍💻 Author

Developed by **Prasad Kanakgiri**
Final Year B.Tech CSE Student @ VIIT Pune



import mysql.connector
import bcrypt
import sys
import os
from datetime import datetime

# =====================
# Database Config
# =====================
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "Prasad@123422110709",
    "database": "cinema_cli"
}

# =====================
# Database Initialization
# =====================
def get_connection(dbname=True):
    cfg = DB_CONFIG.copy()
    if not dbname:
        cfg.pop("database", None)
    return mysql.connector.connect(**cfg)

def init_db():
    # First connect without database to create it
    conn = get_connection(dbname=False)
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS cinema_cli CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    conn.commit()
    cur.close()
    conn.close()

    # Now connect with the DB and create tables
    conn = get_connection()
    cur = conn.cursor()

    # Users
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password_hash VARBINARY(60) NOT NULL,
            role ENUM('user','admin','staff') DEFAULT 'user',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
    """)

    # Movies
    cur.execute("""
        CREATE TABLE IF NOT EXISTS movies (
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            duration_min INT,
            rating VARCHAR(20),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
    """)

    # Screens
    cur.execute("""
        CREATE TABLE IF NOT EXISTS screens (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            total_rows INT NOT NULL,
            total_cols INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ) ENGINE=InnoDB;
    """)

    # Showtimes
    cur.execute("""
        CREATE TABLE IF NOT EXISTS showtimes (
            id INT AUTO_INCREMENT PRIMARY KEY,
            movie_id INT NOT NULL,
            screen_id INT NOT NULL,
            start_time DATETIME NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(screen_id, start_time),
            FOREIGN KEY(movie_id) REFERENCES movies(id) ON DELETE CASCADE,
            FOREIGN KEY(screen_id) REFERENCES screens(id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """)

    # Bookings (transaction-level)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bookings (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            showtime_id INT NOT NULL,
            total_amount DECIMAL(10,2) NOT NULL,
            booked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
            FOREIGN KEY(showtime_id) REFERENCES showtimes(id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """)

    # Booking Seats (individual seats inside a booking)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS booking_seats (
            id INT AUTO_INCREMENT PRIMARY KEY,
            booking_id INT NOT NULL,
            seat_row VARCHAR(5) NOT NULL,
            seat_col INT NOT NULL,
            UNIQUE(booking_id, seat_row, seat_col),
            FOREIGN KEY(booking_id) REFERENCES bookings(id) ON DELETE CASCADE
        ) ENGINE=InnoDB;
    """)

    conn.commit()
    cur.close()
    conn.close()

# =====================
# Authentication
# =====================
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def verify_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def register_user():
    print("\n=== User Registration ===")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    # Ask role
    role = input("Enter role (user/admin): ").strip().lower()
    if role not in ["user", "admin"]:
        print("❌ Invalid role. Defaulting to 'user'.")
        role = "user"

    conn = get_connection()
    cur = conn.cursor()

    try:
        password_hash = hash_password(password)
        cur.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (username, password_hash, role),
        )
        conn.commit()
        print(f"✅ User '{username}' registered successfully as '{role}'.")
    except mysql.connector.IntegrityError:
        print("❌ Username already exists.")
    finally:
        cur.close()
        conn.close()



def login_user():
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    print("\n=== User Login ===")
    username = input("Enter username: ").strip()
    password = input("Enter password: ").strip()

    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cur.fetchone()

    cur.close()
    conn.close()

    if user and verify_password(password, user["password_hash"]):
        print(f"✅ Login successful! Welcome {user['username']} ({user['role']})")
        return user
    else:
        print("❌ Invalid username or password.")
        return None

# =====================
# Admin Functions
# =====================
def view_all_bookings():
    print("\n📖 All Bookings:")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT b.id, u.username, m.title, s.start_time, b.total_amount
        FROM bookings b
        JOIN users u ON b.user_id = u.id
        JOIN showtimes s ON b.showtime_id = s.id
        JOIN movies m ON s.movie_id = m.id
        ORDER BY s.start_time DESC
    """)
    bookings = cur.fetchall()

    if not bookings:
        print("❌ No bookings found.")
    else:
        for b in bookings:
            print(f"Booking ID: {b['id']} | User: {b['username']} | Movie: {b['title']} | Showtime: {b['start_time']} | Amount: ₹{b['total_amount']:.2f}")

    cur.close()
    conn.close()

def admin_monthly_report():
    print("\n📊 Monthly Report (Last 30 Days)")

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Revenue & tickets per day
    cur.execute("""
        SELECT DATE(s.start_time) AS day,
               SUM(b.total_amount) AS revenue,
               COUNT(b.id) AS tickets_sold
        FROM bookings b
        JOIN showtimes s ON b.showtime_id = s.id
        WHERE s.start_time >= CURDATE() - INTERVAL 30 DAY
        GROUP BY day
        ORDER BY day
    """)
    rows = cur.fetchall()

    if not rows:
        print("❌ No bookings in the last 30 days.")
        cur.close()
        conn.close()
        return

    total_revenue = 0
    total_tickets = 0

    print("\nDay-wise Summary:")
    for r in rows:
        print(f"{r['day']} → Tickets: {r['tickets_sold']} | Revenue: ₹{r['revenue']:.2f}")
        total_revenue += r["revenue"] or 0
        total_tickets += r["tickets_sold"]

    print("\n📌 Totals:")
    print(f"Total Tickets Sold: {total_tickets}")
    print(f"Total Revenue: ₹{total_revenue:.2f}")

    # Find top performing movie
    cur.execute("""
        SELECT m.title, SUM(b.total_amount) AS revenue
        FROM bookings b
        JOIN showtimes s ON b.showtime_id = s.id
        JOIN movies m ON s.movie_id = m.id
        WHERE s.start_time >= CURDATE() - INTERVAL 30 DAY
        GROUP BY m.title
        ORDER BY revenue DESC
        LIMIT 1
    """)
    top = cur.fetchone()

    if top:
        print(f"🏆 Top Performing Movie: {top['title']} (Revenue: ₹{top['revenue']:.2f})")

    cur.close()
    conn.close()


def admin_daily_report():
    """
    Daily report for a given date (default = today).
    Shows per-showtime:
      - movie, screen, start_time
      - seats sold (count of booking_seats)
      - revenue (sum of bookings.total_amount)
      - capacity and occupancy %
      - average ticket price
    Also prints totals and top movie by revenue for that date.
    """
    from datetime import date

    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # 1) Ask date (default today)
    date_str = input("Enter date for report (YYYY-MM-DD, leave empty for today): ").strip()
    if not date_str:
        date_str = date.today().strftime("%Y-%m-%d")

    print(f"\n📊 Daily Report for {date_str}\n")

    # 2) Per-showtime aggregation (tickets count from booking_seats, revenue from bookings.total_amount)
    cur.execute("""
        SELECT
            s.id AS show_id,
            m.title AS movie_title,
            sc.name AS screen_name,
            s.start_time,
            sc.total_rows, sc.total_cols,
            COUNT(bs.id) AS tickets_sold,
            COALESCE(SUM(b.total_amount), 0) AS revenue
        FROM showtimes s
        JOIN movies m ON s.movie_id = m.id
        JOIN screens sc ON s.screen_id = sc.id
        LEFT JOIN bookings b ON b.showtime_id = s.id
        LEFT JOIN booking_seats bs ON bs.booking_id = b.id
        WHERE DATE(s.start_time) = %s
        GROUP BY s.id, m.title, sc.name, s.start_time, sc.total_rows, sc.total_cols
        ORDER BY s.start_time;
    """, (date_str,))
    rows = cur.fetchall()

    if not rows:
        print("No showtimes found for this date.\n")
        cur.close()
        conn.close()
        return

    total_revenue = 0.0
    total_tickets = 0
    # Print per-showtime details
    for r in rows:
        capacity = (r["total_rows"] or 0) * (r["total_cols"] or 0)
        tickets_sold = int(r["tickets_sold"] or 0)
        revenue = float(r["revenue"] or 0.0)
        avg_ticket = (revenue / tickets_sold) if tickets_sold > 0 else 0.0
        occupancy = (tickets_sold / capacity * 100) if capacity > 0 else 0.0

        print(f"🎬 {r['movie_title']} @ {r['screen_name']} on {r['start_time']}")
        print(f"    Tickets sold: {tickets_sold} / {capacity}  |  Occupancy: {occupancy:.1f}%")
        print(f"    Revenue: ₹{revenue:.2f}  |  Avg ticket: ₹{avg_ticket:.2f}\n")

        total_revenue += revenue
        total_tickets += tickets_sold

    print("----")
    print(f"💰 Total revenue for {date_str}: ₹{total_revenue:.2f}")
    print(f"🎟 Total tickets sold: {total_tickets}")

    # 3) Top movie by revenue that day
    cur.execute("""
        SELECT m.title AS movie_title, COALESCE(SUM(b.total_amount),0) AS revenue
        FROM showtimes s
        JOIN movies m ON s.movie_id = m.id
        LEFT JOIN bookings b ON b.showtime_id = s.id
        WHERE DATE(s.start_time) = %s
        GROUP BY m.title
        ORDER BY revenue DESC
        LIMIT 1;
    """, (date_str,))
    top = cur.fetchone()
    if top and top["revenue"] and top["revenue"] > 0:
        print(f"🏆 Top movie of the day: {top['movie_title']} (Revenue: ₹{top['revenue']:.2f})")
    else:
        print("No revenue/bookings for this date.")

    cur.close()
    conn.close()


def admin_menu(admin_user):
    while True:
        print("\n=== Admin Panel ===")
        print("1. Manage Movies")
        print("2. Manage Screens")
        print("3. Manage Showtimes")
        print("4. View All Bookings")
        print("5. Daily Report")
        print("6. Monthly Report")
        print("7. Logout")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            manage_movies()
        elif choice == "2":
            manage_screens()
        elif choice == "3":
            manage_showtimes()
        elif choice == "4":
            view_all_bookings()   # ✅ new function
        elif choice == "5":
            admin_daily_report()  # ✅ function we added
        elif choice == "6":
            admin_monthly_report()  # ✅ you can implement monthly aggregation
        elif choice == "7":
            print("👋 Logging out of Admin Panel...")
            break
        else:
            print("❌ Invalid choice.")

def manage_movies():
    while True:
        print("\n--- Manage Movies ---")
        print("1. Add Movie")
        print("2. View Movies")
        print("3. Delete Movie")
        print("4. Back")
        choice = input("Enter choice: ")

        if choice == "1":
            add_movie()
        elif choice == "2":
            view_movies()
        elif choice == "3":
            movie_id = input("Enter movie ID to delete: ")
            delete_movie(movie_id)
        elif choice == "4":
            break
        else:
            print("Invalid choice.")

def add_movie():
    title = input("Enter movie title: ")
    description = input("Enter description: ")
    duration = input("Enter duration in minutes: ")
    rating = input("Enter rating (e.g. PG, R, etc.): ")

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO movies (title, description, duration_min, rating) VALUES (%s, %s, %s, %s)",
        (title, description, duration, rating)
    )
    conn.commit()
    cur.close()
    conn.close()
    print(f"✅ Movie '{title}' added successfully!")


def view_movies():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, duration_min, rating FROM movies;")
    movies = cur.fetchall()
    if not movies:
        print("No movies found.")
    else:
        print("\nMovies:")
        for m in movies:
            print(f"{m[0]} - {m[1]} ({m[2]}min, {m[3]})")  # show ID so you can delete
    cur.close()
    conn.close()

def delete_movie(movie_id):
    conn = get_connection()
    cur = conn.cursor()

    # check if movie exists
    cur.execute("SELECT title FROM movies WHERE id=%s", (movie_id,))
    row = cur.fetchone()
    if not row:
        print("⚠️ Movie not found.")
    else:
        confirm = input(f"Are you sure you want to delete '{row[0]}'? (y/n): ")
        if confirm.lower() == "y":
            cur.execute("DELETE FROM movies WHERE id=%s", (movie_id,))
            conn.commit()
            print(f"✅ Movie '{row[0]}' deleted successfully!")
        else:
            print("❌ Deletion cancelled.")

    cur.close()
    conn.close()


def manage_screens():
    while True:
        print("\n--- Manage Screens ---")
        print("1. Add Screen")
        print("2. View Screens")
        print("3. Back")

        choice = input("Enter choice: ").strip()
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        if choice == "1":
            name = input("Enter screen name: ").strip()
            rows = int(input("Enter number of seat rows: "))
            cols = int(input("Enter number of seat cols: "))
            cur.execute("INSERT INTO screens (name, total_rows, total_cols) VALUES (%s, %s, %s)",
                        (name, rows, cols))
            conn.commit()
            print("✅ Screen added.")

        elif choice == "2":
            cur.execute("SELECT * FROM screens")
            rows = cur.fetchall()
            print("\nScreens:")
            for r in rows:
                print(f"{r['id']}. {r['name']} ({r['total_rows']}x{r['total_cols']})")

        elif choice == "3":
            break
        else:
            print("❌ Invalid choice.")

        cur.close()
        conn.close()


# ---------------------
# Showtimes Management
# ---------------------
def manage_showtimes():
    while True:
        print("\n--- Manage Showtimes ---")
        print("1. Add Showtime")
        print("2. View Showtimes")
        print("3. Back")

        choice = input("Enter choice: ").strip()
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        if choice == "1":
            # list movies
            cur.execute("SELECT * FROM movies")
            movies = cur.fetchall()
            print("Available Movies:")
            for m in movies:
                print(f"{m['id']}. {m['title']}")
            movie_id = int(input("Enter Movie ID: "))

            # list screens
            cur.execute("SELECT * FROM screens")
            screens = cur.fetchall()
            print("Available Screens:")
            for s in screens:
                print(f"{s['id']}. {s['name']} ({s['total_rows']}x{s['total_cols']})")
            screen_id = int(input("Enter Screen ID: "))

            start_time = input("Enter start time (YYYY-MM-DD HH:MM:SS): ").strip()
            price = float(input("Enter ticket price: "))

            cur.execute("INSERT INTO showtimes (movie_id, screen_id, start_time, price) VALUES (%s, %s, %s, %s)",
                        (movie_id, screen_id, start_time, price))
            conn.commit()
            print("✅ Showtime added.")

        elif choice == "2":
            cur.execute("""SELECT showtimes.id, movies.title, screens.name, start_time, price 
                           FROM showtimes 
                           JOIN movies ON showtimes.movie_id=movies.id 
                           JOIN screens ON showtimes.screen_id=screens.id""")
            rows = cur.fetchall()
            print("\nShowtimes:")
            for r in rows:
                print(f"{r['id']}. {r['title']} @ {r['name']} on {r['start_time']} (₹{r['price']})")

        elif choice == "3":
            break
        else:
            print("❌ Invalid choice.")

        cur.close()
        conn.close()


# =====================
# User Functions
# =====================
def user_book_tickets(user):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # Step 1: Show available showtimes
    cur.execute("""SELECT showtimes.id, movies.title, screens.name, start_time, price 
                   FROM showtimes 
                   JOIN movies ON showtimes.movie_id = movies.id 
                   JOIN screens ON showtimes.screen_id = screens.id""")
    shows = cur.fetchall()

    print("\n📅 Available Showtimes:")
    for s in shows:
        print(f"{s['id']}. {s['title']} @ {s['name']} on {s['start_time']} (₹{s['price']})")

    show_id = int(input("Enter showtime ID to book: ").strip())

    # Step 2: Fetch screen info for seat layout
    cur.execute("""SELECT screens.id, screens.total_rows, screens.total_cols 
                   FROM showtimes 
                   JOIN screens ON showtimes.screen_id = screens.id 
                   WHERE showtimes.id=%s""", (show_id,))
    screen = cur.fetchone()
    rows, cols = screen["total_rows"], screen["total_cols"]

    # Step 3: Fetch already booked seats
    cur.execute("""SELECT seat_row, seat_col FROM booking_seats 
                   WHERE showtime_id=%s""", (show_id,))
    booked = {(b["seat_row"], b["seat_col"]) for b in cur.fetchall()}

    # Step 4: Display seat map
    print("\nSeat Map (O = Available, X = Booked):")
    for r in range(rows):
        row_label = chr(65 + r)  # A, B, C...
        row_seats = []
        for c in range(1, cols + 1):
            if (row_label, c) in booked:
                row_seats.append("X")
            else:
                row_seats.append("O")
        print(f"{row_label}: {' '.join(row_seats)}")

    # Step 5: Ask number of tickets
    num_tickets = int(input("Enter number of tickets to book: ").strip())

    # ✅ Step 6: Get price and calculate total_amount
    cur.execute("SELECT price FROM showtimes WHERE id=%s", (show_id,))
    price = cur.fetchone()["price"]
    total_amount = price * num_tickets

    # ✅ Step 7: Insert into bookings with total_amount
    cur.execute(
        "INSERT INTO bookings (user_id, showtime_id, total_amount) VALUES (%s, %s, %s)",
        (user["id"], show_id, total_amount)
    )
    booking_id = cur.lastrowid

    # Step 8: Select seats
    selected_seats = []
    for i in range(num_tickets):
        seat = input(f"Enter seat {i+1} (e.g., A5): ").strip().upper()
        row_label, col = seat[0], int(seat[1:])
        if (row_label, col) in booked or (row_label, col) in selected_seats:
            print("❌ Seat already booked. Choose another.")
            continue
        cur.execute("""INSERT INTO booking_seats 
                       (booking_id, showtime_id, seat_row, seat_col) 
                       VALUES (%s, %s, %s, %s)""", 
                    (booking_id, show_id, row_label, col))
        selected_seats.append((row_label, col))

    conn.commit()
    print(f"\n✅ Booking confirmed! Total amount: ₹{total_amount}")
    print("Your seats:", ", ".join(f"{r}{c}" for r, c in selected_seats))

    cur.close()
    conn.close()

def display_seat_map(show_id):
    conn = get_connection()
    cur = conn.cursor(dictionary=True)

    # 1. Get screen layout for this showtime
    cur.execute("""
        SELECT s.total_rows, s.total_cols
        FROM showtimes st
        JOIN screens s ON st.screen_id = s.id
        WHERE st.id = %s
    """, (show_id,))
    screen = cur.fetchone()
    if not screen:
        print("Showtime not found.")
        cur.close()
        conn.close()
        return

    total_rows, total_cols = screen["total_rows"], screen["total_cols"]

    # 2. Get booked seats for this showtime
    cur.execute("""
        SELECT bs.seat_row, bs.seat_col
        FROM booking_seats bs
        JOIN bookings b ON bs.booking_id = b.id
        WHERE b.showtime_id = %s
    """, (show_id,))
    booked = {(row["seat_row"], row["seat_col"]) for row in cur.fetchall()}

    cur.close()
    conn.close()

    # 3. Print seat map
    print("\nSeat Map (O = Available, X = Booked):")
    for r in range(1, total_rows + 1):
        row_label = chr(64 + r)   # 1→A, 2→B...
        row_display = []
        for c in range(1, total_cols + 1):
            if (row_label, c) in booked:
                row_display.append("X")
            else:
                row_display.append("O")
        print(f"{row_label}: {' '.join(row_display)}")


def user_menu(user):
    while True:
        print("\n=== User Menu ===")
        print("1. View Movies")
        print("2. View Showtimes")
        print("3. Book Tickets")
        print("4. My Bookings")
        print("5. Logout")

        choice = input("Enter choice: ").strip()
        conn = get_connection()
        cur = conn.cursor(dictionary=True)

        if choice == "1":
            cur.execute("SELECT * FROM movies")
            movies = cur.fetchall()
            print("\n🎬 Movies:")
            for m in movies:
                print(f"{m['id']}. {m['title']} ({m['duration_min']} min)")

        elif choice == "2":
            cur.execute("""SELECT showtimes.id, movies.title, screens.name, start_time, price 
                           FROM showtimes 
                           JOIN movies ON showtimes.movie_id=movies.id 
                           JOIN screens ON showtimes.screen_id=screens.id""")
            shows = cur.fetchall()
            print("\n📅 Showtimes:")
            for s in shows:
                print(f"{s['id']}. {s['title']} @ {s['name']} on {s['start_time']} (₹{s['price']})")

        elif choice == "3":
            user_book_tickets(user)   # ✅ call booking function we built

        elif choice == "4":
            # show past bookings
            cur.execute("""
                SELECT b.id AS booking_id, m.title, s.start_time, sc.name AS screen_name, COUNT(bs.id) AS tickets
                FROM bookings b
                JOIN showtimes s ON b.showtime_id = s.id
                JOIN movies m ON s.movie_id = m.id
                JOIN screens sc ON s.screen_id = sc.id
                JOIN booking_seats bs ON b.id = bs.booking_id
                WHERE b.user_id = %s
                GROUP BY b.id, m.title, s.start_time, sc.name
                ORDER BY s.start_time DESC
            """, (user['id'],))
            bookings = cur.fetchall()

            print("\n🎟️ My Bookings:")
            if not bookings:
                print("No bookings yet.")
            else:
                for b in bookings:
                    print(f"Booking #{b['booking_id']} - {b['title']} @ {b['screen_name']} on {b['start_time']} | Tickets: {b['tickets']}")

        elif choice == "5":
            print("👋 Logging out...")
            break
        else:
            print("❌ Invalid choice.")

        cur.close()
        conn.close()


# =====================
# Main App
# =====================
def main():
    print("=== Cinema Booking CLI ===")
    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")

        choice = input("Enter choice: ").strip()

        if choice == "1":
            register_user()

        elif choice == "2":
            user = login_user()
            if user:
                print(f"\n✅ Welcome, {user['username']}! (Role: {user['role']})")

                if user["role"] == "admin":
                    admin_menu(user)   # go to Admin Panel
                else:
                    user_menu(user)    # placeholder for normal user menu

        elif choice == "3":
            print("👋 Exiting... Goodbye!")
            break
        else:
            print("❌ Invalid choice.")

if __name__ == "__main__":
    main()

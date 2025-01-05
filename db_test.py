import sqlite3

# Connect to the SQLite database (or create it if it doesn't exist)
connection = sqlite3.connect("/Users/prathyet/PycharmProjects/OpenVault/static/databases/test.db")

# Create a cursor object to execute SQL commands
cursor = connection.cursor()

# Create a table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    age INTEGER NOT NULL,
    email TEXT NOT NULL UNIQUE
)
""")

# Function to insert data into the table
def insert_user(name, age, email):
    try:
        cursor.execute("INSERT INTO users (name, age, email) VALUES (?, ?, ?)", (name, age, email))
        connection.commit()  # Commit the transaction
        print(f"User {name} added successfully.")
    except sqlite3.IntegrityError as e:
        print(f"Error: {e}")

# Function to read data from the table
def fetch_users():
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

# Insert sample data
insert_user("Alice", 25, "alice@example.com")
insert_user("Bob", 30, "bob@example.com")

# Fetch and display data
print("\nUsers in the database:")
fetch_users()

# Close the connection
connection.close()

import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import sqlite3
import bcrypt
from datetime import datetime
from PIL import Image, ImageTk

# Database Initialization
conn = sqlite3.connect("localmarket.db")
cursor = conn.cursor()

# Create Tables
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    location TEXT
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS listings (
    listing_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT,
    price REAL NOT NULL,
    category TEXT,
    seller_id INTEGER,
    location TEXT,
    image_path TEXT,
    FOREIGN KEY (seller_id) REFERENCES users (user_id)
)""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS messages (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER,
    receiver_id INTEGER,
    listing_id INTEGER,
    message_text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (sender_id) REFERENCES users (user_id),
    FOREIGN KEY (receiver_id) REFERENCES users (user_id),
    FOREIGN KEY (listing_id) REFERENCES listings (listing_id)
)""")

conn.commit()


class MarketplaceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Local Community Marketplace")
        self.root.geometry("900x700")

        self.items_per_page = 5
        self.current_page = 0

        self.user_id = None
        self.login_screen()

    ### Authentication ###
    def login_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Login", font=("Arial", 20)).pack(pady=10)

        tk.Label(self.root, text="Email:").pack()
        self.email_entry = tk.Entry(self.root)
        self.email_entry.pack()

        tk.Label(self.root, text="Password:").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Button(self.root, text="Login", command=self.login).pack(pady=10)
        tk.Button(self.root, text="Signup", command=self.signup_screen).pack()

    def signup_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Signup", font=("Arial", 20)).pack(pady=10)

        tk.Label(self.root, text="Name:").pack()
        self.name_entry = tk.Entry(self.root)
        self.name_entry.pack()

        tk.Label(self.root, text="Email:").pack()
        self.email_entry = tk.Entry(self.root)
        self.email_entry.pack()

        tk.Label(self.root, text="Password:").pack()
        self.password_entry = tk.Entry(self.root, show="*")
        self.password_entry.pack()

        tk.Label(self.root, text="Location:").pack()
        self.location_entry = tk.Entry(self.root)
        self.location_entry.pack()

        tk.Button(self.root, text="Signup", command=self.signup).pack(pady=10)
        tk.Button(self.root, text="Back to Login", command=self.login_screen).pack()

    def login(self):
        email = self.email_entry.get()
        password = self.password_entry.get()

        user = cursor.execute("SELECT user_id, password FROM users WHERE email = ?", (email,)).fetchone()
        if user and bcrypt.checkpw(password.encode('utf-8'), user[1].encode('utf-8')):
            self.user_id = user[0]
            self.dashboard()
        else:
            messagebox.showerror("Login Failed", "Invalid email or password.")

    def signup(self):
        name = self.name_entry.get()
        email = self.email_entry.get()
        password = self.password_entry.get()
        location = self.location_entry.get()

        if not (name and email and password and location):
            messagebox.showerror("Signup Failed", "All fields are required!")
            return

        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        try:
            cursor.execute("INSERT INTO users (name, email, password, location) VALUES (?, ?, ?, ?)",
                           (name, email, hashed_password, location))
            conn.commit()
            messagebox.showinfo("Signup Successful", "You can now log in!")
            self.login_screen()
        except sqlite3.IntegrityError:
            messagebox.showerror("Signup Failed", "Email already exists.")

    ### Dashboard ###
    def dashboard(self):
        self.clear_screen()
        tk.Label(self.root, text="Welcome to the Marketplace!", font=("Arial", 16)).pack(pady=10)

        tk.Button(self.root, text="Post a Listing", command=self.post_listing_screen).pack(pady=5)
        tk.Button(self.root, text="Browse Listings", command=lambda: self.display_listings(sort_by="price")).pack(
            pady=5)
        tk.Button(self.root, text="My Profile", command=self.profile_screen).pack(pady=5)
        tk.Button(self.root, text="Messages", command=self.messages_screen).pack(pady=5)
        tk.Button(self.root, text="Logout", command=self.logout).pack(pady=5)

    ### Profile Screen ###
    def profile_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Edit Profile", font=("Arial", 20)).pack(pady=10)

        user_data = cursor.execute("SELECT name, email, location FROM users WHERE user_id = ?",
                                   (self.user_id,)).fetchone()
        self.name_entry = tk.Entry(self.root)
        self.name_entry.insert(0, user_data[0])
        self.name_entry.pack()

        self.email_entry = tk.Entry(self.root)
        self.email_entry.insert(0, user_data[1])
        self.email_entry.pack()

        self.location_entry = tk.Entry(self.root)
        self.location_entry.insert(0, user_data[2])
        self.location_entry.pack()

        tk.Button(self.root, text="Update Profile", command=self.update_profile).pack(pady=10)
        tk.Button(self.root, text="Back to Dashboard", command=self.dashboard).pack(pady=5)

    def update_profile(self):
        name = self.name_entry.get()
        email = self.email_entry.get()
        location = self.location_entry.get()

        if not (name and email and location):
            messagebox.showerror("Update Failed", "All fields are required!")
            return

        cursor.execute("UPDATE users SET name = ?, email = ?, location = ? WHERE user_id = ?",
                       (name, email, location, self.user_id))
        conn.commit()
        messagebox.showinfo("Profile Updated", "Your profile has been updated.")

        file_path = filedialog.askopenfilename(title="Select Profile Picture",
                                               filetypes=(("Image Files", "*.png;*.jpg;*.jpeg"), ("All Files", "*.*")))
        if file_path:
            try:
                cursor.execute("UPDATE users SET profile_picture = ? WHERE user_id = ?", (file_path, self.user_id))
                conn.commit()
                self.display_profile_picture(file_path)
                messagebox.showinfo("Success", "Profile picture updated!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to update profile picture: {e}")
        self.dashboard()

    def display_profile_picture(self, file_path):
        try:
            img = Image.open(file_path)
            img.thumbnail((100, 100))  # Adjust size as needed
            photo = ImageTk.PhotoImage(img)
            # Assuming you have a label in your profile screen to show the profile picture
            tk.Label(self.root, image=photo).pack(side="left", padx=10)
            self.root.image = photo  # Prevent garbage collection
        except Exception as e:
            messagebox.showerror("Image Error", f"Unable to display image: {e}")

    ### Post a Listing Screen ###
    def post_listing_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Post a New Listing", font=("Arial", 16)).pack(pady=10)

        tk.Label(self.root, text="Title:").pack()
        self.title_entry = tk.Entry(self.root)
        self.title_entry.pack()

        tk.Label(self.root, text="Description:").pack()
        self.description_entry = tk.Entry(self.root)
        self.description_entry.pack()

        tk.Label(self.root, text="Price:").pack()
        self.price_entry = tk.Entry(self.root)
        self.price_entry.pack()

        tk.Label(self.root, text="Category:").pack()
        self.category_entry = tk.Entry(self.root)
        self.category_entry.pack()

        self.image_path = tk.StringVar()
        tk.Button(self.root, text="Upload Image", command=self.upload_image).pack()
        tk.Label(self.root, textvariable=self.image_path).pack()

        tk.Button(self.root, text="Post Listing", command=self.post_listing).pack(pady=10)
        tk.Button(self.root, text="Back to Dashboard", command=self.dashboard).pack(pady=5)

    def upload_image(self):
        file_path = filedialog.askopenfilename(title="Select Image",
                                               filetypes=(("Image Files", "*.png;*.jpg;*.jpeg"), ("All Files", "*.*")))
        self.image_path.set(file_path)

    def post_listing(self):
        title = self.title_entry.get().strip()
        description = self.description_entry.get().strip()
        price = self.price_entry.get().strip()
        category = self.category_entry.get().strip()
        image_path = self.image_path.get()

        if not title or not price or not category:
            messagebox.showerror("Error", "Title, Price, and Category are required!")
            return

        try:
            price = float(price)
        except ValueError:
            messagebox.showerror("Error", "Price must be a number.")
            return

        user_location = cursor.execute("SELECT location FROM users WHERE user_id = ?", (self.user_id,)).fetchone()
        if not user_location:
            messagebox.showerror("Error", "Unable to fetch user location.")
            return

        location = user_location[0]

        cursor.execute(
            "INSERT INTO listings (title, description, price, category, seller_id, location, image_path) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, description, price, category, self.user_id, location, image_path))
        conn.commit()
        messagebox.showinfo("Success", "Listing posted successfully!")
        self.dashboard()

    # Sent Messages Screen
    def sent_messages_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Sent Messages", font=("Arial", 20)).pack(pady=10)

        messages = cursor.execute("""
            SELECT m.message_text, COALESCE(l.title, 'Unknown Listing') AS title, u.name, m.timestamp
            FROM messages m
            LEFT JOIN listings l ON m.listing_id = l.listing_id
            JOIN users u ON m.receiver_id = u.user_id
            WHERE m.sender_id = ? ORDER BY m.timestamp DESC
            """, (self.user_id,)).fetchall()

        for message in messages:
            tk.Label(self.root,
                     text=f"To: {message[2]} | Listing: {message[1]} | Date: {message[3]}\nMessage: {message[0]}",
                     justify="left", wraplength=600, anchor="w", padx=10, pady=5).pack(fill="x", padx=10)

        tk.Button(self.root, text="Back to Messages", command=self.messages_screen).pack(pady=10)

    # Compose New Message Screen

    def messages_screen(self):
        self.clear_screen()
        tk.Label(self.root, text="Your Messages", font=("Arial", 20)).pack(pady=10)

        # Fetch distinct conversation partners
        conversations = cursor.execute("""
            SELECT DISTINCT u.user_id, u.name, u.email
            FROM users u
            JOIN messages m ON u.user_id IN (m.sender_id, m.receiver_id)
            WHERE ? IN (m.sender_id, m.receiver_id) AND u.user_id != ?
            """, (self.user_id, self.user_id)).fetchall()

        if not conversations:
            tk.Label(self.root, text="No conversations yet.", font=("Arial", 14)).pack(pady=20)
            tk.Button(self.root, text="Back to Dashboard", command=self.dashboard).pack(pady=10)
            return

        for conversation in conversations:
            partner_id, partner_name, partner_email = conversation
            tk.Button(
                self.root,
                text=f"{partner_name} ({partner_email})",
                command=lambda pid=partner_id, pname=partner_name: self.conversation_screen(pid, pname)
            ).pack(fill="x", pady=5)

        tk.Button(self.root, text="Back to Dashboard", command=self.dashboard).pack(pady=10)

    def conversation_screen(self, partner_id, partner_name):
        self.clear_screen()
        tk.Label(self.root, text=f"Conversation with {partner_name}", font=("Arial", 20)).pack(pady=10)

        # Fetch messages between the two users
        messages = cursor.execute("""
            SELECT m.message_text, u.name, m.timestamp, m.sender_id
            FROM messages m
            JOIN users u ON u.user_id = m.sender_id
            WHERE (m.sender_id = ? AND m.receiver_id = ?) OR (m.sender_id = ? AND m.receiver_id = ?)
            ORDER BY m.timestamp ASC
            """, (self.user_id, partner_id, partner_id, self.user_id)).fetchall()

        frame = tk.Frame(self.root)
        frame.pack(pady=10, fill="both", expand=True)

        canvas = tk.Canvas(frame)
        scroll_y = tk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        message_frame = tk.Frame(canvas)

        message_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=message_frame, anchor="nw")
        canvas.configure(yscrollcommand=scroll_y.set)

        canvas.pack(side="left", fill="both", expand=True)
        scroll_y.pack(side="right", fill="y")

        for message in messages:
            # Handle different message structures
            if len(message) == 4:  # Expected structure
                sender_name, text, timestamp, sender_id = message
            elif len(message) == 3:  # If one field (e.g., sender_id) is missing
                sender_name, text, timestamp = message
                sender_id = "Unknown"  # Placeholder for missing data
            else:
                continue  # Skip invalid or unexpected data structures

            # Determine alignment and background color
            align = "w" if sender_id != self.user_id else "e"
            bg_color = "lightgrey" if sender_id != self.user_id else "lightblue"

            # Create and pack the label
            tk.Label(
                message_frame,
                text=f"{sender_name}: {text}\n{timestamp}",
                anchor=align,
                justify="left" if align == "w" else "right",
                wraplength=500,
                bg=bg_color,
                padx=10,
                pady=5,
            ).pack(anchor=align, fill="x", pady=2)

        # Input for sending a new message
        self.message_text_entry = tk.Text(self.root, height=4, width=70)
        self.message_text_entry.pack(pady=5)

        tk.Button(self.root, text="Send", command=lambda partner_id=partner_id: self.send_messages(partner_id)).pack(
            pady=10)
        tk.Button(self.root, text="Back to Messages", command=self.messages_screen).pack(pady=5)

    def send_messages(self, recipient_id=None):
        message_text = self.message_text_entry.get("1.0", tk.END).strip()
        if not message_text:
            messagebox.showerror("Error", "Message text cannot be empty.")
            return

        if not recipient_id:
            recipient_email = self.recipient_email_entry.get().strip()  # This should not be re-assigned
            if not recipient_email:
                messagebox.showerror("Error", "Recipient email cannot be empty.")
                return

            # Fetch recipient ID from the email
            recipient = cursor.execute("SELECT user_id FROM users WHERE email = ?", (recipient_email,)).fetchone()
            if not recipient:
                messagebox.showerror("Error", "Recipient email does not exist.")
                return
            recipient_id = recipient[0]

        try:
            # Insert the message into the database
            cursor.execute(
                """
                INSERT INTO messages (sender_id, receiver_id, message_text, timestamp)
                VALUES (?, ?, ?, datetime('now'))
                """,
                (self.user_id, recipient_id, message_text)
            )
            conn.commit()
            messagebox.showinfo("Success", "Message sent successfully!")
            self.message_text_entry.delete("1.0", tk.END)  # Clear the text box
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")

    ### Display Listings ###

    def display_listings(self, sort_by="price"):
        self.clear_screen()
        tk.Label(self.root, text="Marketplace Listings", font=("Arial", 16)).pack(pady=10)

        listings = cursor.execute("""
            SELECT l.listing_id, l.title, l.price, l.category, l.location, l.image_path, u.email, u.name
            FROM listings l
            JOIN users u ON l.seller_id = u.user_id
            ORDER BY ? ASC LIMIT ? OFFSET ?
        """, (sort_by, self.items_per_page, self.current_page * self.items_per_page)).fetchall()

        if not listings:
            tk.Label(self.root, text="No listings available.", font=("Arial", 14)).pack(pady=20)

        for listing in listings:
            frame = tk.Frame(self.root, relief="solid", borderwidth=1, padx=10, pady=5)
            frame.pack(fill="x", padx=10, pady=5)

            # Display listing details
            tk.Label(frame,
                     text=f"Title: {listing[1]} | Price: ${listing[2]} | Category: {listing[3]} | Location: {listing[4]}").pack(
                anchor="w")
            tk.Label(frame, text=f"Seller: {listing[7]} ({listing[6]})").pack(anchor="w")

            # Display image (if available)
            try:
                image_path = listing[5]
                if image_path:  # Check if the image path exists
                    image = Image.open(image_path)
                    image = image.resize((100, 100))  # Resize to fit within the UI
                    photo = ImageTk.PhotoImage(image)
                    tk.Label(frame, image=photo).pack(side="left", padx=10)
                    # Keep a reference to avoid garbage collection
                    frame.image = photo
            except Exception as e:
                print(f"Error loading image for listing {listing[1]}: {e}")
                tk.Label(frame, text="[Image Not Available]").pack(side="left", padx=10)

            # Message Seller Button
            tk.Button(
                frame,
                text="Message Seller",
                command=lambda seller_email=listing[6], listing_id=listing[0]: self.compose_message_screen(
                    seller_email, listing_id)
            ).pack(anchor="e", padx=10)

        # Pagination Controls
        nav_frame = tk.Frame(self.root)
        nav_frame.pack(pady=10)
        tk.Button(nav_frame, text="Previous", command=self.previous_page).pack(side="left", padx=5)
        tk.Button(nav_frame, text="Next", command=self.next_page).pack(side="right", padx=5)

        tk.Button(self.root, text="Back to Dashboard", command=self.dashboard).pack(pady=10)

    def compose_message_screen(self, recipient_email="", listing_id=None):
        self.clear_screen()
        tk.Label(self.root, text="Compose Message", font=("Arial", 20)).pack(pady=10)

        tk.Label(self.root, text="Recipient's Email:").pack(pady=5)
        self.recipient_email_entry = tk.Entry(self.root, width=50)
        self.recipient_email_entry.pack(pady=5)
        self.recipient_email_entry.insert(0, recipient_email)  # Ensure the email is prefilled if passed

        tk.Label(self.root, text="Message Text:").pack(pady=5)
        self.message_text_entry = tk.Text(self.root, height=10, width=60)
        self.message_text_entry.pack(pady=5)

        tk.Label(self.root, text="Listing ID (Optional):").pack(pady=5)
        self.listing_id_entry = tk.Entry(self.root, width=20)
        self.listing_id_entry.pack(pady=5)
        if listing_id:
            self.listing_id_entry.insert(0, listing_id)

        tk.Button(self.root, text="Send Message", command=lambda: self.send_message()).pack(pady=10)
        tk.Button(self.root, text="Back to Messages", command=self.messages_screen).pack(pady=5)
        tk.Button(self.root, text="Back to Browse Listings", command=self.display_listings).pack(pady=5)

    def send_message(self):
        recipient_email = self.recipient_email_entry.get().strip()  # Get the email from the input field
        message_text = self.message_text_entry.get("1.0", tk.END).strip()

        if not message_text:
            messagebox.showerror("Error", "Message text cannot be empty.")
            return

        if not recipient_email:
            messagebox.showerror("Error", "Recipient email cannot be empty.")
            return

        # Fetch recipient ID from the email
        recipient = cursor.execute("SELECT user_id FROM users WHERE email = ?", (recipient_email,)).fetchone()
        if not recipient:
            messagebox.showerror("Error", "Recipient email does not exist.")
            return
        recipient_id = recipient[0]

        try:
            # Insert the message into the database
            cursor.execute(
                """
                INSERT INTO messages (sender_id, receiver_id, message_text, timestamp, listing_id)
                VALUES (?, ?, ?, datetime('now'), ?)
                """,
                (self.user_id, recipient_id, message_text, self.listing_id_entry.get())
            )
            conn.commit()
            messagebox.showinfo("Success", "Message sent successfully!")
            self.message_text_entry.delete("1.0", tk.END)  # Clear the text box
        except Exception as e:
            messagebox.showerror("Error", f"Failed to send message: {e}")

    def next_page(self):
        self.current_page += 1
        self.display_listings()

    def previous_page(self):
        if self.current_page > 0:
            self.current_page -= 1
        self.display_listings()

    ### Clear Screen ###
    def clear_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

    ### Logout ###
    def logout(self):
        self.user_id = None
        self.login_screen()


# Initialize the Tkinter root and run the app
root = tk.Tk()
app = MarketplaceApp(root)
root.mainloop()


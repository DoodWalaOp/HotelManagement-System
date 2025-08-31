import streamlit as st
import pandas as pd
import mysql.connector
from mysql.connector import Error
from streamlit_option_menu import option_menu
import plotly.express as px

# Database connection
def get_connection():
    try:
        return mysql.connector.connect(
            host='localhost',
            user='root',
            password='adesh',  # Replace with your MySQL password
            database='HotelManagement'
        )
    except Error as e:
        st.error(f"Database connection error: {e}")
        return None

def run_query(sql, params=None):
    conn = get_connection()
    if not conn:
        return pd.DataFrame()
    try:
        with st.spinner("Loading data..."):
            df = pd.read_sql(sql, conn, params=params)
        return df
    except Exception as e:
        st.error(f"Query failed: {e}")
        return pd.DataFrame()
    finally:
        conn.close()

def format_datetime(val):
    try:
        return val.strftime('%Y-%m-%d %H:%M')
    except Exception:
        return str(val)

def main():
    st.set_page_config(page_title="Hotel Management System", layout="wide")
    st.title("🏨 Hotel Management System")

    with st.sidebar:
        st.markdown("### Menu")
        selected = option_menu(
            menu_title=None,
            options=[
                "Lodhi",
                "Guest Management",
                "Add Guests",
                "Reservations",
                "Payments",
                "Staff Directory",
                "Room Catalog",
                "Room Inventory",
                "Revenue",
                "Reviews"
            ],
            icons=[
                "building",
                "people",
                "person-plus",
                "calendar-check",
                "credit-card",
                "person-badge",
                "collection",
                "door-open",
                "bar-chart-line",
                "chat-square-text"
            ],
            menu_icon="app-indicator",
            default_index=0,
            orientation="vertical",
            styles={
                "container": {"padding": "10px 10px", "background-color": "#f9f9f9"},
                "icon": {"color": "#0a9396", "font-size": "20px"},
                "nav-link": {
                    "font-size": "17px",
                    "text-align": "left",
                    "margin": "5px 0",
                    "padding": "8px 15px",
                    "border-radius": "8px",
                    "--hover-color": "#94d2bd",
                    "color": "#005f73"
                },
                "nav-link-selected": {
                    "background-color": "#0a9396",
                    "color": "white",
                    "font-weight": "600",
                    "border-radius": "8px"
                },
            }
        )

    if selected == "Lodhi":
        show_lodhi_info()
    elif selected == "Guest Management":
        show_guests()
    elif selected == "Add Guests":
        add_guest_form()
    elif selected == "Reservations":
        show_bookings()
    elif selected == "Payments":
        show_payments()
    elif selected == "Staff Directory":
        show_staff()
    elif selected == "Room Catalog":
        show_room_types()
    elif selected == "Room Inventory":
        show_rooms()
    elif selected == "Revenue":
        show_revenue()
    elif selected == "Reviews":
        show_reviews()

def show_lodhi_info():
    st.header("The Lodhi Hotel, Delhi")
    st.image(
        "https://user-gen-media-assets.s3.amazonaws.com/gpt4o_images/2b1d2348-2a94-4058-a557-b7e616a31df2.png",
        caption="The Lodhi Hotel Exterior",
        width=600
    )
    st.markdown("""
    ### About The Lodhi Hotel

    Established in 2008, The Lodhi Hotel is a luxurious urban oasis located in the heart of Lutyens' Delhi.  
    It combines contemporary design with traditional Indian hospitality, featuring beautifully landscaped gardens and elegant interiors.  
    The hotel offers 83 rooms and suites, fine dining options, a spa, fitness center, and extensive conference facilities.  
    Its prime location provides easy access to India's iconic landmarks such as India Gate and Humayun’s Tomb.  

    The Lodhi is renowned for impeccable service and creating memorable experiences for both leisure and business travelers.
    """)

def show_guests():
    st.header("Guest Management")

    count_df = run_query("SELECT COUNT(*) AS total FROM Guest")
    total_guests = count_df['total'][0] if not count_df.empty else 0
    st.markdown(f"**Total Guests:** {total_guests}")

    # Fetch guest data including address and last booking date
    sql = """
        SELECT g.GuestID, g.FirstName, g.LastName, g.Email, g.DateOfBirth, g.Phone, g.Address,
               MAX(b.CheckinDate) AS LastBookingDate
        FROM Guest g
        LEFT JOIN Booking b ON g.GuestID = b.GuestID
        GROUP BY g.GuestID
        ORDER BY g.LastName, g.FirstName
    """
    guests = run_query(sql)
    if guests.empty:
        st.warning("No guests found.")
        return

    guests['DateOfBirth'] = guests['DateOfBirth'].astype(str)
    guests['LastBookingDate'] = guests['LastBookingDate'].astype(str)

    search = st.text_input("Search Guests by Name, Email or Address:")
    if search:
        mask = (
            guests['FirstName'].str.contains(search, case=False, na=False) |
            guests['LastName'].str.contains(search, case=False, na=False) |
            guests['Email'].str.contains(search, case=False, na=False) |
            guests['Address'].str.contains(search, case=False, na=False)
        )
        filtered = guests.loc[mask]
        st.write(f"Showing {len(filtered)} results for '{search}'")
        display_df = filtered
    else:
        display_df = guests

    guests_per_page = 20
    total_pages = (len(display_df) - 1) // guests_per_page + 1
    page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1)
    start = (page - 1) * guests_per_page
    end = start + guests_per_page

    # Show table with specified columns including new ones
    show_columns = ['FirstName', 'LastName', 'Email', 'Phone', 'Address', 'DateOfBirth', 'LastBookingDate']
    st.dataframe(display_df.iloc[start:end][show_columns])

def add_guest_form():
    st.header("Add New Guest")

    with st.form("guest_form", clear_on_submit=True):
        first_name = st.text_input("First Name", max_chars=50)
        last_name = st.text_input("Last Name", max_chars=50)
        email = st.text_input("Email", max_chars=100)
        dob = st.date_input("Date of Birth")
        phone = st.text_input("Phone Number", max_chars=15)
        address = st.text_area("Address", max_chars=255)

        submitted = st.form_submit_button("Add Guest")
        if submitted:
            if not first_name or not last_name or not email:
                st.warning("Please enter at least First Name, Last Name, and Email.")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    insert_sql = """
                        INSERT INTO Guest (FirstName, LastName, Email, DateOfBirth, Phone, Address)
                        VALUES (%s, %s, %s, %s, %s, %s)
                    """
                    cursor.execute(insert_sql, (first_name, last_name, email, dob.strftime('%Y-%m-%d'), phone, address))
                    conn.commit()
                    st.success(f"Guest {first_name} {last_name} added successfully!")
                except Exception as e:
                    st.error(f"Error inserting guest: {e}")
                finally:
                    if cursor:
                        cursor.close()
                    if conn:
                        conn.close()

# Other existing functions (show_bookings, show_payments, show_staff, show_room_types, show_rooms, show_revenue, show_reviews)
# remain unchanged from the previously provided full app code, so include them here as well.

def show_bookings():
    st.header("Reservations")
    bookings = run_query("""
        SELECT b.BookingID, g.FirstName, g.LastName, r.RoomNumber,
               b.CheckinDate, b.CheckoutDate, b.TotalPrice
        FROM Booking b
        JOIN Guest g ON b.GuestID = g.GuestID
        JOIN Room r ON b.RoomNumber = r.RoomNumber
        ORDER BY b.CheckinDate DESC
        """)
    if bookings.empty:
        st.warning("No bookings found.")
        return
    bookings['CheckinDate'] = bookings['CheckinDate'].astype(str)
    bookings['CheckoutDate'] = bookings['CheckoutDate'].astype(str)
    st.dataframe(bookings)

def show_payments():
    st.header("Payments")
    payments = run_query("""
        SELECT p.PaymentID, p.BookingID, p.Amount, p.PaymentDate, p.PaymentMethod
        FROM Payment p
        ORDER BY p.PaymentDate DESC
        """)
    if payments.empty:
        st.warning("No payments found.")
        return
    payments['PaymentDate'] = payments['PaymentDate'].astype(str)
    st.dataframe(payments)

def show_staff():
    st.header("Staff Directory")
    staff = run_query("""
        SELECT s.StaffID, s.FirstName, s.LastName, s.Role, s.Phone, s.Email, h.Name as HotelName
        FROM Staff s
        JOIN Hotel h ON s.HotelID = h.HotelID
        ORDER BY h.Name, s.LastName
        """)
    if staff.empty:
        st.warning("No staff records found.")
        return
    st.dataframe(staff)

def show_room_types():
    st.header("Room Catalog")
    room_types = run_query("SELECT * FROM RoomType ORDER BY Name")
    if room_types.empty:
        st.warning("No room types found.")
        return
    st.dataframe(room_types)

def show_rooms():
    st.header("Room Inventory")
    rooms = run_query("""
        SELECT r.RoomNumber, r.Status, h.Name as HotelName, rt.Name as RoomTypeName
        FROM Room r
        JOIN Hotel h ON r.HotelID = h.HotelID
        JOIN RoomType rt ON r.TypeID = rt.TypeID
        ORDER BY h.Name, r.RoomNumber
        """)
    if rooms.empty:
        st.warning("No rooms found.")
        return
    st.dataframe(rooms)

def show_revenue():
    st.header("Monthly Revenue")
    sql = """
        SELECT 
            YEAR(CheckinDate) AS Year,
            MONTH(CheckinDate) AS Month,
            SUM(TotalPrice) AS Revenue
        FROM Booking
        GROUP BY Year, Month
        ORDER BY Year, Month
    """
    df = run_query(sql)
    if df.empty:
        st.info("No revenue data available.")
        return
    df['YearMonth'] = df.apply(
        lambda row: f"{int(row.Year)}-{int(row.Month):02d}" if pd.notnull(row.Year) and pd.notnull(row.Month) else "",
        axis=1
    )
    df['Revenue'] = df['Revenue'] * 10000000  # Scale revenue to crores
    st.markdown("*(Revenue values scaled to crores)*")
    fig = px.bar(df, x='YearMonth', y='Revenue', title="Monthly Revenue (INR)", labels={'YearMonth': 'Month', 'Revenue': 'Revenue (₹)'})
    st.plotly_chart(fig, use_container_width=True)

def show_reviews():
    st.header("Customer Reviews")
    lodhi_hotel = run_query("SELECT HotelID FROM Hotel WHERE Name = 'The Lodhi'")
    if lodhi_hotel.empty:
        st.warning("Lodhi hotel data not found.")
        return
    hotel_id = int(lodhi_hotel.iloc[0]['HotelID'])

    sql = """
        SELECT r.Rating, r.Comment, r.Timestamp, g.FirstName, g.LastName
        FROM Review r
        JOIN Guest g ON r.GuestID = g.GuestID
        JOIN (
            SELECT GuestID, MAX(Timestamp) AS LatestTimestamp
            FROM Review
            WHERE HotelID = %s
            GROUP BY GuestID
        ) lr ON r.GuestID = lr.GuestID AND r.Timestamp = lr.LatestTimestamp
        WHERE r.HotelID = %s
        ORDER BY r.Timestamp DESC
    """
    reviews = run_query(sql, (hotel_id, hotel_id))
    if reviews.empty:
        st.info("No reviews available for The Lodhi.")
        return
    for _, review in reviews.iterrows():
        st.markdown(f"**{review['FirstName']} {review['LastName']}** — {format_datetime(review['Timestamp'])}")
        stars = '⭐' * int(round(review['Rating']))
        st.markdown(f"Rating: {stars} ({review['Rating']})")
        st.write(review['Comment'])
        st.markdown("---")

if __name__ == "__main__":
    main()

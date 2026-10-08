import sqlite3
import random
from datetime import date, datetime, timedelta

DB_FILE = "burkin_auto.db"

# Sample Staff Members
STAFF = [
    ("101", "M. B. Sajeev", "Senior Mechanic"),
    ("102", "Rahul V. Nair", "Assistant Mechanic"),
    ("103", "Faisal Rahman", "Auto Electrician"),
    ("104", "Sreejith Kumar", "Diagnostic Technician"),
    ("105", "Shaji Mohammad", "AC Lead Technician"),
    ("106", "K. V. Antony", "Denter"),
    ("107", "Biju Mathew", "Painter"),
]

# Specific holidays in Sept 2026 (Optional)
SEPT_HOLIDAYS = [
    ("2026-10-07", "Labour / Workshop Maintenance Day")
]

def calculate_shift_metrics(check_in_str, check_out_str, date_str):
    fmt = "%Y-%m-%d %H:%M:%S"
    dt_in = datetime.strptime(f"{date_str} {check_in_str}", fmt)
    dt_out = datetime.strptime(f"{date_str} {check_out_str}", fmt)
    
    total_seconds = (dt_out - dt_in).total_seconds()
    total_hours = round(total_seconds / 3600.0, 2)
    
    window_start = datetime.strptime(f"{date_str} 09:00:00", fmt)
    window_end = datetime.strptime(f"{date_str} 20:00:00", fmt)
    
    reg_start = max(dt_in, window_start)
    reg_end = min(dt_out, window_end)
    
    if reg_end > reg_start:
        regular_seconds = (reg_end - reg_start).total_seconds()
        regular_hours = round(regular_seconds / 3600.0, 2)
    else:
        regular_hours = 0.0
        
    covered = "Yes" if regular_hours >= 10.5 else "No"
    return total_hours, regular_hours, covered

def seed_database():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    # 1. Ensure Employees exist
    for emp_id, name, role in STAFF:
        c.execute("""
            INSERT OR IGNORE INTO employees (emp_id, name, role) 
            VALUES (?, ?, ?)
        """, (emp_id, name, role))
        
    # 2. Add Holidays
    for h_date, h_desc in SEPT_HOLIDAYS:
        c.execute("""
            INSERT OR IGNORE INTO holidays (holiday_date, description) 
            VALUES (?, ?)
        """, (h_date, h_desc))
        
    holiday_dates = {h[0] for h in SEPT_HOLIDAYS}
    
    # 3. Generate Daily Records for September 2026
    start_date = date(2026, 10, 1)
    end_date = date(2026, 10, 30)
    
    curr_date = start_date
    records_added = 0
    
    while curr_date <= end_date:
        date_str = curr_date.strftime("%Y-%m-%d")
        day_of_week = curr_date.weekday() # 0=Mon, 5=Sat, 6=Sun
        
        # Skip Sundays and official holidays
        if day_of_week != 6 and date_str not in holiday_dates:
            for emp_id, _, _ in STAFF:
                # Add realistic variance (e.g., ~10% chance an employee is absent)
                if random.random() < 0.10:
                    continue  # Employee absent today
                
                # Check-in time variance: usually between 08:45 and 09:30
                check_in_min = random.randint(45, 90)
                check_in_dt = datetime.strptime(f"{date_str} 08:00:00", "%Y-%m-%d %H:%M:%S") + timedelta(minutes=check_in_min)
                check_in_str = check_in_dt.strftime("%H:%M:%S")
                
                # Check-out time variance: usually between 19:45 and 20:30
                check_out_min = random.randint(645, 690)
                check_out_dt = datetime.strptime(f"{date_str} 09:00:00", "%Y-%m-%d %H:%M:%S") + timedelta(minutes=check_out_min)
                check_out_str = check_out_dt.strftime("%H:%M:%S")
                
                tot_hrs, reg_hrs, covered = calculate_shift_metrics(check_in_str, check_out_str, date_str)
                
                # Prevent duplicate entries for the same day
                c.execute("SELECT id FROM attendance WHERE emp_id = ? AND date = ?", (emp_id, date_str))
                if c.fetchone() is None:
                    c.execute("""
                        INSERT INTO attendance (emp_id, date, check_in, check_out, total_hours, regular_hours, covered_regular_shift)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (emp_id, date_str, check_in_str, check_out_str, tot_hrs, reg_hrs, covered))
                    records_added += 1
                    
        curr_date += timedelta(days=1)
        
    conn.commit()
    conn.close()
    
    print(f"✅ Database updated successfully! Added {records_added} attendance logs for September 2026.")

if __name__ == "__main__":
    seed_database()
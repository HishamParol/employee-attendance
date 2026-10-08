import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime, date, timedelta
import altair as alt

# --- REPORTLAB PDF IMPORTS ---
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

# --- IMPORT CONFIGURATION VARIABLES ---
import config

# --- 1. PAGE CONFIG & CUSTOM THEMING ---
st.set_page_config(
    page_title=f"{config.COMPANY_NAME} - Attendance Kiosk",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom High-Contrast CSS using Specified Palette
st.markdown("""
    <style>
    /* Main App Background - Charcoal Black */
    .stApp {
        background-color: #17191C !important;
        color: #FFFFFF !important;
    }
    
    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #454B52 !important;
        border-right: 1px solid #17191C !important;
    }
    section[data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }
    
    /* Labels, Paragraphs, Headings - High Contrast White */
    label, p, span, h1, h2, h3, h4, h5, h6, .stMarkdown {
        color: #FFFFFF !important;
    }
    
    /* Text Input & Dropdown Container Styling - Light Grey Background */
    div[data-baseweb="input"] > div, 
    div[data-baseweb="select"] > div,
    div[data-baseweb="base-input"] {
        background-color: #EEF0F2 !important;
        border: 2px solid #454B52 !important;
        border-radius: 8px !important;
    }
    
    /* Input Text & Selected Text - Dark Charcoal Black for High Visibility */
    div[data-baseweb="input"] input, 
    div[data-baseweb="select"] * {
        color: #17191C !important;
        font-weight: 700 !important;
    }
    
    /* Input Placeholder Text */
    ::placeholder {
        color: #454B52 !important;
        opacity: 0.8 !important;
    }
    
    /* --- BUTTON STYLING (Standard, Form Submit, and Download Buttons) --- */
    .stButton > button, 
    div[data-testid="stFormSubmitButton"] > button,
    div[data-testid="stDownloadButton"] > button {
        background-color: #F05A28 !important;
        background-image: none !important;
        color: #FFFFFF !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 8px !important;
        transition: all 0.2s ease !important;
    }
    
    /* Force inner text & paragraph elements inside buttons to stay white */
    .stButton > button *, 
    div[data-testid="stFormSubmitButton"] > button *,
    div[data-testid="stDownloadButton"] > button * {
        color: #FFFFFF !important;
        fill: #FFFFFF !important;
        font-weight: 700 !important;
    }
    
    /* Hover State */
    .stButton > button:hover, 
    div[data-testid="stFormSubmitButton"] > button:hover,
    div[data-testid="stDownloadButton"] > button:hover {
        background-color: #d84e20 !important;
        color: #FFFFFF !important;
    }
    
    /* --- CIRCULAR KIOSK ACTION BUTTONS (GREEN & RED) --- */
    div.circle-in > button {
        background: #2E7D32 !important;
        background-image: linear-gradient(135deg, #2E7D32, #1B5E20) !important;
        color: #FFFFFF !important;
        width: 160px !important;
        height: 160px !important;
        border-radius: 50% !important;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        border: 4px solid #4CAF50 !important;
        box-shadow: 0 10px 25px rgba(76, 175, 80, 0.4) !important;
        margin: 0 auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    div.circle-in > button:hover {
        background: #1B5E20 !important;
        border-color: #81C784 !important;
        transform: scale(1.05);
    }
    
    div.circle-out > button {
        background: #D32F2F !important;
        background-image: linear-gradient(135deg, #D32F2F, #C62828) !important;
        color: #FFFFFF !important;
        width: 160px !important;
        height: 160px !important;
        border-radius: 50% !important;
        font-size: 1.25rem !important;
        font-weight: 800 !important;
        border: 4px solid #FF5252 !important;
        box-shadow: 0 10px 25px rgba(211, 47, 47, 0.4) !important;
        margin: 0 auto !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
    }

    div.circle-out > button:hover {
        background: #B71C1C !important;
        border-color: #FF8A80 !important;
        transform: scale(1.05);
    }
    
    /* Dataframes and Tables */
    div[data-testid="stDataFrame"] {
        background-color: #EEF0F2 !important;
        border-radius: 8px !important;
        padding: 4px;
    }
    div[data-testid="stDataFrame"] * {
        color: #17191C !important;
    }

    .main-title {
        color: #F05A28 !important;
        font-weight: 800;
        font-size: 2.3rem;
        text-align: center;
        margin-bottom: 0px;
    }
    .sub-title {
        color: #EEF0F2 !important;
        font-size: 1.1rem;
        text-align: center;
        margin-bottom: 25px;
    }
    
    .employee-card {
        background-color: #454B52;
        border: 1px solid #F05A28;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)


# --- 2. DATABASE SETUP ---
DB_FILE = "burkin_auto.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS employees (
            emp_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            role TEXT DEFAULT 'Mechanic'
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            emp_id TEXT NOT NULL,
            date TEXT NOT NULL,
            check_in TEXT NOT NULL,
            check_out TEXT,
            total_hours REAL DEFAULT 0.0,
            regular_hours REAL DEFAULT 0.0,
            covered_regular_shift TEXT DEFAULT 'No',
            FOREIGN KEY (emp_id) REFERENCES employees (emp_id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS holidays (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            holiday_date TEXT NOT NULL UNIQUE,
            description TEXT NOT NULL
        )
    ''')
    
    c.execute("SELECT COUNT(*) FROM employees")
    if c.fetchone()[0] == 0:
        default_staff = [
            ("101", "Marcus Vance", "Senior Mechanic"),
            ("102", "Elena Rostova", "Auto Electrician"),
            ("103", "Dave Miller", "Bodywork Technician"),
            ("104", "Sam Jenkins", "Garage Manager")
        ]
        c.executemany("INSERT INTO employees VALUES (?, ?, ?)", default_staff)
        
    conn.commit()
    conn.close()

init_db()

def get_db():
    return sqlite3.connect(DB_FILE)


# --- 3. HELPER FUNCTIONS ---
def calculate_shift_metrics(check_in_str, check_out_str, date_str):
    fmt = "%Y-%m-%d %H:%M:%S"
    dt_in = datetime.strptime(f"{date_str} {check_in_str}", fmt)
    dt_out = datetime.strptime(f"{date_str} {check_out_str}", fmt)
    
    if dt_out < dt_in:
        dt_out = dt_out.replace(day=dt_out.day + 1)
        
    total_seconds = (dt_out - dt_in).total_seconds()
    total_hours = round(total_seconds / 3600.0, 2)
    
    window_start = datetime.strptime(f"{date_str} {config.WORK_START_TIME}", fmt)
    window_end = datetime.strptime(f"{date_str} {config.WORK_END_TIME}", fmt)
    
    reg_start = max(dt_in, window_start)
    reg_end = min(dt_out, window_end)
    
    if reg_end > reg_start:
        regular_seconds = (reg_end - reg_start).total_seconds()
        regular_hours = round(regular_seconds / 3600.0, 2)
    else:
        regular_hours = 0.0
        
    covered = "Yes" if regular_hours >= config.EXPECTED_DAILY_REGULAR_HOURS else "No"
    return total_hours, regular_hours, covered


def count_working_days_in_month(year, month):
    conn = get_db()
    holidays_df = pd.read_sql_query("SELECT holiday_date FROM holidays", conn)
    conn.close()
    
    holiday_dates = set(holidays_df['holiday_date'].tolist()) if not holidays_df.empty else set()
    
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)
        
    working_days = 0
    curr = start_date
    while curr <= end_date:
        if curr.weekday() in [0, 1, 2, 3, 4, 5] and curr.strftime("%Y-%m-%d") not in holiday_dates:
            working_days += 1
        curr += timedelta(days=1)
        
    return working_days


def generate_payroll_pdf(emp_info, month_iso, work_days_count, days_attended, tot_hrs_sum, reg_hrs_sum, rep_attendance):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )
    
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CompanyTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=18,
        textColor=colors.HexColor('#F05A28'),
        spaceAfter=2
    )
    
    tagline_style = ParagraphStyle(
        'CompanyTagline',
        parent=styles['Normal'],
        fontName='Helvetica-Oblique',
        fontSize=9,
        textColor=colors.HexColor('#454B52'),
        spaceAfter=4
    )
    
    address_style = ParagraphStyle(
        'CompanyAddress',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8,
        textColor=colors.HexColor('#17191C'),
        leading=11
    )
    
    section_title = ParagraphStyle(
        'SectionTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=12,
        textColor=colors.HexColor('#17191C'),
        spaceBefore=10,
        spaceAfter=6
    )

    story = []

    header_data = [
        [
            Paragraph(f"<b>{config.COMPANY_NAME}</b>", title_style),
            Paragraph(f"<b>PAYROLL & ATTENDANCE STATEMENT</b>", ParagraphStyle('RightTitle', parent=title_style, fontSize=12, alignment=2, textColor=colors.HexColor('#17191C')))
        ],
        [
            Paragraph(config.COMPANY_TAGLINE, tagline_style),
            Paragraph(f"Period: <b>{month_iso}</b>", ParagraphStyle('RightPeriod', parent=address_style, alignment=2))
        ],
        [
            Paragraph(f"{config.COMPANY_ADDRESS}<br/>Phone: {config.COMPANY_PHONE} | Email: {config.COMPANY_EMAIL}<br/>{config.COMPANY_REG_NO}", address_style),
            Paragraph(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}", ParagraphStyle('RightDate', parent=address_style, alignment=2))
        ]
    ]
    
    header_table = Table(header_data, colWidths=[340, 200])
    header_table.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#F05A28'), spaceAfter=15))

    attendance_rate = round((days_attended / work_days_count) * 100, 1) if work_days_count > 0 else 0
    kpi_status = "PASSED TARGET" if attendance_rate >= config.KPI_ATTENDANCE_TARGET_PCT else "NEEDS IMPROVEMENT"
    kpi_color = colors.HexColor('#F05A28') if attendance_rate >= config.KPI_ATTENDANCE_TARGET_PCT else colors.HexColor('#17191C')

    story.append(Paragraph("Employee Summary & Key Performance Indicators (KPIs)", section_title))
    
    summary_data = [
        ["Employee ID:", emp_info['emp_id'], "Working Days in Month:", str(work_days_count)],
        ["Employee Name:", emp_info['name'], "Days Attended / Absent:", f"{days_attended} / {max(0, work_days_count - days_attended)}"],
        ["Role / Position:", emp_info['role'], "Attendance Rate (KPI):", f"{attendance_rate}% ({kpi_status})"],
        ["Total Hours Logged:", f"{round(tot_hrs_sum, 2)} hrs", "Regular Hours Covered:", f"{round(reg_hrs_sum, 2)} hrs"]
    ]
    
    summary_table = Table(summary_data, colWidths=[120, 150, 140, 130])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#EEF0F2')),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#454B52')),
        ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
        ('FONTNAME', (2,0), (2,-1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#17191C')),
        ('FONTSIZE', (0,0), (-1,-1), 9),
        ('PADDING', (0,0), (-1,-1), 6),
        ('TEXTCOLOR', (3,2), (3,2), kpi_color),
        ('FONTNAME', (3,2), (3,2), 'Helvetica-Bold'),
    ]))
    story.append(summary_table)
    story.append(Spacer(1, 15))

    story.append(Paragraph("Daily Shift Logs", section_title))
    
    table_headers = ["Date", "Check-In", "Check-Out", "Total Hrs", "Regular Hrs", "Shift Target Met"]
    table_rows = [table_headers]
    
    if not rep_attendance.empty:
        for _, row in rep_attendance.iterrows():
            table_rows.append([
                str(row['date']),
                str(row['check_in']),
                str(row['check_out']) if pd.notna(row['check_out']) else "ACTIVE",
                f"{row['total_hours']:.2f}",
                f"{row['regular_hours']:.2f}",
                str(row['covered_regular_shift'])
            ])
    else:
        table_rows.append(["No attendance logs found for this period.", "", "", "", "", ""])

    log_table = Table(table_rows, colWidths=[80, 80, 80, 80, 100, 120])
    log_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#454B52')),
        ('TEXTCOLOR', (0,0), (-1,0), colors.HexColor('#FFFFFF')),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 8.5),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor('#454B52')),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.HexColor('#FFFFFF'), colors.HexColor('#EEF0F2')]),
        ('PADDING', (0,0), (-1,-1), 5),
    ]))
    story.append(log_table)
    
    story.append(Spacer(1, 25))
    auth_data = [
        ["_________________________", "_________________________"],
        ["Employee Signature", "Manager / Payroll Approval"]
    ]
    auth_table = Table(auth_data, colWidths=[270, 270])
    auth_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('FONTNAME', (0,1), (-1,1), 'Helvetica-Oblique'),
        ('FONTSIZE', (0,0), (-1,-1), 8),
        ('TEXTCOLOR', (0,0), (-1,-1), colors.HexColor('#454B52')),
    ]))
    story.append(auth_table)

    doc.build(story)
    buffer.seek(0)
    return buffer


# --- 4. SESSION STATE FOR NAVIGATION ---
if 'view_mode' not in st.session_state:
    st.session_state.view_mode = "kiosk"

if 'validated_emp_id' not in st.session_state:
    st.session_state.validated_emp_id = None

if 'admin_authenticated' not in st.session_state:
    st.session_state.admin_authenticated = False


# ==============================================================================
# PAGE 1: MOBILE KIOSK VIEW (DEFAULT OPENING PAGE)
# ==============================================================================
if st.session_state.view_mode == "kiosk":
    st.markdown("<h1 class='main-title'>Burkin Auto Employee Attendance Sheet</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-title'>Workshop Attendance Kiosk</p>", unsafe_allow_html=True)
    
    col_input, col_btn = st.columns([3, 1])
    with col_input:
        input_id = st.text_input("🆔 Enter Employee ID", value="", max_chars=10, key="kiosk_id_input", label_visibility="collapsed", placeholder="Enter Employee ID...")
    with col_btn:
        if st.button("OK / Submit", use_container_width=True):
            if input_id.strip():
                st.session_state.validated_emp_id = input_id.strip()
            else:
                st.session_state.validated_emp_id = None
                
    st.write("---")
    
    # Process Employee Action after clicking OK
    if st.session_state.validated_emp_id:
        emp_id = st.session_state.validated_emp_id
        conn = get_db()
        c = conn.cursor()
        c.execute("SELECT name, role FROM employees WHERE emp_id = ?", (emp_id,))
        employee = c.fetchone()
        
        if not employee:
            st.error("❌ Employee ID not found. Please try again or contact your manager.")
        else:
            emp_name, emp_role = employee
            today_str = datetime.now().strftime("%Y-%m-%d")
            
            c.execute("""
                SELECT id, check_in FROM attendance 
                WHERE emp_id = ? AND date = ? AND check_out IS NULL 
                ORDER BY id DESC LIMIT 1
            """, (emp_id, today_str))
            
            active_shift = c.fetchone()
            conn.close()
            
            # Display Employee Info Box
            st.markdown(f"""
                <div class="employee-card">
                    <h3 style="margin:0; color:#FFFFFF;">{emp_name}</h3>
                    <p style="margin:5px 0 0 0; color:#EEF0F2;"><b>Role:</b> {emp_role} | <b>ID:</b> {emp_id}</p>
                </div>
            """, unsafe_allow_html=True)
            
            c_left, c_mid, c_right = st.columns([1, 1, 1])
            with c_mid:
                if active_shift is None:
                    # Circular Green Check-In Button Container
                    st.markdown('<div class="circle-in">', unsafe_allow_html=True)
                    if st.button("CHECK IN", key="btn_check_in"):
                        conn = get_db()
                        c = conn.cursor()
                        now_time = datetime.now().strftime("%H:%M:%S")
                        c.execute("INSERT INTO attendance (emp_id, date, check_in) VALUES (?, ?, ?)", 
                                  (emp_id, today_str, now_time))
                        conn.commit()
                        conn.close()
                        st.success(f"🎉 **Check-In Recorded!** Marked at {now_time}")
                        st.session_state.validated_emp_id = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)
                else:
                    shift_id, check_in_time = active_shift
                    # Circular Red Check-Out Button Container
                    st.markdown('<div class="circle-out">', unsafe_allow_html=True)
                    if st.button("CHECK OUT", key="btn_check_out"):
                        conn = get_db()
                        c = conn.cursor()
                        now_time = datetime.strftime(datetime.now(), "%H:%M:%S")
                        tot_hrs, reg_hrs, covered = calculate_shift_metrics(check_in_time, now_time, today_str)
                        
                        c.execute("""
                            UPDATE attendance 
                            SET check_out = ?, total_hours = ?, regular_hours = ?, covered_regular_shift = ?
                            WHERE id = ?
                        """, (now_time, tot_hrs, reg_hrs, covered, shift_id))
                        conn.commit()
                        conn.close()
                        
                        st.success(f"👋 **Check-Out Recorded!** Marked at {now_time}. Total Shift: {tot_hrs} hrs.")
                        st.session_state.validated_emp_id = None
                        st.rerun()
                    st.markdown('</div>', unsafe_allow_html=True)

    # Small Admin Button at bottom of page
    st.write("<br><br><br>", unsafe_allow_html=True)
    st.write("---")
    b_col1, b_col2, b_col3 = st.columns([2, 1, 2])
    with b_col2:
        if st.button("🔒 Admin Login", use_container_width=True):
            st.session_state.view_mode = "admin"
            st.rerun()


# ==============================================================================
# PAGE 2: ADMIN DASHBOARD VIEW
# ==============================================================================
elif st.session_state.view_mode == "admin":
    st.title(f"🔒 {config.COMPANY_NAME.split()[0]} Auto — Admin Portal")
    
    top_col1, top_col2 = st.columns([4, 1])
    with top_col2:
        if st.button("👈 Back to Kiosk", use_container_width=True):
            st.session_state.admin_authenticated = False
            st.session_state.view_mode = "kiosk"
            st.rerun()

    # Check authentication state
    if not st.session_state.admin_authenticated:
        admin_pass = st.text_input("🔑 Enter Admin Password", type="password")
        if admin_pass:
            if admin_pass == config.ADMIN_PASSWORD:
                st.session_state.admin_authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect Admin Password.")
        else:
            st.warning(f"Please enter the admin password.")
    
    if st.session_state.admin_authenticated:
        st.success("Authenticated as Administrator")
        
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📅 Visual Dashboard & Timelines",
            "✏️ Edit Check-Ins & Holidays",
            "📈 Monthly Performance",
            "🖨 Printable Employee Report",
            "👥 Staff Management"
        ])
        
        # ----------------------------------------------------------------------
        # TAB 1: VISUAL DASHBOARD & EMPLOYEE TIMELINES
        # ----------------------------------------------------------------------
        with tab1:
            st.subheader("📅 Today's Live Attendance Dashboard")
            
            c_date, c_legend = st.columns([1, 1])
            with c_date:
                dashboard_date = st.date_input("Select Date", value=date.today())
                today_iso = dashboard_date.strftime("%Y-%m-%d")
                st.markdown(f"### Date: **{dashboard_date.strftime('%A, %B %d, %Y')}**")
            
            with c_legend:
                st.markdown("""
                **Timeline Legend:**
                * 🟢 **Green**: Covered Regular Shift Met (` covered_regular_shift = Yes `)
                * 🔴 **Red**: Regular Shift Hours Not Met (` covered_regular_shift = No `)
                * 🟡 **Yellow**: Garage Holiday
                * ⚪ **Grey**: No Check-In / Absent
                """)
            
            conn = get_db()
            employees_df = pd.read_sql_query("SELECT emp_id, name, role FROM employees", conn)
            today_attendance = pd.read_sql_query("""
                SELECT emp_id, check_in, check_out, covered_regular_shift 
                FROM attendance 
                WHERE date = ?
            """, conn, params=[today_iso])
            
            is_holiday_df = pd.read_sql_query("SELECT description FROM holidays WHERE holiday_date = ?", conn, params=[today_iso])
            conn.close()
            
            is_holiday = not is_holiday_df.empty
            holiday_desc = is_holiday_df['description'].values[0] if is_holiday else ""

            timeline_rows = []
            now_str = datetime.now().strftime("%H:%M:%S")
            
            for _, emp in employees_df.iterrows():
                e_id = emp['emp_id']
                e_name = f"{emp['name']} ({e_id})"
                
                if is_holiday:
                    # Holiday Block (Yellow)
                    timeline_rows.append({
                        "Employee": e_name,
                        "Status": f"Holiday: {holiday_desc}",
                        "Start": f"{today_iso} 06:00:00",
                        "End": f"{today_iso} 23:59:59",
                        "Color": "#FBC02D"
                    })
                else:
                    att = today_attendance[today_attendance['emp_id'] == e_id]
                    if not att.empty:
                        for _, row in att.iterrows():
                            c_in = str(row['check_in']).strip() if pd.notna(row['check_in']) else config.WORK_START_TIME
                            c_out_raw = row['check_out']
                            
                            if pd.isna(c_out_raw) or str(c_out_raw).strip().lower() in ["none", "nan", ""]:
                                # Shift currently active
                                c_out = now_str if today_iso == date.today().strftime("%Y-%m-%d") else config.WORK_END_TIME
                                shift_status = "Active Shift"
                            else:
                                c_out = str(c_out_raw).strip()
                                shift_status = "Shift Logged"
                            
                            is_covered = str(row['covered_regular_shift']).strip().capitalize() == "Yes"
                            bar_color = "#2E7D32" if is_covered else "#D32F2F"
                            status_lbl = f"{shift_status} (Met Target: {row['covered_regular_shift']})"

                            timeline_rows.append({
                                "Employee": e_name,
                                "Status": status_lbl,
                                "Start": f"{today_iso} {c_in}",
                                "End": f"{today_iso} {c_out}",
                                "Color": bar_color
                            })
                    else:
                        # Absent / Not Checked In (Grey)
                        timeline_rows.append({
                            "Employee": e_name,
                            "Status": "Absent / No Check-In",
                            "Start": f"{today_iso} 06:00:00",
                            "End": f"{today_iso} 06:15:00",
                            "Color": "#616161"
                        })
                    
            chart_data = pd.DataFrame(timeline_rows)
            chart_data['Start'] = pd.to_datetime(chart_data['Start'])
            chart_data['End'] = pd.to_datetime(chart_data['End'])
            
            # Base timeline chart
            bars = alt.Chart(chart_data).mark_bar(cornerRadius=4, height=20).encode(
                x=alt.X('Start:T', 
                        title='Time of Day (06:00 - 24:00)', 
                        scale=alt.Scale(domain=[f"{today_iso} 06:00:00", f"{today_iso} 23:59:59"]),
                        axis=alt.Axis(format='%H:%M', tickCount=18)),
                x2='End:T',
                y=alt.Y('Employee:N', title='Employees'),
                color=alt.Color('Color:N', scale=None, legend=None),
                tooltip=['Employee', 'Status', alt.Tooltip('Start:T', format='%H:%M:%S'), alt.Tooltip('End:T', format='%H:%M:%S')]
            )

            # Office Start & End Rules Markers
            rules_df = pd.DataFrame([
                {"Time": f"{today_iso} {config.WORK_START_TIME}", "Label": f"Office Start ({config.WORK_START_TIME})"},
                {"Time": f"{today_iso} {config.WORK_END_TIME}", "Label": f"Office End ({config.WORK_END_TIME})"}
            ])
            rules_df['Time'] = pd.to_datetime(rules_df['Time'])

            office_rules = alt.Chart(rules_df).mark_rule(
                color='#F05A28', 
                strokeWidth=2, 
                strokeDash=[4, 4]
            ).encode(
                x='Time:T',
                tooltip=['Label']
            )

            chart = (bars + office_rules).properties(
                width='container', 
                height=380,
                background='transparent'
            ).configure_axis(
                labelColor='#FFFFFF',
                titleColor='#FFFFFF',
                tickColor='#FFFFFF',
                domainColor='#454B52',
                gridColor='#454B52',
                labelFontSize=12,
                titleFontSize=14
            ).configure_view(
                strokeWidth=0
            )
            
            st.altair_chart(chart, use_container_width=True)

        # ----------------------------------------------------------------------
        # TAB 2: EDIT CHECK-INS & HOLIDAYS
        # ----------------------------------------------------------------------
        with tab2:
            st.subheader("✏️ Edit Attendance Records & Manage Holidays")
            col_edit, col_hol = st.columns([1.2, 0.8])
            
            with col_edit:
                st.markdown("#### 🛠 Edit Existing Check-In / Check-Out Log")
                conn = get_db()
                logs_df = pd.read_sql_query("""
                    SELECT a.id, a.emp_id, e.name, a.date, a.check_in, a.check_out 
                    FROM attendance a
                    JOIN employees e ON a.emp_id = e.emp_id
                    ORDER BY a.id DESC LIMIT 30
                """, conn)
                conn.close()
                
                if not logs_df.empty:
                    selected_log_id = st.selectbox(
                        "Select Log Record to Edit", 
                        logs_df['id'].tolist(),
                        format_func=lambda x: f"Log #{x} - {logs_df[logs_df['id']==x]['name'].values[0]} ({logs_df[logs_df['id']==x]['date'].values[0]})"
                    )
                    
                    row = logs_df[logs_df['id'] == selected_log_id].iloc[0]
                    
                    with st.form("edit_log_form"):
                        st.write(f"Editing record for: **{row['name']}** on **{row['date']}**")
                        new_in = st.text_input("Check-In Time (HH:MM:SS)", value=row['check_in'])
                        
                        out_val = row['check_out']
                        default_out = config.WORK_END_TIME if (pd.isna(out_val) or str(out_val).strip().lower() in ["nan", "none", ""]) else str(out_val)
                        new_out = st.text_input("Check-Out Time (HH:MM:SS)", value=default_out)
                        
                        if st.form_submit_button("Update Log Entry"):
                            tot, reg, cov = calculate_shift_metrics(new_in, new_out, row['date'])
                            conn = get_db()
                            c = conn.cursor()
                            c.execute("""
                                UPDATE attendance 
                                SET check_in = ?, check_out = ?, total_hours = ?, regular_hours = ?, covered_regular_shift = ?
                                WHERE id = ?
                            """, (new_in, new_out, tot, reg, cov, selected_log_id))
                            conn.commit()
                            conn.close()
                            st.success("Updated record successfully!")
                            st.rerun()
                else:
                    st.info("No attendance records found.")

            with col_hol:
                st.markdown("#### 🌴 Add Garage Holiday")
                with st.form("add_holiday_form", clear_on_submit=True):
                    h_date = st.date_input("Holiday Date", value=date.today())
                    h_desc = st.text_input("Description / Reason", placeholder="e.g. National Day")
                    
                    if st.form_submit_button("Add Holiday"):
                        conn = get_db()
                        c = conn.cursor()
                        try:
                            c.execute("INSERT INTO holidays (holiday_date, description) VALUES (?, ?)", 
                                      (h_date.strftime("%Y-%m-%d"), h_desc.strip()))
                            conn.commit()
                            st.success(f"Added holiday for {h_date}")
                            st.rerun()
                        except sqlite3.IntegrityError:
                            st.error("Holiday date already exists!")
                        finally:
                            conn.close()
                            
                st.markdown("##### Existing Holidays")
                conn = get_db()
                hol_df = pd.read_sql_query("SELECT holiday_date AS Date, description AS Reason FROM holidays ORDER BY holiday_date DESC", conn)
                conn.close()
                st.dataframe(hol_df, use_container_width=True)

        # ----------------------------------------------------------------------
        # TAB 3: MONTHLY PERFORMANCE
        # ----------------------------------------------------------------------
        with tab3:
            st.subheader("📈 Monthly Performance Analytics (Mon–Sat)")
            
            c1, c2 = st.columns(2)
            with c1:
                selected_year = st.selectbox("Year", [2025, 2026, 2027], index=1)
            with c2:
                selected_month = st.selectbox("Month", list(range(1, 13)), index=datetime.now().month - 1)
                
            total_working_days = count_working_days_in_month(selected_year, selected_month)
            expected_regular_hours = total_working_days * config.EXPECTED_DAILY_REGULAR_HOURS
            
            st.info(f"🗓 **Mon–Sat Working Days in Month:** {total_working_days} Days | **Target Regular Hours:** {expected_regular_hours} hrs")
            
            month_str = f"{selected_year}-{selected_month:02d}"
            
            conn = get_db()
            perf_df = pd.read_sql_query("""
                SELECT 
                    e.emp_id AS Employee_ID,
                    e.name AS Employee_Name,
                    COUNT(DISTINCT a.date) AS Days_Worked,
                    ROUND(SUM(a.total_hours), 2) AS Total_Hours_Logged,
                    ROUND(SUM(a.regular_hours), 2) AS Regular_Hours_Covered,
                    SUM(CASE WHEN a.covered_regular_shift = 'Yes' THEN 1 ELSE 0 END) AS Full_Shifts_Completed
                FROM employees e
                LEFT JOIN attendance a ON e.emp_id = a.emp_id AND a.date LIKE ?
                GROUP BY e.emp_id
            """, conn, params=[f"{month_str}%"])
            conn.close()
            
            if not perf_df.empty:
                perf_df['Days_Absent'] = total_working_days - perf_df['Days_Worked']
                perf_df['Days_Absent'] = perf_df['Days_Absent'].apply(lambda x: max(0, x))
                perf_df['Attendance_Rate_%'] = round((perf_df['Days_Worked'] / total_working_days) * 100, 1) if total_working_days > 0 else 0
                st.dataframe(perf_df, use_container_width=True)

        # ----------------------------------------------------------------------
        # TAB 4: PRINTABLE EMPLOYEE REPORT & PDF DOWNLOAD
        # ----------------------------------------------------------------------
        with tab4:
            st.subheader("🖨 Printable Monthly Employee Report & Payroll PDF")
            
            conn = get_db()
            emp_list = pd.read_sql_query("SELECT emp_id, name FROM employees", conn)
            conn.close()
            
            r_col1, r_col2, r_col3 = st.columns(3)
            with r_col1:
                rep_emp_id = st.selectbox("Select Employee", emp_list['emp_id'].tolist(), format_func=lambda x: f"{x} - {emp_list[emp_list['emp_id']==x]['name'].values[0]}")
            with r_col2:
                rep_year = st.selectbox("Report Year", [2025, 2026, 2027], index=1, key="rep_y")
            with r_col3:
                rep_month = st.selectbox("Report Month", list(range(1, 13)), index=datetime.now().month - 1, key="rep_m")
                
            month_iso = f"{rep_year}-{rep_month:02d}"
            
            conn = get_db()
            emp_info = pd.read_sql_query("SELECT * FROM employees WHERE emp_id = ?", conn, params=[rep_emp_id]).iloc[0]
            rep_attendance = pd.read_sql_query("""
                SELECT date, check_in, check_out, total_hours, regular_hours, covered_regular_shift 
                FROM attendance 
                WHERE emp_id = ? AND date LIKE ?
                ORDER BY date ASC
            """, conn, params=[rep_emp_id, f"{month_iso}%"])
            conn.close()
            
            work_days_count = count_working_days_in_month(rep_year, rep_month)
            days_attended = len(rep_attendance)
            tot_hrs_sum = rep_attendance['total_hours'].sum() if not rep_attendance.empty else 0.0
            reg_hrs_sum = rep_attendance['regular_hours'].sum() if not rep_attendance.empty else 0.0
            att_rate = round((days_attended / work_days_count) * 100, 1) if work_days_count > 0 else 0.0
            
            st.markdown(f"""
                <div class="employee-card">
                    <h2 style="color: #F05A28; margin-bottom: 0;">{config.COMPANY_NAME}</h2>
                    <p style="color: #EEF0F2; margin-top: 0;">{config.COMPANY_TAGLINE} | {config.COMPANY_ADDRESS}</p>
                    <hr style="border-color: #F05A28;">
                    <p><b>Employee ID:</b> {emp_info['emp_id']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Name:</b> {emp_info['name']} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Role:</b> {emp_info['role']}</p>
                    <p><b>Period:</b> {month_iso} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Total Working Days:</b> {work_days_count} &nbsp;&nbsp;|&nbsp;&nbsp; <b>Days Attended:</b> {days_attended}</p>
                    <p><b>Attendance KPI:</b> {att_rate}% &nbsp;&nbsp;|&nbsp;&nbsp; <b>Total Logged Hours:</b> {round(tot_hrs_sum, 2)} hrs &nbsp;&nbsp;|&nbsp;&nbsp; <b>Regular Hours:</b> {round(reg_hrs_sum, 2)} hrs</p>
                </div>
            """, unsafe_allow_html=True)
            
            st.write("### Detailed Attendance Logs")
            st.dataframe(rep_attendance, use_container_width=True)
            
            pdf_buffer = generate_payroll_pdf(
                emp_info, month_iso, work_days_count, days_attended, tot_hrs_sum, reg_hrs_sum, rep_attendance
            )
            
            btn_col1, btn_col2 = st.columns(2)
            with btn_col1:
                st.download_button(
                    label="📄 Download Official Payroll PDF",
                    data=pdf_buffer,
                    file_name=f"{config.COMPANY_NAME.split()[0]}_Payroll_{emp_info['name'].replace(' ', '_')}_{month_iso}.pdf",
                    mime="application/pdf",
                    type="primary"
                )
            with btn_col2:
                csv = rep_attendance.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Raw CSV",
                    data=csv,
                    file_name=f"BurkinAuto_Logs_{emp_info['name']}_{month_iso}.csv",
                    mime="text/csv"
                )

        # ----------------------------------------------------------------------
        # TAB 5: STAFF MANAGEMENT (ADD, EDIT, DELETE & DIRECTORY)
        # ----------------------------------------------------------------------
        with tab5:
            st.subheader(f"👥 {config.COMPANY_NAME.split()[0]} Auto Staff Directory & Management")
            
            conn = get_db()
            emp_df = pd.read_sql_query("SELECT emp_id AS 'Employee ID', name AS 'Full Name', role AS 'Role' FROM employees ORDER BY emp_id ASC", conn)
            conn.close()
            
            # Display Directory
            st.markdown("#### Current Staff Directory")
            st.dataframe(emp_df, use_container_width=True)
            st.write("---")
            
            # Action Columns: Add, Edit, Delete
            a_col, e_col, d_col = st.columns(3)
            
            # 1. ADD EMPLOYEE
            with a_col:
                st.markdown("#### ➕ Add New Staff Member")
                with st.form("add_staff_form", clear_on_submit=True):
                    s_id = st.text_input("Employee ID")
                    s_name = st.text_input("Full Name")
                    s_role = st.selectbox("Role", ["Senior Mechanic", "Junior Mechanic", "Auto Electrician", "Bodywork Specialist", "Garage Manager", "Apprentice"], key="add_role")
                    if st.form_submit_button("Add Employee"):
                        if s_id.strip() and s_name.strip():
                            conn = get_db()
                            c = conn.cursor()
                            try:
                                c.execute("INSERT INTO employees VALUES (?, ?, ?)", (s_id.strip(), s_name.strip(), s_role))
                                conn.commit()
                                st.success(f"Added {s_name.strip()} successfully!")
                                st.rerun()
                            except sqlite3.IntegrityError:
                                st.error("❌ Employee ID already exists! Please use a unique ID.")
                            finally:
                                conn.close()
                        else:
                            st.warning("Please fill in both Employee ID and Name.")

            # 2. EDIT EMPLOYEE
            with e_col:
                st.markdown("#### ✏️ Edit Staff Details")
                conn = get_db()
                emp_records = pd.read_sql_query("SELECT emp_id, name, role FROM employees", conn)
                conn.close()
                
                if not emp_records.empty:
                    edit_emp_id = st.selectbox(
                        "Select Staff Member to Edit",
                        emp_records['emp_id'].tolist(),
                        format_func=lambda x: f"{x} - {emp_records[emp_records['emp_id']==x]['name'].values[0]}"
                    )
                    
                    selected_emp = emp_records[emp_records['emp_id'] == edit_emp_id].iloc[0]
                    
                    role_options = ["Senior Mechanic", "Junior Mechanic", "Auto Electrician", "Bodywork Specialist", "Garage Manager", "Apprentice"]
                    default_role_idx = role_options.index(selected_emp['role']) if selected_emp['role'] in role_options else 0
                    
                    with st.form("edit_staff_form"):
                        new_name = st.text_input("Update Full Name", value=selected_emp['name'])
                        new_role = st.selectbox("Update Role", role_options, index=default_role_idx)
                        
                        if st.form_submit_button("Save Changes"):
                            if new_name.strip():
                                conn = get_db()
                                c = conn.cursor()
                                c.execute("UPDATE employees SET name = ?, role = ? WHERE emp_id = ?", (new_name.strip(), new_role, edit_emp_id))
                                conn.commit()
                                conn.close()
                                st.success("Employee details updated!")
                                st.rerun()
                            else:
                                st.warning("Name cannot be empty.")
                else:
                    st.info("No employee records found.")

            # 3. DELETE EMPLOYEE
            with d_col:
                st.markdown("#### 🗑 Delete Staff Member")
                conn = get_db()
                emp_records = pd.read_sql_query("SELECT emp_id, name FROM employees", conn)
                conn.close()
                
                if not emp_records.empty:
                    del_emp_id = st.selectbox(
                        "Select Staff Member to Delete",
                        emp_records['emp_id'].tolist(),
                        format_func=lambda x: f"{x} - {emp_records[emp_records['emp_id']==x]['name'].values[0]}",
                        key="del_select"
                    )
                    
                    with st.form("delete_staff_form"):
                        st.warning("⚠️ Action cannot be undone.")
                        if st.form_submit_button("Confirm Delete"):
                            conn = get_db()
                            c = conn.cursor()
                            
                            # Check if employee has attendance records to protect database integrity
                            c.execute("SELECT COUNT(*) FROM attendance WHERE emp_id = ?", (del_emp_id,))
                            att_count = c.fetchone()[0]
                            
                            if att_count > 0:
                                st.error(f"❌ Cannot delete: Employee has {att_count} logged attendance record(s). Delete or adjust logs first.")
                                conn.close()
                            else:
                                c.execute("DELETE FROM employees WHERE emp_id = ?", (del_emp_id,))
                                conn.commit()
                                conn.close()
                                st.success("Employee deleted successfully!")
                                st.rerun()
                else:
                    st.info("No employee records found.")
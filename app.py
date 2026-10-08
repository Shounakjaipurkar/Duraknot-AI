import threading

from flask import Flask, render_template, Response, request, redirect, session, url_for, send_file
import mysql.connector
from datetime import datetime
import cv2
from ultralytics import YOLO
import os
import time
import mysql.connector
import os


from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak
)
from reportlab.lib.units import inch
from io import BytesIO
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DETECTED_IMAGES_DIR = os.path.join(
    BASE_DIR,
    "detected_images"
)

os.makedirs(
    DETECTED_IMAGES_DIR,
    exist_ok=True
)


MODEL_PATH = r"D:\second final\runs\detect\train\weights\best.pt"

model = YOLO(MODEL_PATH)

app = Flask(__name__)
app.secret_key = "duraknot_secret_key_2026"

@app.route("/")
def home():

    return redirect(url_for("login"))



# =========================================================
# MYSQL CONNECTION
# =========================================================

def get_db_connection():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="Hishounak",
        database="duraknot_production"
    )


# =========================================================
# CAMERA SETUP
# =========================================================

camera = cv2.VideoCapture(0)
current_camera = 0
camera_lock = threading.Lock()

if not camera.isOpened():
    print("ERROR: Camera could not be opened")
else:
    print("SUCCESS: Camera opened")

def save_detection(
    defect_type,
    confidence,
    x1,
    y1,
    x2,
    y2,
    image_path
):
    db = None
    cursor = None

    try:
        # Create a fresh MySQL connection
        db = get_db_connection()

        if db is None or not db.is_connected():
            print("❌ MySQL connection failed")
            return

        cursor = db.cursor()

        sql = """
            INSERT INTO ai_detections
            (
                roll_id,
                defect_type,
                confidence,
                x1,
                y1,
                x2,
                y2,
                image_saved
            )
            SELECT
                roll_id,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s
            FROM production_rolls
            WHERE status = 'RUNNING'
            ORDER BY roll_id DESC
            LIMIT 1
        """

        values = (
            defect_type,
            confidence,
            x1,
            y1,
            x2,
            y2,
            image_path
        )

        cursor.execute(sql, values)
        db.commit()

        print("================================")
        print("✅ Detection saved to MySQL")
        print("Defect:", defect_type)
        print("Confidence:", confidence)
        print("Image:", image_path)
        print("================================")

    except mysql.connector.Error as error:
        print("❌ MySQL error:", error)

    finally:
        if cursor is not None:
            cursor.close()

        if db is not None and db.is_connected():
            db.close()

# =========================================================
# LIVE VIDEO ROUTE
# =========================================================

@app.route("/video_feed")
def video_feed():

    return Response(
        generate_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

@app.route("/switch_camera/<int:camera_index>")
def switch_camera(camera_index):
    global camera
    global current_camera

    with camera_lock:

        # Close current camera
        if camera is not None:
            camera.release()

        # Open selected camera
        new_camera = cv2.VideoCapture(camera_index)

        if not new_camera.isOpened():
            print(f"❌ Camera {camera_index} could not be opened")

            # Try to reopen current camera
            camera = cv2.VideoCapture(current_camera)

            return "Camera failed", 500

        camera = new_camera
        current_camera = camera_index

        print(f"✅ Switched to camera {camera_index}")

    return "OK"

# ==============================
# CAMERA + YOLO GENERATOR
# ==============================
import os
from datetime import datetime

# Folder to save detected images
SAVE_DIR = os.path.join(
    "static",
    "detected_images"
)

os.makedirs(SAVE_DIR, exist_ok=True)

last_saved_time = 0
SAVE_COOLDOWN = 5


def generate_frames():
    global last_saved_time

    while True:

        with camera_lock:
         success, frame = camera.read()

        if not success:
            break

        # Run YOLO
        results = model.predict(
            source=frame,
            conf=0.25,
            verbose=False
        )

        result = results[0]

        # -----------------------------------
        # FIND DETECTIONS WITH >= 70%
        # -----------------------------------

        high_conf_detections = []

        for box in result.boxes:

            confidence = float(box.conf[0])

            if confidence >= 0.70:

                # Bounding box
                x1, y1, x2, y2 = box.xyxy[0].tolist()

                x1 = int(x1)
                y1 = int(y1)
                x2 = int(x2)
                y2 = int(y2)

                # Class name
                class_id = int(box.cls[0])
                defect_type = model.names[class_id]

                high_conf_detections.append({
                    "defect_type": defect_type,
                    "confidence": confidence,
                    "x1": x1,
                    "y1": y1,
                    "x2": x2,
                    "y2": y2
                })

        # -----------------------------------
        # SAVE ONLY EVERY 5 SECONDS
        # -----------------------------------

        current_time = time.time()

        if (
            high_conf_detections
            and current_time - last_saved_time >= SAVE_COOLDOWN
        ):

            # Create filename
            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S_%f"
            )

            filename = f"improper_{timestamp}.jpg"

            full_image_path = os.path.join(
                SAVE_DIR,
                filename
            )

            # Draw bounding boxes
            annotated_frame = result.plot()

            # Save image
            # Save annotated image
            saved = cv2.imwrite(
                full_image_path,
                annotated_frame
            )

            if saved:
                # Path stored in MySQL
                database_image_path = f"detected_images/{filename}"

                print(f"📸 Image saved successfully: {full_image_path}")
                print(f"📂 Database path: {database_image_path}")

            else:
                print(f"❌ Failed to save image: {full_image_path}")
                database_image_path = None

            # -----------------------------------
            # SAVE EACH DETECTION TO MYSQL
            # -----------------------------------

            for detection in high_conf_detections:

                confidence_percent = (
                    detection["confidence"] * 100
                )

                # IMPORTANT:
                # Replace this with your actual
                # current production roll ID.
                roll_id = 1

                save_detection(
                    defect_type=detection["defect_type"],
                    confidence=confidence_percent,
                    x1=detection["x1"],
                    y1=detection["y1"],
                    x2=detection["x2"],
                    y2=detection["y2"],
                    image_path=database_image_path
                )


            print(
                    f"Defect: {detection['defect_type']}"
                )

            print(
                    f"Confidence: "
                    f"{confidence_percent:.2f}%"
                )

            # Reset cooldown
            last_saved_time = current_time

        # -----------------------------------
        # DISPLAY LIVE FRAME
        # -----------------------------------

        annotated_frame = result.plot()

        success, buffer = cv2.imencode(
            ".jpg",
            annotated_frame
        )

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )
# =========================================================
# ESP32 → FLASK → MYSQL
# =========================================================

@app.route("/update_production", methods=["POST"])
def update_production():

    # =====================================================
    # 1. RECEIVE DATA FROM ESP32    
    # =====================================================

    data = request.get_json(silent=True)

    print("\n================================")
    print("ESP32 DATA RECEIVED")
    print("================================")
    print(data)

    if not data:
        print("ERROR: No JSON data received")

        return {
            "success": False,
            "message": "No data received",
            "reset": False
        }, 400

    # Get ESP32 values
    pulse_count = data.get("pulse_count")
    length_cm = data.get("length_cm")
    length_cm = data.get("length_cm")
    # Hall Effect values
    hall_pulse_count = data.get("hall_pulse_count")
    hall_length_cm = data.get("hall_length_cm")

    

    print("Pulse Count :", pulse_count)
    print("Length CM   :", length_cm)
    print("Length CM    :", length_cm)
    print("Hall Pulses  :", hall_pulse_count)
    print("Hall Length  :", hall_length_cm, "cm")
   

   


    # Validate length
    if length_cm is None:

        return {
            "success": False,
            "message": "length_cm is missing",
            "reset": False
        }, 400

    try:
        length_cm = float(length_cm)
    except (TypeError, ValueError):

        return {
            "success": False,
            "message": "Invalid length value",
            "reset": False
        }, 400


    # =====================================================
    # 2. CONNECT TO MYSQL
    # =====================================================

    db = None
    cursor = None

    try:

        db = get_db_connection()

        cursor = db.cursor(dictionary=True)


        # =================================================
        # 3. GET CURRENT RUNNING ROLL
        # =================================================

        cursor.execute("""
            SELECT
                roll_id,
                roll_number,
                required_length,
                current_length,
                status
            FROM production_rolls
            WHERE status = 'RUNNING'
            ORDER BY roll_id DESC
            LIMIT 1
        """)

        production = cursor.fetchone()


        # =================================================
        # 4. NO RUNNING ROLL
        # =================================================

        if not production:

            print("ERROR: No RUNNING roll found")

            return {
                "success": False,
                "message": "No running roll found",
                "reset": False
            }, 400


        # =================================================
        # 5. GET ROLL INFORMATION
        # =================================================

        roll_id = production["roll_id"]
        roll_number = production["roll_number"]

        required_length = float(
            production["required_length"]
        )

        print("\n--------------------------------")
        print("CURRENT ROLL")
        print("--------------------------------")
        print("Roll ID        :", roll_id)
        print("Roll Number    :", roll_number)
        print("Required Length:", required_length, "cm")
        print("ESP32 Length   :", length_cm, "cm")


        # =================================================
        # 6. UPDATE CURRENT LENGTH
        # =================================================

        cursor.execute("""
            UPDATE production_rolls
            SET current_length = %s
            WHERE roll_id = %s
              AND status = 'RUNNING'
        """, (
            length_cm,
            roll_id
        ))

        print(
            "Rows updated:",
            cursor.rowcount
        )


        # =================================================
        # 7. CHECK WHETHER ROLL IS COMPLETED
        # =================================================

        reset = False

        if length_cm >= required_length:

            print("\n================================")
            print("ROLL COMPLETED")
            print("================================")
            print("Roll Number    :", roll_number)
            print("Required Length:", required_length, "cm")
            print("Produced Length:", length_cm, "cm")


            # =============================================
            # 8. COMPLETE CURRENT ROLL
            # =============================================

            cursor.execute("""
                UPDATE production_rolls
                SET
                    current_length = %s,
                    status = 'COMPLETED',
                    end_time = NOW()
                WHERE roll_id = %s
            """, (
                length_cm,
                roll_id
            ))


            # =============================================
            # 9. CREATE NEXT ROLL
            # =============================================

            next_roll_id = roll_id + 1

            next_roll_number = f"DRK-{next_roll_id:04d}"

            cursor.execute("""
                INSERT INTO production_rolls
                (
                    roll_number,
                    required_length,
                    current_length,
                    status,
                    start_time
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    'RUNNING',
                    NOW()
                )
            """, (
                next_roll_number,
                required_length,
                0
            ))

            print("--------------------------------")
            print("NEW ROLL CREATED")
            print("--------------------------------")
            print("New Roll ID    :", next_roll_id)
            print("New Roll Number:", next_roll_number)
            print("Required Length:", required_length, "cm")
            print("Current Length :", 0, "cm")


            # Tell ESP32 to reset
            reset = True


        # =================================================
        # 10. SAVE CHANGES
        # =================================================

        db.commit()

        print("\n================================")
        print("MYSQL UPDATED SUCCESSFULLY")
        print("================================")
        print("Reset ESP32:", reset)


        # =================================================
        # 11. RESPONSE TO ESP32
        # =================================================

    
        return {
    "success": True,
    "reset": reset,
    "required_length_cm": required_length,
    
}, 200

    except mysql.connector.Error as error:

        if db:
            db.rollback()

        print("\nMYSQL ERROR:")
        print(error)

        return {
            "success": False,
            "message": str(error),
            "reset": False
        }, 500


    except Exception as error:

        if db:
            db.rollback()

        print("\nSERVER ERROR:")
        print(error)

        return {
            "success": False,
            "message": str(error),
            "reset": False
        }, 500


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()

        print("================================\n")
# =========================================================
# SET REQUIRED ROLL LENGTH
# =========================================================

@app.route("/set_required_length", methods=["POST"])
def set_required_length():

    required_length = request.form.get("required_length")

    try:

        required_length = float(required_length)

        if required_length <= 0:

            return "Required length must be greater than 0"

        # Connect to MySQL
        db = get_db_connection()

        cursor = db.cursor()

        # Update currently running roll
        cursor.execute("""
            UPDATE production_rolls
            SET required_length = %s
            WHERE status = 'RUNNING'
            ORDER BY roll_id DESC
            LIMIT 1
        """, (
            required_length,
        ))

        db.commit()

        cursor.close()
        db.close()

        print("--------------------------------")
        print("REQUIRED LENGTH UPDATED")
        print("New Required Length:", required_length, "m")
        print("--------------------------------")

        return redirect("/")

    except ValueError:

        return "Invalid required length"

# =========================================================
# LOGIN
# =========================================================

@app.route("/login", methods=["GET", "POST"])
def login():

    # -----------------------------------------------------
    # IF ALREADY LOGGED IN
    # -----------------------------------------------------

    if "user_id" in session:
        return redirect(url_for("dashboard"))


    # -----------------------------------------------------
    # SHOW LOGIN PAGE
    # -----------------------------------------------------

    if request.method == "GET":

        return render_template("login.html")


    # -----------------------------------------------------
    # GET LOGIN DATA
    # -----------------------------------------------------

    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")


    if not username or not password:

        return render_template(
            "login.html",
            error="Please enter User ID and Password"
        )


    db = None
    cursor = None


    try:

        # -------------------------------------------------
        # CONNECT TO MYSQL
        # -------------------------------------------------

        db = get_db_connection()

        cursor = db.cursor(dictionary=True)


        # -------------------------------------------------
        # FIND USER
        # -------------------------------------------------

        cursor.execute("""
            SELECT
                user_id,
                username,
                password,
                name
            FROM users
            WHERE username = %s
            LIMIT 1
        """, (username,))


        user = cursor.fetchone()


        # -------------------------------------------------
        # CHECK USER
        # -------------------------------------------------

        if not user:

            print("--------------------------------")
            print("LOGIN FAILED")
            print("Unknown User:", username)
            print("--------------------------------")

            return render_template(
                "login.html",
                error="Invalid User ID or Password"
            )


        # -------------------------------------------------
        # CHECK PASSWORD
        # -------------------------------------------------

        if user["password"] != password:

            print("--------------------------------")
            print("LOGIN FAILED")
            print("User:", username)
            print("--------------------------------")

            return render_template(
                "login.html",
                error="Invalid User ID or Password"
            )


        # -------------------------------------------------
        # LOGIN SUCCESSFUL
        # -------------------------------------------------

        session["user_id"] = user["user_id"]
        session["username"] = user["username"]
        session["name"] = user["name"]


        # -------------------------------------------------
        # SAVE LOGIN HISTORY
        # -------------------------------------------------

        cursor.execute("""
            INSERT INTO login_history
            (
                user_id,
                username,
                login_time
            )
            VALUES
            (
                %s,
                %s,
                NOW()
            )
        """, (
            user["user_id"],
            user["username"]
        ))


        # Get newly created login_history ID
        login_id = cursor.lastrowid


        # Store it in Flask session
        session["login_id"] = login_id


        # Save database changes
        db.commit()


        print("--------------------------------")
        print("USER LOGIN SUCCESSFUL")
        print("User ID:", user["username"])
        print("Name:", user["name"])
        print("Login History ID:", login_id)
        print("--------------------------------")


        # -------------------------------------------------
        # GO TO DASHBOARD
        # -------------------------------------------------

        return redirect(url_for("dashboard"))


    except mysql.connector.Error as error:

        print("--------------------------------")
        print("LOGIN MYSQL ERROR")
        print(error)
        print("--------------------------------")


        if db:
            db.rollback()


        return render_template(
            "login.html",
            error="Database error. Please try again."
        )


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()
# =========================================================
# LOGOUT
# =========================================================

@app.route("/logout")
def logout():

    login_id = session.get("login_id")
    username = session.get("username")


    db = None
    cursor = None


    try:

        # -------------------------------------------------
        # UPDATE LOGOUT TIME
        # -------------------------------------------------

        if login_id:

            db = get_db_connection()

            cursor = db.cursor()


            cursor.execute("""
                UPDATE login_history
                SET logout_time = NOW()
                WHERE login_id = %s
            """, (
                login_id,
            ))


            db.commit()


            print("--------------------------------")
            print("USER LOGGED OUT")
            print("User:", username)
            print("Login History ID:", login_id)
            print("--------------------------------")


    except mysql.connector.Error as error:

        print("--------------------------------")
        print("LOGOUT MYSQL ERROR")
        print(error)
        print("--------------------------------")


        if db:
            db.rollback()


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()


    # -----------------------------------------------------
    # CLEAR FLASK SESSION
    # -----------------------------------------------------

    session.clear()


    # -----------------------------------------------------
    # RETURN TO LOGIN
    # -----------------------------------------------------

    return redirect(url_for("login"))
# =========================================================
# MAIN DASHBOARD
# =========================================================

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect(url_for("login"))

   

    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    # -----------------------------------------------------
    # PRODUCTION DATA
    # -----------------------------------------------------

    cursor.execute("""
        SELECT *
        FROM production_rolls
        ORDER BY roll_id DESC
        LIMIT 1
    """)

    production = cursor.fetchone()


    # -----------------------------------------------------
    # LATEST AI DETECTION
    # -----------------------------------------------------

    cursor.execute("""
        SELECT *
        FROM ai_detections
        ORDER BY detection_id DESC
        LIMIT 1
    """)

    latest_detection = cursor.fetchone()


    # -----------------------------------------------------
    # DEFECT HISTORY
    # -----------------------------------------------------

    cursor.execute("""
        SELECT *
        FROM ai_detections
        ORDER BY detection_id DESC
        LIMIT 10
    """)

    defect_history = cursor.fetchall()


    # -----------------------------------------------------
    # ALERTS
    # -----------------------------------------------------

    cursor.execute("""
        SELECT *
        FROM alerts
        ORDER BY alert_id DESC
        LIMIT 10
    """)

    alerts = cursor.fetchall()


    cursor.close()
    db.close()


    return render_template(
        "dashboard.html",

        production=production,

        latest_detection=latest_detection,

        defect_history=defect_history,

        alerts=alerts,

        user_name=session.get("name"),

        username=session.get("username")
    )

    # Connect to MySQL
    db = get_db_connection()

    cursor = db.cursor(dictionary=True)

    # =====================================================
    # PRODUCTION DATA
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM production_rolls
        ORDER BY roll_id DESC
        LIMIT 1
    """)

    production = cursor.fetchone()

    # =====================================================
    # LATEST AI DETECTION
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM ai_detections
        ORDER BY detection_id DESC
        LIMIT 1
    """)

    latest_detection = cursor.fetchone()

    # =====================================================
    # DEFECT HISTORY
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM ai_detections
        ORDER BY detection_id DESC
        LIMIT 10
    """)

    defect_history = cursor.fetchall()

    # =====================================================
    # ALERTS
    # =====================================================

    cursor.execute("""
        SELECT *
        FROM alerts
        ORDER BY alert_id DESC
        LIMIT 10
    """)

    alerts = cursor.fetchall()

    # Close database
    cursor.close()
    db.close()

    # =====================================================
    # SEND DATA TO DASHBOARD
    # =====================================================

    return render_template(
        "dashboard.html",
        production=production,
        latest_detection=latest_detection,
        defect_history=defect_history,
        alerts=alerts
    )


# =========================================================
# START FLASK
# =========================================================
@app.route("/production_data")
def production_data():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            roll_id,
            roll_number,
            required_length,
            current_length,
            status
        FROM production_rolls
        ORDER BY roll_id DESC
        LIMIT 1
    """)

    production = cursor.fetchone()

    cursor.close()
    db.close()

    if not production:
        return {
            "success": False,
            "message": "No production data"
        }

    return {
    "success": True,
    "roll_id": production["roll_id"],
    "roll_number": production["roll_number"],
    "required_length": float(production["required_length"]),
    "current_length": float(production["current_length"]),
    "status": production["status"],
}

# =========================================================
# ROLL HISTORY
# =========================================================

@app.route("/history")
def history():

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # Get all completed rolls
    cursor.execute("""
        SELECT
            roll_id,
            roll_number,
            required_length,
            current_length,
            status,
            start_time,
            end_time
        FROM production_rolls
        WHERE status = 'COMPLETED'
        ORDER BY roll_id DESC
    """)

    rolls = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        "history.html",
        rolls=rolls
    )


# =========================================================
# SPECIFIC ROLL DETAILS
# =========================================================

@app.route("/roll/<int:roll_id>")
def roll_details(roll_id):

    db = get_db_connection()
    cursor = db.cursor(dictionary=True)

    # =====================================================
    # GET SELECTED ROLL
    # =====================================================

    cursor.execute("""
        SELECT
            roll_id,
            roll_number,
            required_length,
            current_length,
            status,
            start_time,
            end_time
        FROM production_rolls
        WHERE roll_id = %s
    """, (roll_id,))

    roll = cursor.fetchone()

    if not roll:

        cursor.close()
        db.close()

        return "Roll not found", 404


    # =====================================================
    # GET DEFECTS FOR THIS ROLL
    # =====================================================

    cursor.execute("""
        SELECT
            detection_id,
            roll_id,
            timestamp,
            defect_type,
            confidence,
            image_saved
        FROM ai_detections
        WHERE roll_id = %s
        ORDER BY detection_id ASC
    """, (roll_id,))

    raw_defects = cursor.fetchall()


    # =====================================================
    # GROUP DEFECTS
    #
    # Same image + same defect type
    # will be counted together.
    # =====================================================

    grouped_defects = {}

    for defect in raw_defects:

        image_name = defect["image_saved"]
        defect_type = defect["defect_type"]

        key = (
            image_name,
            defect_type
        )

        if key not in grouped_defects:

            grouped_defects[key] = {
                "image_name": image_name,
                "defect_type": defect_type,
                "count": 0
            }

        grouped_defects[key]["count"] += 1


    # Convert dictionary to list
    defects = list(grouped_defects.values())


    # =====================================================
    # TOTAL DEFECTS
    # =====================================================

    total_defects = 0

    for defect in defects:

        total_defects += defect["count"]


    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    cursor.close()
    db.close()


    # =====================================================
    # SEND DATA TO HTML
    # =====================================================

    return render_template(
        "roll_details.html",
        roll=roll,
        defects=defects,
        total_defects=total_defects
    )
## =========================================================
# ANALYTICS
# =========================================================

@app.route("/analytics")
def analytics():

    # -----------------------------------------------------
    # LOGIN CHECK
    # -----------------------------------------------------

    if "user_id" not in session:
        return redirect(url_for("login"))


    db = None
    cursor = None

    try:

        db = get_db_connection()
        cursor = db.cursor(dictionary=True)


        # =================================================
        # 1. PRODUCTION SUMMARY
        # =================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_rolls,

                COALESCE(
                    SUM(current_length),
                    0
                ) AS total_length,

                COALESCE(
                    AVG(current_length),
                    0
                ) AS average_length

            FROM production_rolls

            WHERE status = 'COMPLETED'
        """)

        production_summary = cursor.fetchone()


        # =================================================
        # 2. TOTAL DEFECTS
        # =================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_defects

            FROM ai_detections
        """)

        defect_summary = cursor.fetchone()


        total_defects = (
            defect_summary["total_defects"]
            if defect_summary
            else 0
        )


        # =================================================
        # 3. DEFECTS BY TYPE
        # =================================================

        cursor.execute("""
            SELECT

                defect_type,

                COUNT(*) AS defect_count

            FROM ai_detections

            GROUP BY defect_type

            ORDER BY defect_count DESC
        """)

        defects_by_type = cursor.fetchall()


        # =================================================
        # 4. DEFECTS BY ROLL
        # =================================================

        cursor.execute("""
            SELECT

                p.roll_number,

                COUNT(a.detection_id)
                    AS defect_count

            FROM production_rolls p

            LEFT JOIN ai_detections a
                ON p.roll_id = a.roll_id

            GROUP BY
                p.roll_id,
                p.roll_number

            ORDER BY
                p.roll_id ASC
        """)

        defects_by_roll = cursor.fetchall()


        # =================================================
        # 5. PRODUCTION BY ROLL
        # =================================================

        cursor.execute("""
            SELECT

                roll_number,

                current_length,

                required_length

            FROM production_rolls

            WHERE status = 'COMPLETED'

            ORDER BY roll_id ASC
        """)

        production_by_roll = cursor.fetchall()


        # =================================================
        # 6. TOTAL ROLLS PRODUCED
        # =================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_rolls_produced

            FROM production_rolls

            WHERE status = 'COMPLETED'
        """)

        roll_result = cursor.fetchone()


        total_rolls_produced = (
            roll_result["total_rolls_produced"]
            if roll_result
            else 0
        )


        # =================================================
        # CLOSE DATABASE
        # =================================================

        cursor.close()
        db.close()


        # =================================================
        # SEND DATA TO ANALYTICS PAGE
        # =================================================

        return render_template(

            "analytics.html",

            production_summary=production_summary,

            total_defects=total_defects,

            defects_by_type=defects_by_type,

            defects_by_roll=defects_by_roll,

            production_by_roll=production_by_roll,

            total_rolls_produced=total_rolls_produced

        )


    except mysql.connector.Error as error:

        print("--------------------------------")
        print("ANALYTICS MYSQL ERROR")
        print(error)
        print("--------------------------------")


        if cursor:
            cursor.close()

        if db:
            db.close()


        return "Analytics database error", 500
    # =====================================================
    # CLOSE DATABASE
    # =====================================================

    cursor.close()
    db.close()


    # =====================================================
    # SEND DATA TO ANALYTICS PAGE
    # =====================================================

    return render_template(
        "analytics.html",

        production_summary=production_summary,

        total_defects=defect_summary["total_defects"],

        defects_by_type=defects_by_type,

        defects_by_roll=defects_by_roll,

        production_by_roll=production_by_roll
    )

# =========================================================
# DOWNLOAD ANALYTICS PDF REPORT
# =========================================================

@app.route("/download_report")
def download_report():

    db = None
    cursor = None

    try:

        # =================================================
        # CONNECT TO MYSQL
        # =================================================

        db = get_db_connection()

        cursor = db.cursor(dictionary=True)


        # =================================================
        # PRODUCTION SUMMARY
        # =================================================

        cursor.execute("""
            SELECT
                COUNT(*) AS total_rolls,
                COALESCE(SUM(current_length), 0) AS total_length,
                COALESCE(AVG(current_length), 0) AS average_length
            FROM production_rolls
            WHERE status = 'COMPLETED'
        """)

        production_summary = cursor.fetchone()


        # =================================================
        # TOTAL DEFECTS
        # =================================================

        cursor.execute("""
            SELECT COUNT(*) AS total_defects
            FROM ai_detections
        """)

        defect_result = cursor.fetchone()

        total_defects = defect_result["total_defects"] or 0


        # =================================================
        # DEFECTS BY TYPE
        # =================================================

        cursor.execute("""
            SELECT
                defect_type,
                COUNT(*) AS defect_count
            FROM ai_detections
            GROUP BY defect_type
            ORDER BY defect_count DESC
        """)

        defects_by_type = cursor.fetchall()


        # =================================================
        # PRODUCTION BY ROLL
        # =================================================

        cursor.execute("""
            SELECT
                roll_id,
                roll_number,
                required_length,
                current_length,
                status,
                start_time,
                end_time
            FROM production_rolls
            WHERE status = 'COMPLETED'
            ORDER BY roll_id ASC
        """)

        production_by_roll = cursor.fetchall()


        # =================================================
        # DEFECTS BY ROLL
        # =================================================

        cursor.execute("""
            SELECT
                p.roll_number,
                COUNT(a.detection_id) AS defect_count
            FROM production_rolls p
            LEFT JOIN ai_detections a
                ON p.roll_id = a.roll_id
            GROUP BY p.roll_id, p.roll_number
            ORDER BY p.roll_id ASC
        """)

        defects_by_roll = cursor.fetchall()


        # =================================================
        # CLOSE MYSQL
        # =================================================

        cursor.close()
        db.close()

        cursor = None
        db = None


        # =================================================
        # CREATE PDF IN MEMORY
        # =================================================

        pdf_buffer = BytesIO()


        document = SimpleDocTemplate(

            pdf_buffer,

            pagesize=A4,

            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40

        )


        # =================================================
        # STYLES
        # =================================================

        styles = getSampleStyleSheet()


        title_style = ParagraphStyle(

            "ReportTitle",

            parent=styles["Title"],

            alignment=TA_CENTER,

            fontSize=22,

            spaceAfter=10

        )


        subtitle_style = ParagraphStyle(

            "ReportSubtitle",

            parent=styles["Normal"],

            alignment=TA_CENTER,

            fontSize=11,

            spaceAfter=20

        )


        heading_style = ParagraphStyle(

            "SectionHeading",

            parent=styles["Heading2"],

            fontSize=15,

            spaceBefore=15,

            spaceAfter=10

        )


        normal_style = ParagraphStyle(

            "NormalReport",

            parent=styles["Normal"],

            fontSize=10,

            spaceAfter=5

        )


        # =================================================
        # PDF CONTENT
        # =================================================

        story = []


        # =================================================
        # TITLE
        # =================================================

        story.append(
            Paragraph(
                "DuraKnot Production & AI Analysis Report",
                title_style
            )
        )


        story.append(
            Paragraph(
                "A-1 Fence Quality & Production Monitoring System",
                subtitle_style
            )
        )


        story.append(
            Paragraph(
                "Report Generated: "
                + datetime.now().strftime(
                    "%d-%m-%Y %H:%M:%S"
                ),
                normal_style
            )
        )


        story.append(Spacer(1, 15))


        # =================================================
        # PRODUCTION SUMMARY
        # =================================================

        story.append(
            Paragraph(
                "Production Summary",
                heading_style
            )
        )


        summary_data = [

            ["Parameter", "Value"],

            [
                "Total Rolls Completed",
                str(
                    production_summary["total_rolls"] or 0
                )
            ],

            [
                "Total Length Produced",
                f'{float(production_summary["total_length"] or 0):.2f} m'
            ],

            [
                "Average Roll Length",
                f'{float(production_summary["average_length"] or 0):.2f} m'
            ],

            [
                "Total Defects",
                str(total_defects)
            ]

        ]


        summary_table = Table(

            summary_data,

            colWidths=[
                250,
                200
            ]

        )


        summary_table.setStyle(

            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "TEXTCOLOR",
                    (0, 0),
                    (-1, 0),
                    colors.black
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "CENTER"
                ),

                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE"
                )

            ])

        )


        story.append(summary_table)


        # =================================================
        # PRODUCTION BY ROLL
        # =================================================

        story.append(
            Paragraph(
                "Production by Roll",
                heading_style
            )
        )


        production_data = [

            [
                "Roll Number",
                "Required",
                "Produced",
                "Status"
            ]

        ]


        for roll in production_by_roll:

            production_data.append(

                [

                    roll["roll_number"],

                    f'{float(roll["required_length"] or 0):.2f} m',

                    f'{float(roll["current_length"] or 0):.2f} m',

                    roll["status"]

                ]

            )


        if len(production_data) == 1:

            production_data.append(
                [
                    "No completed rolls",
                    "-",
                    "-",
                    "-"
                ]
            )


        production_table = Table(

            production_data,

            colWidths=[
                130,
                100,
                100,
                100
            ]

        )


        production_table.setStyle(

            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (-1, -1),
                    "CENTER"
                )

            ])

        )


        story.append(production_table)


        # =================================================
        # DEFECT ANALYSIS
        # =================================================

        story.append(
            Paragraph(
                "Defect Analysis",
                heading_style
            )
        )


        defect_data = [

            [
                "Defect Type",
                "Number of Defects"
            ]

        ]


        for defect in defects_by_type:

            defect_data.append(

                [

                    defect["defect_type"],

                    str(defect["defect_count"])

                ]

            )


        if len(defect_data) == 1:

            defect_data.append(

                [
                    "No defects recorded",
                    "0"
                ]

            )


        defect_table = Table(

            defect_data,

            colWidths=[
                300,
                180
            ]

        )


        defect_table.setStyle(

            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "CENTER"
                )

            ])

        )


        story.append(defect_table)


        # =================================================
        # DEFECTS BY ROLL
        # =================================================

        story.append(
            Paragraph(
                "Defects by Roll",
                heading_style
            )
        )


        defect_roll_data = [

            [
                "Roll Number",
                "Total Defects"
            ]

        ]


        for roll in defects_by_roll:

            count = roll["defect_count"] or 0

            defect_roll_data.append(

                [

                    roll["roll_number"],

                    str(count)

                ]

            )


        if len(defect_roll_data) == 1:

            defect_roll_data.append(

                [
                    "No roll data",
                    "0"
                ]

            )


        defect_roll_table = Table(

            defect_roll_data,

            colWidths=[
                300,
                180
            ]

        )


        defect_roll_table.setStyle(

            TableStyle([

                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey
                ),

                (
                    "FONTNAME",
                    (0, 0),
                    (-1, 0),
                    "Helvetica-Bold"
                ),

                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    0.5,
                    colors.grey
                ),

                (
                    "ALIGN",
                    (1, 1),
                    (1, -1),
                    "CENTER"
                )

            ])

        )


        story.append(defect_roll_table)


        # =================================================
        # BUILD PDF
        # =================================================

        document.build(story)


        # Move buffer back to beginning

        pdf_buffer.seek(0)


        # =================================================
        # SEND PDF TO USER
        # =================================================

        filename = (
            "DuraKnot_Analytics_Report_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".pdf"
        )


        return send_file(

            pdf_buffer,

            as_attachment=True,

            download_name=filename,

            mimetype="application/pdf"

        )


    except Exception as error:

        print("\n================================")
        print("PDF REPORT ERROR")
        print("================================")
        print(error)
        print("================================")


        if cursor:

            cursor.close()


        if db:

            db.close()


        return (
            "Error generating PDF report: "
            + str(error)
        ), 500

if __name__ == "__main__":

    print("------------------------------------")
    print("DuraKnot Dashboard Starting...")
    print("------------------------------------")

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
    )
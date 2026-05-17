from flask import Flask, render_template, request, redirect, url_for, flash
import mysql.connector

app = Flask(__name__)
app.secret_key = "medibook_secret"


def get_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="doctor_app"
    )


def init_db():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="root"
    )
    cur = conn.cursor()
    cur.execute("CREATE DATABASE IF NOT EXISTS doctor_app")
    cur.execute("USE doctor_app")
    cur.execute("""
        CREATE TABLE IF NOT EXISTS doctors (
            id             INT AUTO_INCREMENT PRIMARY KEY,
            name           VARCHAR(100) NOT NULL,
            specialization VARCHAR(100) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id               INT AUTO_INCREMENT PRIMARY KEY,
            patient_name     VARCHAR(100) NOT NULL,
            doctor_id        INT NOT NULL,
            appointment_date DATE NOT NULL,
            FOREIGN KEY (doctor_id) REFERENCES doctors(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    cur.close()
    conn.close()


@app.route("/")
def home():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM doctors")
    total_doctors = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM appointments")
    total_appointments = cur.fetchone()[0]
    cur.close()
    conn.close()
    return render_template("home.html",
                           total_doctors=total_doctors,
                           total_appointments=total_appointments)


@app.route("/add_doctor", methods=["GET", "POST"])
def add_doctor():
    if request.method == "POST":
        name           = request.form["name"].strip()
        specialization = request.form["specialization"].strip()
        if not name or not specialization:
            flash("Both fields are required.", "error")
            return redirect(url_for("add_doctor"))
        conn = get_db()
        cur  = conn.cursor()
        cur.execute("INSERT INTO doctors (name, specialization) VALUES (%s, %s)", (name, specialization))
        conn.commit()
        cur.close()
        conn.close()
        flash(f"Dr. {name} added successfully!", "success")
        return redirect(url_for("home"))
    return render_template("add_doctor.html")


@app.route("/book", methods=["GET", "POST"])
def book():
    conn = get_db()
    cur  = conn.cursor()
    if request.method == "POST":
        patient_name     = request.form["patient_name"].strip()
        doctor_id        = request.form["doctor_id"]
        appointment_date = request.form["appointment_date"]
        if not patient_name or not doctor_id or not appointment_date:
            flash("All fields are required.", "error")
            cur.execute("SELECT id, name, specialization FROM doctors ORDER BY name")
            doctors = cur.fetchall()
            return render_template("book.html", doctors=doctors)
        cur.execute(
            "INSERT INTO appointments (patient_name, doctor_id, appointment_date) VALUES (%s, %s, %s)",
            (patient_name, doctor_id, appointment_date)
        )
        conn.commit()
        cur.close()
        conn.close()
        flash("Appointment booked successfully!", "success")
        return redirect(url_for("view"))
    cur.execute("SELECT id, name, specialization FROM doctors ORDER BY name")
    doctors = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("book.html", doctors=doctors)


@app.route("/view")
def view():
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("""
        SELECT a.id, a.patient_name, d.name, d.specialization, a.appointment_date
        FROM   appointments a
        JOIN   doctors d ON a.doctor_id = d.id
        ORDER  BY a.appointment_date ASC
    """)
    appointments = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("view.html", appointments=appointments)


@app.route("/edit/<int:appointment_id>", methods=["GET", "POST"])
def edit(appointment_id):
    conn = get_db()
    cur  = conn.cursor()
    if request.method == "POST":
        patient_name     = request.form["patient_name"].strip()
        doctor_id        = request.form["doctor_id"]
        appointment_date = request.form["appointment_date"]
        cur.execute("""
            UPDATE appointments
            SET    patient_name=%s, doctor_id=%s, appointment_date=%s
            WHERE  id=%s
        """, (patient_name, doctor_id, appointment_date, appointment_id))
        conn.commit()
        cur.close()
        conn.close()
        flash("Appointment updated successfully!", "success")
        return redirect(url_for("view"))
    cur.execute("SELECT * FROM appointments WHERE id=%s", (appointment_id,))
    appointment = cur.fetchone()
    cur.execute("SELECT id, name, specialization FROM doctors ORDER BY name")
    doctors = cur.fetchall()
    cur.close()
    conn.close()
    if not appointment:
        flash("Appointment not found.", "error")
        return redirect(url_for("view"))
    return render_template("edit.html", appointment=appointment, doctors=doctors)


@app.route("/delete/<int:appointment_id>")
def delete(appointment_id):
    conn = get_db()
    cur  = conn.cursor()
    cur.execute("DELETE FROM appointments WHERE id=%s", (appointment_id,))
    conn.commit()
    cur.close()
    conn.close()
    flash("Appointment deleted.", "success")
    return redirect(url_for("view"))


if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=5000)

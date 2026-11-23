import os
import re

import pymysql
from flask import Flask, g, jsonify, request
from pymysql.cursors import DictCursor

app = Flask(__name__)


def database():
    if "db" not in g:
        g.db = pymysql.connect(
            host=os.environ["DB_HOST"],
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            database=os.environ["DB_NAME"],
            cursorclass=DictCursor,
            charset="utf8mb4",
            autocommit=True,
            connect_timeout=3,
        )
    return g.db


@app.teardown_appcontext
def close_database(error):
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


@app.errorhandler(pymysql.MySQLError)
def database_error(error):
    app.logger.exception("Database operation failed")
    return jsonify(error="Database unavailable. Check backend logs."), 503

@app.get("/version")
def version():
    return jsonify(version="v2")


@app.get("/readyz")
def ready():
    with database().cursor() as cursor:
        cursor.execute("SELECT id FROM students LIMIT 1")
    return jsonify(status="ready")


@app.get("/api/students")
def list_students():
    with database().cursor() as cursor:
        cursor.execute("SELECT id, name, email FROM students ORDER BY id")
        return jsonify(cursor.fetchall())


@app.post("/api/students")
def add_student():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify(error="Send a JSON object with name and email."), 400
    name, email = data.get("name"), data.get("email")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 100:
        return jsonify(error="Enter a name between 1 and 100 characters."), 400
    if not isinstance(email, str):
        return jsonify(error="Enter a valid email address."), 400
    name, email = name.strip(), email.strip()
    if len(email) > 254 or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
        return jsonify(error="Enter a valid email address."), 400
    with database().cursor() as cursor:
        try:
            cursor.execute("INSERT INTO students (name, email) VALUES (%s, %s)", (name, email))
        except pymysql.IntegrityError as error:
            if error.args[0] == 1062:
                return jsonify(error="That email already belongs to a student."), 409
            raise
        return jsonify(id=cursor.lastrowid, name=name, email=email), 201


@app.get("/api/students/<int:student_id>")
def get_student(student_id):
    with database().cursor() as cursor:
        cursor.execute("SELECT id, name, email FROM students WHERE id = %s", (student_id,))
        student = cursor.fetchone()
    if student is None:
        return jsonify(error="Student not found."), 404
    return jsonify(student)


@app.delete("/api/students/<int:student_id>")
def delete_student(student_id):
    with database().cursor() as cursor:
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        if cursor.rowcount == 0:
            return jsonify(error="Student not found."), 404
    return "", 204

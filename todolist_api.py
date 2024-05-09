from flask import Flask, render_template, redirect, g, request, url_for, jsonify, Response, session
import mysql.connector
import urllib
import json
import hashlib
import os
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

DATABASE = 'todolist'

app = Flask(__name__)
app.config.from_object(__name__)
app.secret_key = b'\x9f\xff\xd4\xe7\xc9\x91\xe9o/L\x93\xdb\x16\xe9\xc2r\xdf\x99\x84\xae\xef?\xc7/'

def hash_password(password):
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

@app.route("/api/register", methods=['POST'])
def register():
    db = get_db()
    cur = db.cursor()
    username = request.json['username']
    password = request.json['password']
    password_hash = hash_password(password)
    cur.execute('INSERT INTO users (username, password_hash) VALUES (%s, %s)', (username, password_hash))
    db.commit()
    cur.close()
    return jsonify({"result": True})

@app.route("/api/login", methods=['POST'])
def login():
    try:
        db = get_db()
        cur = db.cursor()
        username = request.json['username']
        password = request.json['password']
        cur.execute('SELECT id, username, password_hash FROM users WHERE username=%s', (username,))
        user = cur.fetchone()
        cur.close()
        if user and user[2] == hash_password(password):
            session['user_id'] = user[0]
            session['username'] = user[1]
            return jsonify({"result": True})
        else:
            return jsonify({"result": False})
    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({"result": False, "error": "An error occurred during login"})

def get_user_id(username):
    if username:
        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT id FROM users WHERE username=%s', (username,))
        user = cur.fetchone()
        cur.close()
        if user:
            return user[0]
    return None

@app.route("/api/items")
def get_items():
    username = request.json.get('username')
    user_id = get_user_id(username)
    if user_id:
        db = get_db()
        cur = db.cursor()
        cur.execute('SELECT id, what_to_do, due_date, status, recurring_interval FROM entries WHERE user_id=%s ORDER BY due_date ASC', (user_id,))
        entries = cur.fetchall()
        cur.close()
        tdlist = [dict(id=row[0], what_to_do=row[1], due_date=row[2].strftime('%Y-%m-%d') if row[2] else None, status=row[3], recurring_interval=row[4] or 'No')
                  for row in entries]
        response = Response(json.dumps(tdlist), mimetype='application/json')
        return response
    else:
        return jsonify([])


@app.route("/api/items", methods=['POST'])
def add_item():
    username = request.json.get('username')
    user_id = get_user_id(username)
    print(f"User ID: {user_id}")  # Debug statement

    if user_id:
        db = get_db()
        cur = db.cursor()
        what_to_do = request.json['what_to_do']
        due_date = request.json.get('due_date')
        recurring_interval = request.json.get('recurring_interval')

        print(f"What to do: {what_to_do}")  # Debug statement
        print(f"Due date: {due_date}")  # Debug statement
        print(f"Recurring interval: {recurring_interval}")  # Debug statement

        try:
            cur.execute('INSERT INTO entries (what_to_do, due_date, recurring_interval, user_id) VALUES (%s, %s, %s, %s)',
                        (what_to_do, due_date, recurring_interval, user_id))
            new_id = cur.lastrowid
            db.commit()
            print(f"New entry added with ID: {new_id}")  # Debug statement
            cur.close()
            return jsonify({"id": new_id})
        except Exception as e:
            print(f"Error adding entry: {str(e)}")  # Debug statement
            db.rollback()
            cur.close()
            return jsonify({"result": False, "error": "An error occurred while adding the entry"})
    else:
        print("User not logged in")  # Debug statement
        return jsonify({"result": False, "error": "User not logged in"})



@app.route("/api/items/<int:item_id>", methods=['DELETE'])
def delete_item(item_id):
    username = request.json.get('username')
    user_id = get_user_id(username)
    if user_id:
        db = get_db()
        cur = db.cursor()
        cur.execute("DELETE FROM entries WHERE id=%s AND user_id=%s", (item_id, user_id))
        db.commit()
        cur.close()
        return jsonify({"result": True})
    else:
        return jsonify({"result": False})

@app.route("/api/items/<int:item_id>", methods=['PUT'])
def update_item(item_id):
    username = request.json.get('username')
    user_id = get_user_id(username)
    if user_id:
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT * FROM entries WHERE id=%s AND user_id=%s", (item_id, user_id))
        entry = cur.fetchone()
        if entry:
            cur.execute("UPDATE entries SET status='done' WHERE id=%s", (item_id,))
            if entry[4]:  # if recurring_interval is not empty
                due_date = entry[2]
                if entry[4] == 'daily':
                    due_date += timedelta(days=1)
                elif entry[4] == 'weekly':
                    due_date += timedelta(weeks=1)
                elif entry[4] == 'monthly':
                    due_date += relativedelta(months=1)
                elif entry[4] == 'yearly':
                    due_date += relativedelta(years=1)
                cur.execute('INSERT INTO entries (what_to_do, due_date, recurring_interval, user_id) VALUES (%s, %s, %s, %s)',
                            (entry[1], due_date, entry[4], user_id))
            db.commit()
        cur.close()
        return jsonify({"result": True})
    else:
        return jsonify({"result": False})


@app.route("/api/search")
def search_items():
    username = request.json.get('username')
    user_id = get_user_id(username)
    if user_id:
        query = request.args.get('query', '')
        db = get_db()
        cur = db.cursor()
        cur.execute("SELECT id, what_to_do, due_date, status, recurring_interval FROM entries WHERE user_id=%s AND what_to_do LIKE %s ORDER BY due_date ASC", 
                    (user_id, '%' + query + '%'))
        entries = cur.fetchall()
        cur.close()
        tdlist = [dict(id=row[0], what_to_do=row[1], due_date=row[2].strftime('%Y-%m-%d') if row[2] else None, status=row[3], recurring_interval=row[4] or 'No')
                  for row in entries]
        response = Response(json.dumps(tdlist), mimetype='application/json')
        return response
    else:
        return jsonify([])

def get_db():
    if not hasattr(g, 'mysql_db'):
        g.mysql_db = mysql.connector.connect(
            host="localhost",
            database=DATABASE,
            user="todo_app",
            password="todo_password"
        )
    return g.mysql_db

@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'mysql_db'):
        g.mysql_db.close()

if __name__ == "__main__":
    app.run("0.0.0.0", port=5001)

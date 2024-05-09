from flask import Flask, render_template, redirect, g, request, url_for, jsonify, Response
import mysql.connector
import urllib
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

DATABASE = 'todolist'

app = Flask(__name__)
app.config.from_object(__name__)

@app.route("/api/items")
def get_items():
    db = get_db()
    cur = db.cursor()
    cur.execute('SELECT id, what_to_do, due_date, status, recurring_interval FROM entries ORDER BY due_date ASC')
    entries = cur.fetchall()
    cur.close()
    tdlist = [dict(id=row[0], what_to_do=row[1], due_date=row[2].strftime('%Y-%m-%d') if row[2] else None, status=row[3], recurring_interval=row[4] or 'No')
              for row in entries]
    response = Response(json.dumps(tdlist), mimetype='application/json')
    return response

@app.route("/api/items", methods=['POST'])
def add_item():
    db = get_db()
    cur = db.cursor()
    what_to_do = request.json['what_to_do']
    due_date = request.json.get('due_date')
    recurring_interval = request.json.get('recurring_interval')
    cur.execute('INSERT INTO entries (what_to_do, due_date, recurring_interval) VALUES (%s, %s, %s)',
                (what_to_do, due_date, recurring_interval))
    new_id = cur.lastrowid
    db.commit()
    cur.close()
    return jsonify({"id": new_id})


@app.route("/api/items/<int:item_id>", methods=['DELETE'])
def delete_item(item_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM entries WHERE id=%s", (item_id,))
    db.commit()
    cur.close()
    return jsonify({"result": True})

@app.route("/api/items/<int:item_id>", methods=['PUT'])
def update_item(item_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT * FROM entries WHERE id=%s", (item_id,))
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
            cur.execute('INSERT INTO entries (what_to_do, due_date, recurring_interval) VALUES (%s, %s, %s)',
                        (entry[1], due_date, entry[4]))
        db.commit()
    cur.close()
    return jsonify({"result": True})

@app.route("/api/search")
def search_items():
    query = request.args.get('query', '')
    db = get_db()
    cur = db.cursor()
    cur.execute("SELECT id, what_to_do, due_date, status, recurring_interval FROM entries WHERE what_to_do LIKE %s ORDER BY due_date ASC", ('%' + query + '%',))
    entries = cur.fetchall()
    cur.close()
    tdlist = [dict(id=row[0], what_to_do=row[1], due_date=row[2].strftime('%Y-%m-%d') if row[2] else None, status=row[3], recurring_interval=row[4] or 'No')
              for row in entries]
    response = Response(json.dumps(tdlist), mimetype='application/json')
    return response

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

from flask import Flask, render_template, redirect, g, request, url_for, jsonify, json, session
import urllib
import requests
import os

app = Flask(__name__)
TODO_API_URL = "http://"+os.environ['TODO_API_IP']+":5001"
# TODO_API_URL = "http://localhost:5001"
app.secret_key = b'\x9f\xff\xd4\xe7\xc9\x91\xe9o/L\x93\xdb\x16\xe9\xc2r\xdf\x99\x84\xae\xef?\xc7/'

@app.route("/auth", methods=['GET', 'POST'])
def auth():
    error = None
    success = None
    if request.method == 'POST':
        if request.form['action'] == 'register':
            username = request.form['username']
            password = request.form['password']
            response = requests.post(TODO_API_URL + "/api/register", json={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                result = response.json()
                if result['result']:
                    success = "Registration successful. Please login."
                else:
                    error = result.get('error', "An error occurred during registration.")
            else:
                error = "An error occurred during registration."
        elif request.form['action'] == 'login':
            username = request.form['username']
            password = request.form['password']
            response = requests.post(TODO_API_URL + "/api/login", json={
                "username": username,
                "password": password
            })
            if response.status_code == 200:
                result = response.json()
                if result['result']:
                    session['username'] = username
                    return redirect(url_for('show_list'))
                else:
                    error = "Invalid username or password."
            else:
                error = "An error occurred during login."
    return render_template('auth.html', error=error, success=success, username=request.form.get('username', ''))



@app.route("/logout")
def logout():
    requests.get(TODO_API_URL + "/api/logout")
    session.pop('username', None)
    return redirect(url_for('auth'))

@app.route("/")
def show_list():
    username = session.get('username')
    if not username:
        return redirect(url_for('auth'))
    resp = requests.get(TODO_API_URL + "/api/items", json={"username": username})
    resp = resp.json()
    return render_template('index.html', todolist=resp, username=username)

@app.route("/add", methods=['POST'])
def add_entry():
    what_to_do = request.form['what_to_do']
    due_date = request.form.get('due_date')
    recurring_interval = request.form.get('recurring_interval')
    response = requests.post(TODO_API_URL + "/api/items", json={
        "what_to_do": what_to_do,
        "due_date": due_date if due_date else None,
        "recurring_interval": recurring_interval if recurring_interval else None,
        "username": session.get('username')
    })
    if response.status_code == 200:
        return redirect(url_for('show_list'))
    else:
        return "Error adding entry", 500

@app.route("/delete/<int:item_id>")
def delete_entry(item_id):
    requests.delete(TODO_API_URL + "/api/items/" + str(item_id), json={"username": session.get('username')})
    return redirect(url_for('show_list'))

@app.route("/mark/<int:item_id>")
def mark_as_done(item_id):
    requests.put(TODO_API_URL + "/api/items/" + str(item_id), json={"username": session.get('username')})
    return redirect(url_for('show_list'))

@app.route("/search")
def search_entries():
    query = request.args.get('query', '')
    resp = requests.get(TODO_API_URL + "/api/search?query=" + query, json={"username": session.get('username')})
    resp = resp.json()
    return jsonify(resp)



if __name__ == "__main__":
    app.run("0.0.0.0")

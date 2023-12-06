import flask 

import models 
from flask import request, url_for
from sqlalchemy.sql import func

app = flask.Flask("hrms")
db = models.SQLAlchemy(model_class=models.HRDBBase)

@app.route("/", methods=["GET"])
def index():
    if flask.request.method == "GET":
        return flask.render_template("index.html")


@app.route("/employees")
def employees():
    query = db.select(models.Employee).order_by(models.Employee.fname)
    users = db.session.execute(query).scalars()
    return flask.render_template("userlist.html", users = users)


@app.route("/employees/<int:empid>")
def employee_details(empid):
    query = db.select(models.Employee).order_by(models.Employee.fname)
    users = db.session.execute(query).scalars()
    query1 = db.select(models.Employee).where(models.Employee.id == empid)
    user = db.session.execute(query1).scalar()

    query_for_leaves = db.select(func.count(models.Employee.id)).join(models.Leave, models.Employee.id == models.Leave.employee_id).filter(models.Employee.id == empid)
    leave = db.session.execute(query_for_leaves).scalar()

    return flask.render_template("userdetails.html", user = user, leave = leave, users= users) 


@app.route("/add_leave/<int:empid>", methods=["GET", "POST"])
def add_leave(empid):
    if request.method == "POST":
        leave_date = request.form.get('leave_date')
        leave_reason = request.form.get('leave_reason')

        new_leave = models.Leave(date=leave_date,reason=leave_reason,employee_id=empid)

        db.session.add(new_leave)
        db.session.commit()
        return "Leave details added successfully"

    return flask.render_template("add_leave.html", employee_id=empid)


@app.route('/about')
def about():
    return flask.render_template('about.html')


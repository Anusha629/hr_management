import flask 

import models 
from flask import request, url_for, redirect, jsonify
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
    return flask.render_template("userlist.html", users=users)


cache={}
@app.route("/employees/<int:empid>", methods=["GET", "POST"])
def employee_details(empid):
    if empid in cache:
        print (f"returning {empid} from cache")
        return jsonify(cache[empid])
    else:
        query1 = db.select(models.Employee).where(models.Employee.id == empid)
        user = db.session.execute(query1).scalar()
        
        query_for_leaves = db.select(func.count(models.Employee.id)).join(models.Leave, models.Employee.id == models.Leave.employee_id).filter(models.Employee.id == empid)
        leave = db.session.execute(query_for_leaves).scalar()

        query2 = db.select(models.Designation.max_leaves).where(models.Designation.id == models.Employee.title_id)
        max_leaves = db.session.execute(query2).scalar()

        if request.method == 'POST':
            date = request.form.get['leavedate']
            reason = request.form.get['leavereason']
            new_leave = models.Leave(date=date, employee_id=empid, reason=reason)
            db.session.add(new_leave)
            db.session.commit()

        ret = {
            "id": user.id,
            "fname": user.fname,
            "lname": user.lname,
            "title": user.title.title,
            "email": user.email,
            "phone": user.phone,
            "leave": leave,
            "max_leaves": max_leaves,
            "remaining_leaves": max_leaves - leave}
        return flask.jsonify(ret) 

@app.route("/add_leave/<int:empid>", methods=["GET", "POST"])
def add_leave(empid):
    if request.method == "POST":
        leave_date = request.form.get('leave_date')
        leave_reason = request.form.get('leave_reason')

        new_leave = models.Leave(date=leave_date,reason=leave_reason,employee_id=empid)

        db.session.add(new_leave)
        db.session.commit()
        return redirect(url_for("employees"))


@app.route('/about')
def about():
    return flask.render_template('about.html')


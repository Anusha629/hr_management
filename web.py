import flask 

import models 
from flask import request
from sqlalchemy.sql import func
from flask_cors import CORS

app = flask.Flask("hrms")
CORS(app) 

db = models.SQLAlchemy(model_class=models.HRDBBase)

@app.route("/", methods=["GET"])
def index():
    if flask.request.method == "GET":
        return flask.render_template("index.html")


@app.route("/employees")
def employees():
    users= db.select(models.Employee).order_by(models.Employee.fname)
    users = db.session.execute(users).scalars()

    u_list = []
    for user in users:
        data = {
            "id": user.id,
            "fname": user.fname,
            "lname": user.lname,
            "title": user.title.title,
            "email": user.email,
            "phone": user.phone}
        u_list.append(data)

    return flask.jsonify(u_list)


@app.route("/employees/<int:empid>", methods=["GET"])
def employee_details(empid):
    
    employee = db.select(models.Employee).where(models.Employee.id == empid)
    user = db.session.execute(employee).scalar()
    
    query_for_leaves = db.select(func.count(models.Employee.id)).join(models.Leave, models.Employee.id == models.Leave.employee_id).filter(models.Employee.id == empid)
    leave = db.session.execute(query_for_leaves).scalar()

    leaves = db.select(models.Designation.max_leaves).where(models.Designation.id == models.Employee.title_id)
    max_leaves = db.session.execute(leaves).scalar()
        
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


@app.errorhandler(500)   
def page_not_found(error):
    return flask.render_template('500.html'), 500

@app.errorhandler(404)   
def page_not_found(error):
    return flask.render_template('404.html'), 404


@app.route("/leaves/<int:empid>", methods=["POST"])
def add_leave(empid):
    if request.method == "POST":
        try:
            leave_date = request.form.get('leave_date')
            leave_reason = request.form.get('leave_reason')

            new_leave = models.Leave(date=leave_date,reason=leave_reason,employee_id=empid)
            print(f"Received leave data: {leave_date}, {leave_reason}")

            db.session.add(new_leave)
            db.session.commit()
            return flask.jsonify({"message": "Leave details submitted successfully!"})
        
        except Exception as e:
            print(f"Error adding leave: {str(e)}")
            return flask.jsonify({"error": str(e)}), 500
        

@app.route('/about')
def about():
    return flask.render_template('about.html')

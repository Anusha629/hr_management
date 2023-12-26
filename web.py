import flask 
import models 
from flask import request
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

    employee = db.session.query(models.Employee).filter_by(id=empid).first()

    leaves_taken = db.session.query(models.Leave).filter_by(employee_id=empid).count()
    title_id = employee.title_id

    designation = db.session.query(models.Designation).filter_by(id=title_id).first()
    max_leaves = designation.max_leaves

    remaining_leaves = max_leaves - leaves_taken 

    ret = {
        "id": employee.id,
        "fname": employee.fname,
        "lname": employee.lname,
        "title": employee.title.title,
        "email": employee.email,
        "phone": employee.phone,
        "leave": leaves_taken,
        "max_leaves": max_leaves,
        "remaining_leaves": remaining_leaves }

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
            employee = db.session.query(models.Employee).get(empid)

            if not employee:
                return flask.jsonify({"error": "Employee not found"}), 404
            
            leave_date = request.form.get('leave_date')
            leave_reason = request.form.get('leave_reason')

            leaves_taken = db.session.query(models.Leave).filter_by(employee_id=empid).count()
            max_leaves = employee.title.max_leaves

            if leaves_taken < max_leaves:
                new_leave = models.Leave(date=leave_date, reason=leave_reason, employee_id=empid)

                db.session.add(new_leave)
                db.session.commit()

                return flask.jsonify({"message": "Leave details submitted successfully!"}), 200 
            else:
                return flask.jsonify({"error": "Leaves exceed the maximum allowed"}), 403 
            
        except Exception as e:
            return flask.jsonify({"error": "Leave already exists for this date"}), 400


@app.route('/about')
def about():
    return flask.render_template('about.html') 

if __name__ == '__main__':
    app.run()


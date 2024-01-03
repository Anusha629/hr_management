import argparse
import csv
import logging
import os
import sys
import configparser
import requests

import models
import web

class HRException(Exception): pass

logger = False 

def parse_args():
    parser = argparse.ArgumentParser(description="HR Management")
    config = configparser.ConfigParser()
    config.read('config.ini')
    parser.add_argument("-d","--dbname", help="Adding database name", action="store", type=str, default=config.get('Database', 'dbname'))
    parser.add_argument("-v", "--verbose", help="Print detailed logging", action="store_true", default=False)
 
    # initdb
    subparsers = parser.add_subparsers(dest="op")
    parser_initdb = subparsers.add_parser("initdb", help="Initialize creation of database and table")

    web_parser = subparsers.add_parser("web", help="Start web server")
    
    # import csv
    import_parser = subparsers.add_parser("import", help="Import data from csv file")
    import_parser.add_argument("employees_file", help="List of employees to import")

    #fetch vcard of single employee
    query_parser = subparsers.add_parser("vcard", help="Get information for a single employee")
    query_parser.add_argument("id", help="employee id")
    
    # fetch qr code
    parser_fetch_qr = subparsers.add_parser("qr", help="Generate QR code for an employee using employee ID")
    parser_fetch_qr.add_argument("id", help="Employee ID to generate QR code", type=int)
    parser_fetch_qr.add_argument("-s", "--size", help="Size of QR codes", action='store', type=int, default=500)
    parser_fetch_qr.add_argument("-d", "--directory", help="Output directory for generated QR codes", type=str) 

    #fetch all qr & vcard
    parser_fetch_all = subparsers.add_parser("all", help="Generate QR code and vCard for all employees")
    parser_fetch_all.add_argument("-s", "--size", help="Size of QR codes", action='store', type=int, default=500)
    parser_fetch_all.add_argument("-dir", "--output_directory", help="Output directory path for generated QR codes", type=str)

    # add leave
    parser_leave = subparsers.add_parser("leave", help="Add leave to database. Data format is (YYYY-MM-DD)")
    parser_leave.add_argument("date", type=str, help="Date of leave")
    parser_leave.add_argument("employee_id", type=int, help="Employee id")
    parser_leave.add_argument("reason", type=str, help="Reason of leave")

    #leave_summary of single employee
    parser_summary = subparsers.add_parser("summary", help="Leave summary")
    parser_summary.add_argument("employee_id", type=int, help="Employee id")
    
    #leave_summary export
    parser_export = subparsers.add_parser("export", help="Export leave summary")
    parser_export.add_argument("directory", help="Directory name to export leave summary")

    args = parser.parse_args()
    return args 


def init_logger(is_verbose):
    global logger
    if is_verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    logger = logging.getLogger("HR")
    handler = logging.StreamHandler()
    handler.setLevel(level)
    handler.setFormatter(logging.Formatter("[%(levelname)s] | %(filename)s:%(lineno)d | %(message)s"))
    logger.setLevel(logging.DEBUG)
    logger.addHandler(handler)

def initialize_db(args):
    db_uri = f"postgresql:///{args.dbname}"
    models.create_all(db_uri)
    session = models.get_session(db_uri)

    existing_designations = session.query(models.Designation).first()
    if not existing_designations:
        d1 = models.Designation(title="Staff Engineer", max_leaves=10)
        d2 = models.Designation(title="Senior Engineer", max_leaves=20)
        d3 = models.Designation(title="Junior Engineer", max_leaves=40)
        d4 = models.Designation(title="Tech Lead", max_leaves=15)
        d5 = models.Designation(title="Project Manager", max_leaves=15)

        session.add(d1)
        session.add(d2)
        session.add(d3)
        session.add(d4)
        session.add(d5)
        session.commit()

    
def import_data_to_db(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = models.get_session(db_uri)

    existing_employees = session.query(models.Employee).first()
    if not existing_employees:

        with open(args.employees_file) as f:
            reader = csv.reader(f)
            for lname, fname, title, email, phone in reader:
                designation = session.query(models.Designation).filter(models.Designation.title == title).first()
                
                if designation:
                    logger.info("Inserting %s", email)
                    employee = models.Employee(lname=lname, fname=fname, title=designation, email=email, phone=phone)
                    session.add(employee)
                else:
                    logger.warning(f"No designation found for title: {title}")
            session.commit()


def create_vcard(lname, fname, designation, email, phone):
    return f"""BEGIN:VCARD
VERSION:2.1
N:{lname};{fname}
FN:{fname} {lname}
ORG:Authors, Inc.
TITLE:{designation}
TEL;WORK;VOICE:{phone}
ADR;WORK:;;100 Flat Grape Dr.;Fresno;CA;95555;United States of America
EMAIL;PREF;INTERNET:{email}
REV:20150922T195243Z
END:VCARD"""

def create_vcard_from_db(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = models.get_session(db_uri)
    employee_id = int(args.id)

    employee = session.query(models.Employee).filter(models.Employee.id == employee_id).first()

    if employee:
        vcard = create_vcard(employee.lname,employee.fname,employee.title.title,employee.email,employee.phone)
        if vcard:
            print(vcard)
        else:
            logger.error("Failed to generate vCard.")
    else:
        logger.error("Employee with ID %s not found", employee_id)


def insert_leaves(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = models.get_session(db_uri)
    date = args.date
    employee_id = args.employee_id
    reason = args.reason

    employee = session.query(models.Employee).filter(models.Employee.id == employee_id).first()

    if employee:
        total_leaves = employee.title.max_leaves
        leaves_taken = session.query(models.Leave).filter(models.Leave.employee_id == employee_id).count()
        leaves_remaining = total_leaves - leaves_taken

        if leaves_remaining > 0:
            existing_leave = session.query(models.Leave).filter(models.Leave.date == date, models.Leave.employee_id == employee_id).first()

            if existing_leave:
                logger.info("Leave entry for Employee ID %s on %s already exists with reason: %s", employee_id, date, existing_leave.reason)
            else:
                new_leave = models.Leave(date=date, employee_id=employee_id, reason=reason)
                session.add(new_leave)
                session.commit()
                logger.info("Leave added for Employee ID %s on %s with reason: %s", employee_id, date, reason)
        else:
            logger.warning("Leave limit reached for Employee ID %s. Cannot add more leaves.", employee_id)
    else:
        logger.error("Employee with ID %s not found", employee_id)


def get_leave_summary(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = models.get_session(db_uri)
    employee_id = args.employee_id

    employee = session.query(models.Employee).filter(models.Employee.id == employee_id).first()
    if employee:
        total_leaves = employee.title.max_leaves
        leaves_taken = session.query(models.Leave).filter(models.Leave.employee_id == employee_id).count()
        leaves_remaining = total_leaves - leaves_taken

        print(f"Leave summary for Employee ID {employee_id}:")
        print(f"Total Leaves Allowed: {total_leaves}")
        print(f"Leaves Taken: {leaves_taken}")
        print(f"Leaves Remaining: {leaves_remaining}")

        return { 'Total Leaves Allowed': total_leaves,
            'Leaves Taken': leaves_taken,
            'Leaves Remaining': leaves_remaining}
    else:
        logger.error("Employee with ID %s not found", employee_id) 


def create_qr_code(args):
    employee_id = args.id  
    size = args.size
    output_directory = getattr(args, 'output_directory', None) or getattr(args, 'directory', None) 
    dbname = args.dbname
    db_uri = f"postgresql:///{dbname}"
    session = models.get_session(db_uri)

    employee = session.query(models.Employee).filter(models.Employee.id == employee_id).first()

    if employee:
        vcard = create_vcard(employee.lname, employee.fname, employee.title.title, employee.email, employee.phone)
        qr_code_content = requests.get(f"https://chart.googleapis.com/chart?cht=qr&chs={size}x{size}&chl={vcard}").content

        file_name = f"{employee_id}_vcard_qr.png"
        file_path = os.path.join(output_directory, file_name)

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        with open(file_path, "wb") as qr_file:
            qr_file.write(qr_code_content)

        logger.info(f"QR code saved at: {file_path}")
    else:
        logger.error(f"No employee found with ID: {employee_id}")


def get_all_details(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = models.get_session(db_uri)

    employees = session.query(models.Employee).all()

    if employees:
        output_directory = args.output_directory or args.directory
        os.makedirs(output_directory, exist_ok=True)

        for employee in employees:
            vcard = create_vcard(employee.lname, employee.fname, employee.title.title, employee.email, employee.phone)
            vcard_file = f"{employee.id}_vcard.vcf"
            vcard_file_path = os.path.join(output_directory, vcard_file)

            if not os.path.exists(output_directory):
                os.makedirs(output_directory)

            with open(vcard_file_path, "w") as vcard_file:
                vcard_file.write(vcard)
            qr_args = argparse.Namespace(id=employee.id, size=args.size, output_directory=args.output_directory, dbname=args.dbname)
            create_qr_code(qr_args)

        logger.info("vCard and QR codes saved for all employees")
    else:
        logger.error("No employees found in the database.")



def export_leave_summary(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = models.get_session(db_uri)
    employees = session.query(models.Employee).all()
    os.makedirs(args.directory, exist_ok=True)
    file = os.path.join(args.directory, 'leave_summary.csv')

    with open(file, 'w', newline='') as csvfile:
        fieldnames = ['Employee ID', 'First Name', 'Last Name', 'Designation', 'Total Leaves', 'Leaves Taken', 'Leaves Remaining']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for employee in employees:
            total_leaves = employee.title.max_leaves
            leaves_taken = session.query(models.Leave).filter(models.Leave.employee_id == employee.id).count()
            leaves_remaining = total_leaves - leaves_taken

            writer.writerow({
                'Employee ID': employee.id,
                'First Name': employee.fname,
                'Last Name': employee.lname,
                'Designation': employee.title.title,
                'Total Leaves': total_leaves,
                'Leaves Taken': leaves_taken,
                'Leaves Remaining': leaves_remaining})

    logger.info(f"Leave summary exported to {file}")

def update_config(dbname):
  config = configparser.ConfigParser()
  config.read('config.ini')
  config.set('Database','dbname',dbname)
  with open('config.ini','w') as config_file:
     config.write(config_file) 


def handle_web(args):
    web.app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql:///{args.dbname}"
    web.db.init_app(web.app)
    web.app.run()


def main():
    try:
        args = parse_args()
        init_logger(args.verbose)
        update_config(args.dbname)
        ops = {
            "initdb": initialize_db,
            "import": import_data_to_db,
            "web": handle_web,
            "vcard": create_vcard_from_db,
            "qr": create_qr_code,
            "all": get_all_details,
            "leave": insert_leaves,
            "summary": get_leave_summary,
            "export": export_leave_summary}
        ops[args.op](args)

    except HRException as e:
        logger.error("Program aborted, %s", e)
        sys.exit(-1)

if __name__=="__main__":
    main()

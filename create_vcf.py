import argparse
import csv
import logging
import os
import sys
import configparser
import requests
import db

class HRException(Exception): pass

logger = False 

def parse_args():
    parser = argparse.ArgumentParser(description="HR Management")
    config = configparser.ConfigParser()
    config.read('config.ini')
    parser.add_argument("-d","--dbname", help="Adding database name", action="store", type=str, default=config.get('Database', 'dbname'))
 
    # initdb
    subparsers = parser.add_subparsers(dest="op")
    parser_initdb = subparsers.add_parser("initdb", help="Initialize creation of database and table")
    
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

    parser.add_argument("-n", "--number", help="Number of records to generate", action="store", type=int, default=10)
    parser.add_argument("-v", "--verbose", help="Print detailed logging", action="store_true", default=False)

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
    db.create_all(db_uri)
    session = db.get_session(db_uri)

    existing_designations = session.query(db.Designation).first()
    if not existing_designations:
        d1 = db.Designation(title="Staff Engineer", max_leaves=10)
        d2 = db.Designation(title="Senior Engineer", max_leaves=20)
        d3 = db.Designation(title="Junior Engineer", max_leaves=40)
        d4 = db.Designation(title="Tech Lead", max_leaves=15)
        d5 = db.Designation(title="Project Manager", max_leaves=15)

        session.add(d1)
        session.add(d2)
        session.add(d3)
        session.add(d4)
        session.add(d5)
        session.commit()

    
def import_data_to_db(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = db.get_session(db_uri)

    existing_employees = session.query(db.Employee).first()
    if not existing_employees:

        with open(args.employees_file) as f:
            reader = csv.reader(f)
            for lname, fname, title, email, phone in reader:
                designation = session.query(db.Designation).filter(db.Designation.title == title).first()
                
                if designation:
                    logger.info("Inserting %s", email)
                    employee = db.Employee(lname=lname, fname=fname, title=designation, email=email, phone=phone)
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

def generate_vcard(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = db.get_session(db_uri)
    employee_id = int(args.id)

    employee = session.query(db.Employee).filter(db.Employee.id == employee_id).first()

    if employee:
        vcard = create_vcard(employee.lname,employee.fname,employee.title.title,employee.email,employee.phone)
        if vcard:
            print(vcard)
        else:
            logger.error("Failed to generate vCard.")
    else:
        logger.error("Employee with ID %s not found", employee_id)


def add_leaves(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = db.get_session(db_uri)
    date = args.date
    employee_id = args.employee_id
    reason = args.reason

    employee = session.query(db.Employee).filter(db.Employee.id == employee_id).first()

    if employee:
        total_leaves = employee.title.max_leaves
        leaves_taken = session.query(db.Leave).filter(db.Leave.employee_id == employee_id).count()
        leaves_remaining = total_leaves - leaves_taken

        if leaves_remaining > 0:
            existing_leave = session.query(db.Leave).filter(db.Leave.date == date, db.Leave.employee_id == employee_id).first()

            if existing_leave:
                logger.info("Leave entry for Employee ID %s on %s already exists with reason: %s", employee_id, date, existing_leave.reason)
            else:
                new_leave = db.Leave(date=date, employee_id=employee_id, reason=reason)
                session.add(new_leave)
                session.commit()
                logger.info("Leave added for Employee ID %s on %s with reason: %s", employee_id, date, reason)
        else:
            logger.warning("Leave limit reached for Employee ID %s. Cannot add more leaves.", employee_id)
    else:
        logger.error("Employee with ID %s not found", employee_id)


def get_leave_summary(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = db.get_session(db_uri)
    employee_id = args.employee_id

    employee = session.query(db.Employee).filter(db.Employee.id == employee_id).first()
    if employee:
        total_leaves = employee.title.max_leaves
        leaves_taken = session.query(db.Leave).filter(db.Leave.employee_id == employee_id).count()
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


def generate_qr_code(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = db.get_session(db_uri)
    employee_id = args.id

    employee = session.query(db.Employee).filter(db.Employee.id == employee_id).first()

    if employee:
        vcard = create_vcard(employee.lname, employee.fname, employee.title.title, employee.email, employee.phone)
        qr_code_content = requests.get(f"https://chart.googleapis.com/chart?cht=qr&chs={args.size}x{args.size}&chl={vcard}").content
        
        output_directory = args.directory
        
        os.makedirs(output_directory, exist_ok=True)
        file_name = f"{employee_id}_vcard_qr.png"
        file_path = os.path.join(output_directory, file_name)
        
        with open(file_path, "wb") as qr_file:
            qr_file.write(qr_code_content)

        logger.info(f"QR code saved at: {file_path}")
    else:
        logger.error(f"No employee found with ID: {employee_id}") 

def generate_all_details(args):
    db_uri = f"postgresql:///{args.dbname}"
    session = db.get_session(db_uri)

    employees = session.query(db.Employee).all()

    if employees:
        output_directory = args.output_directory
        os.makedirs(output_directory, exist_ok=True)

        for employee in employees:
            vcard = create_vcard(employee.lname, employee.fname, employee.title.title, employee.email, employee.phone)
            vcard_file = f"{employee.id}_vcard.vcf"
            vcard_file_path = os.path.join(output_directory, vcard_file)
            with open(vcard_file_path, "w") as vcard_file:
                vcard_file.write(vcard)

            qr_args = argparse.Namespace(
                id=employee.id,
                size=args.size,
                directory=output_directory,
                dbname=args.dbname)
            generate_qr_code(qr_args)
        logger.info("vCard and QR codes saved for all employees")
    else:
        logger.error("No employees found in the database.")

def export_leave_summary(db_name, directory):
    db_uri = f"postgresql:///{db_name}"
    session = db.get_session(db_uri)
    employees = session.query(db.Employee).all()
    os.makedirs(directory, exist_ok=True)
    file = os.path.join(directory, 'leave_summary.csv')

    with open(file, 'w', newline='') as csvfile:
        fieldnames = ['Employee ID', 'First Name', 'Last Name', 'Designation', 'Total Leaves', 'Leaves Taken', 'Leaves Remaining']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for employee in employees:
            total_leaves = employee.title.max_leaves
            leaves_taken = session.query(db.Leave).filter(db.Leave.employee_id == employee.id).count()
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

def main():
    try:
        args = parse_args()
        init_logger(args.verbose)
        update_config(args.dbname)
        ops = {
            "initdb": initialize_db,
            "import": import_data_to_db,
            "vcard": generate_vcard,
            "qr": generate_qr_code,
            "all": generate_all_details,
            "leave": add_leaves,
            "summary": get_leave_summary,
            "export": export_leave_summary}
        if args.op == 'export':
            ops[args.op](args.dbname, args.directory)
        else:
            ops[args.op](args)
    except HRException as e:
        logger.error("Program aborted, %s", e)
        sys.exit(-1)


if __name__=="__main__":
    main()

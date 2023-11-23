import argparse
import logging
import psycopg2
import sys
import csv
import requests
import os

class HRException(Exception): pass

logger = False 

def parse_args():
    parser = argparse.ArgumentParser(
        prog="create_vcf.py", description="Generate employee database")
    parser.add_argument("--dbname", help="Adding database name", action="store", type=str, default='Employees_db')
    parser.add_argument("--dbuser", help="Adding user name of database", action="store", type=str, default='anusha')
    
    # Subcommand initdb
    subparsers = parser.add_subparsers(dest="op")
    parser_initdb = subparsers.add_parser("initdb", help="Initialize creation of database and table")
    
    # import csv
    import_parser = subparsers.add_parser("import", help="Import data from csv file")
    import_parser.add_argument("employees_file", help="List of employees to import")

    #fetch vcard
    query_parser = subparsers.add_parser("query", help="Get information for a single employee")
    query_parser.add_argument("--vcard", action="store_true", default=False, help="Generate vcard for employee")
    query_parser.add_argument("id", help="employee id")
    query_parser.add_argument("-q","--qrcode", action="store_true", default=False, help="Generate qrcode for employee")
    query_parser.add_argument("-s", "--size", help="Size of qr codes", action='store', type=int, default=500)

    # add leave
    parser_leave = subparsers.add_parser("leave", help="Add leave to database")
    parser_leave.add_argument("date", type=str, help="Date of leave")
    parser_leave.add_argument("employee_id", type=int, help="Employee id")
    parser_leave.add_argument("reason", type=str, help="Reason of leave")

    #leave_summary
    parser_summary = subparsers.add_parser("summary", help="Leave summary")
    parser_summary.add_argument("employee_id", type=int, help="Employee id")
    parser_summary.add_argument("export",help="export to csv file")
    
    #csv_leave_summary
    parser_export = subparsers.add_parser("export", help="Export leave summary")
    parser_export.add_argument("directory", help="Directory to export leave summary")

    #add designation
    parser_designation = subparsers.add_parser("designation", help="Add designation to database")
    parser_designation.add_argument("name", type=str, help="Name of designation")
    parser_designation.add_argument("percentage", type=int, help="Employees in designation")
    parser_designation.add_argument("leaves", type=str, help="Total number of leaves")

    parser.add_argument("-n", "--number", help="Number of records to generate", action="store", type=int, default=10)
    parser.add_argument("-v", "--verbose", help="Print detailed logging", action="store_true", default=False)
    parser.add_argument("-q", "--add_qr", help="Add QR codes", action="store_true", default=False)
    parser.add_argument("-s", "--qr_size", help="Size of QR code", type=int, default=500)
    parser.add_argument("-a", "--address", help="Employee address", type=str, default="100 Flat Grape Dr.;Fresno;CA;95555;United States of America")

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
    with open("data/init.sql") as f:
        sql=f.read()
        logger.debug(sql)
    try:
        con=psycopg2.connect(dbname=args.dbname)
        cur=con.cursor()
        cur.execute(sql)
        con.commit()
        logger.info("Initialize Database Successfully")
    except psycopg2.OperationalError as e:
        raise HRException(f"Database '{args.dbname}' doesn't exist")
    
def truncate_table(args):
    conn = psycopg2.connect(dbname=args.dbname, user=args.dbuser)
    cursor = conn.cursor()
    truncate_table_query = "TRUNCATE TABLE employees RESTART IDENTITY CASCADE"
    cursor.execute(truncate_table_query)
    conn.commit()
    conn.close()


def import_data_to_db(args):
    truncate_table(args)
    con = psycopg2.connect(dbname=args.dbname)
    cur = con.cursor()
    with open(args.employees_file) as f:
        reader = csv.reader(f)
        for lname, fname, designation, email, phone in reader:
            logger.debug("Inserting %s", email)
            query = "INSERT INTO employees(last_name, first_name, email, phone, designation_id) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(query, (lname, fname, designation, email, phone))
        con.commit()
        print("Successfully inserted")
        cur.close()
        con.close()

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

def generate_qr_code_content(last_name,first_name,designation,email,phone,size):
  qr_code = requests.get(f"https://chart.googleapis.com/chart?cht=qr&chs={size}x{size}&chl={last_name,first_name,designation,email,phone}")
  return qr_code.content


def handle_query(args):
    con = psycopg2.connect(dbname=args.dbname)
    cur = con.cursor()
    query = f"SELECT e.last_name, e.first_name, e.email, e.phone, d.designation_name from employees e INNER JOIN designation d ON e.designation_id = d.designation_id  where e.employee_id = {args.id}"
    cur.execute(query)
    first_name, last_name, email, phone, designation = cur.fetchone()

    print (f"""Name        : {first_name} {last_name}
Designation : {designation}
Email       : {email}
Phone       : {phone}""")
    if (args.vcard):
        vcard = create_vcard(last_name, first_name, designation, email, phone)
        print (f"\n{vcard}")
    con.close()


def add_leaves(args):
    con = psycopg2.connect(dbname=args.dbname)
    cur = con.cursor()
    try:
        leaves_remaining = """
            SELECT d.total_num_of_leaves - COUNT(l.id) AS leaves_remaining 
            FROM employees e 
            LEFT JOIN leaves l ON e.employee_id = l.employee 
            JOIN designation d ON e.designation_id = d.designation_id 
            WHERE e.employee_id = %s 
            GROUP BY e.employee_id, d.total_num_of_leaves
        """
        cur.execute(leaves_remaining, (args.employee_id,))
        leaves_remaining = cur.fetchone()

        if leaves_remaining:
            if leaves_remaining[0] <= 0:
                print("No leaves remaining. Cannot take more leaves.")
            else:
                leave_exists_query = "SELECT id FROM leaves WHERE employee = %s AND date = %s"
                cur.execute(leave_exists_query, (args.employee_id, args.date))
                exists = cur.fetchone()

                if exists:
                    print(f"Employee already taken leave on {args.date}")
                else:
                    insert_leave_query = "INSERT INTO leaves(date, employee, reason) VALUES (%s, %s, %s)"
                    cur.execute(insert_leave_query, (args.date, args.employee_id, args.reason))
                    con.commit()
                    print("Leave details successfully inserted")

    except psycopg2.Error as e:
        con.rollback()
        print(f"Failed to add leave: {e}")

        cur.close()
        con.close()

def get_leave_summary(args):
    con = psycopg2.connect(dbname=args.dbname)
    cur = con.cursor()
    psql= """SELECT e.employee_id, e.first_name, e.last_name, d.designation_name, COUNT(l.id) AS leaves_taken, d.total_num_of_leaves - COUNT(l.id) AS leaves_remaining FROM 
            employees e LEFT JOIN leaves l ON e.employee_id = l.employee JOIN designation d ON e.designation_id = d.designation_id WHERE  e.employee_id = %s 
            GROUP BY e.employee_id, e.first_name, e.last_name, d.designation_name, d.total_num_of_leaves"""
    cur.execute(psql, (args.employee_id,))
    leaves = cur.fetchone()

    if leaves:
        employee_id, first_name, last_name, designation, leaves_taken, leaves_remaining = leaves
        print(f'''Employee ID: {employee_id}
        "Name: {first_name} {last_name}
        "Designation : {designation}
        "Leaves Taken: {leaves_taken}
        "Leaves Remaining: {leaves_remaining}''')
    con.close()

def export_leave_summary(args):
    con = psycopg2.connect(dbname=args.dbname)
    cur = con.cursor()
    try:
        query = """
            SELECT e.employee_id, e.first_name, e.last_name, d.designation_name, 
            COUNT(l.id) AS leaves_taken, d.total_num_of_leaves - COUNT(l.id) AS leaves_remaining 
            FROM employees e 
            LEFT JOIN leaves l ON e.employee_id = l.employee 
            JOIN designation d ON e.designation_id = d.designation_id 
            GROUP BY e.employee_id, e.first_name, e.last_name, d.designation_name, d.total_num_of_leaves"""
        cur.execute(query)
        rows = cur.fetchall()

        directory = args.directory
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, 'leave_summary.csv'), 'w', newline='') as csvfile:
            fieldnames = ['Employee ID', 'First Name', 'Last Name', 'Designation', 'Leaves Taken', 'Leaves Remaining']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in rows:
                employee_id, first_name, last_name, designation, leaves_taken, leaves_remaining = item
                writer.writerow({
                    'Employee ID': employee_id,
                    'First Name': first_name,
                    'Last Name': last_name,
                    'Designation': designation,
                    'Leaves Taken': leaves_taken,
                    'Leaves Remaining': leaves_remaining})

        print(f"Exported leave summary to {os.path.join(directory, 'leave_summary.csv')}")

    except psycopg2.Error as e:
        print(f"Failed to export data: {e}")
        cur.close()
        con.close()



def add_to_designation(args):
    con=psycopg2.connect(dbname=args.dbname)
    cur=con.cursor()
    try:
        psql="insert into designation(designation_name,percentage_of_employees,total_num_of_leaves) values(%s,%s,%s)"
        cur.execute(psql,(args.name,args.percentage,args.leaves))
        con.commit()
        print("Designation details inserted ")
    except:
        con.rollback()
        print("details not inserted ")
    finally:
        cur.close()
        con.close()


def main():
    try:
        args = parse_args()
        init_logger(args.verbose)
        ops = {"initdb" : initialize_db,
               "import" : import_data_to_db,
               "query" : handle_query,
               "leave" : add_leaves,
               "summary":get_leave_summary,
               "designation":add_to_designation,
               "export": export_leave_summary}
        ops[args.op](args)
    except HRException as e:
        logger.error("Program aborted, %s", e)
        sys.exit(-1)


if __name__=="__main__":
    main()




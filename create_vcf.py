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
    
    # initdb
    subparsers = parser.add_subparsers(dest="op")
    parser_initdb = subparsers.add_parser("initdb", help="Initialize creation of database and table")
    
    # import csv
    import_parser = subparsers.add_parser("import", help="Import data from csv file")
    import_parser.add_argument("employees_file", help="List of employees to import")

    #fetch vcard
    query_parser = subparsers.add_parser("query", help="Get information for a single employee")
    query_parser.add_argument("--vcard", action="store_true", default=False, help="Generate vcard for employee")
    query_parser.add_argument("id", help="employee id")
    
    # fetch qr code
    parser_fetch_qr = subparsers.add_parser("qr", help="Generate QR code for an employee using employee ID")
    parser_fetch_qr.add_argument("id", help="Employee ID to generate QR code", type=int)
    parser_fetch_qr.add_argument("-s", "--size", help="Size of QR codes", action='store', type=int, default=500)
    parser_fetch_qr.add_argument("-qr_dir", "--output_directory", help="Output directory for generated QR codes", type=str)

    # add leave
    parser_leave = subparsers.add_parser("leave", help="Add leave to database")
    parser_leave.add_argument("date", type=str, help="Date of leave")
    parser_leave.add_argument("employee_id", type=int, help="Employee id")
    parser_leave.add_argument("reason", type=str, help="Reason of leave")

    #leave_summary
    parser_summary = subparsers.add_parser("summary", help="Leave summary")
    parser_summary.add_argument("employee_id", type=int, help="Employee id")
    
    #leave_summary export
    parser_export = subparsers.add_parser("export", help="Export leave summary")
    parser_export.add_argument("directory", help="Directory_path to export leave summary")

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

def create_connection(dbname):
    conn = psycopg2.connect(dbname=dbname)
    cursor = conn.cursor()
    return conn, cursor

def execute_query(query, dbname, args=None, fetch=False):
    conn = psycopg2.connect(dbname=dbname)
    cursor = conn.cursor()
    try:
        if args:
            cursor.execute(query, args)
        else:
            cursor.execute(query)    
        if fetch:
            result = cursor.fetchall()
        else:
            result = None    
        conn.commit()
        return result
    finally:
        cursor.close()
        conn.close()


def initialize_db(args):
    with open("data/init.sql") as f:
        sql = f.read()
        logger.debug(sql)
    try:
        execute_query(sql, args.dbname)
        logger.info("Initialize Database Successfully")
    except psycopg2.OperationalError as e:
        raise HRException(f"Database '{args.dbname}' doesn't exist")


def truncate_table(args):
    query = "TRUNCATE TABLE employees RESTART IDENTITY CASCADE"
    execute_query(query, args=args)  


def import_data_to_db(args):
    truncate_table(args)
    cur = create_connection()
    with open(args.employees_file) as f:
        reader = csv.reader(f)
        for lname, fname, designation, email, phone in reader:
            logger.debug("Inserting %s", email)
            query = "INSERT INTO employees(last_name, first_name, email, phone, designation_id) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(query, (lname, fname, designation, email, phone))


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


def generate_qr_code(args):
    psql = """
        SELECT e.last_name, e.first_name, e.email, e.phone, d.designation_name FROM employees e 
        INNER JOIN designation d ON e.designation_id = d.designation_id  
        WHERE e.employee_id = %s
    """
    result = execute_query(psql, args.dbname, (args.id,), fetch=True)

    if result:
        first_name, last_name, email, phone, designation = result[0]
        vcard_content = create_vcard(last_name, first_name, designation, email, phone)
        
        qr_code_content = requests.get(f"https://chart.googleapis.com/chart?cht=qr&chs={args.size}x{args.size}&chl={vcard_content}").content
        
        os.makedirs(args.output_directory, exist_ok=True)
        
        file_name = f"{args.id}_vcard_qr.png"
        file_path = os.path.join(args.output_directory, file_name)
        
        with open(file_path, "wb") as qr_file:
            qr_file.write(qr_code_content)

        logger.info(f"QR saved at: {file_path}")
    else:
        logger.error(f"No data found with ID: {args.id}")


def handle_query(args):
    query = """
        SELECT e.last_name, e.first_name, e.email, e.phone, d.designation_name 
        FROM employees e 
        INNER JOIN designation d ON e.designation_id = d.designation_id  
        WHERE e.employee_id = %s
    """
    result = execute_query(query, args.dbname, (args.id,), fetch=True)

    if result:
        first_name, last_name, email, phone, designation = result[0]
        print(f"""Name        : {first_name} {last_name}
        Designation : {designation}
        Email       : {email}
        Phone       : {phone}""")

        if args.vcard:
            vcard = create_vcard(last_name, first_name, designation, email, phone)
            print(f"\n{vcard}")


def add_leaves(args):
    try:
        conn, cur = create_connection(args.dbname)

        leaves_remaining_query = """
            SELECT d.total_num_of_leaves - COUNT(l.id) AS leaves_remaining 
            FROM employees e 
            LEFT JOIN leaves l ON e.employee_id = l.employee 
            JOIN designation d ON e.designation_id = d.designation_id 
            WHERE e.employee_id = %s 
            GROUP BY e.employee_id, d.total_num_of_leaves
        """
        cur.execute(leaves_remaining_query, (args.employee_id,))
        leaves_remaining = cur.fetchone()

        if leaves_remaining:
            if leaves_remaining[0] <= 0:
                logger.warning(f"No leaves remaining. Cannot take more leaves.")
            else:
                leave_exists_query = "SELECT id FROM leaves WHERE employee = %s AND date = %s"
                cur.execute(leave_exists_query, (args.employee_id, args.date))
                exists = cur.fetchone()

                if exists:
                    logger.warning(f"Employee already taken leave on {args.date}")
                else:
                    insert_leave_query = "INSERT INTO leaves(date, employee, reason) VALUES (%s, %s, %s)"
                    cur.execute(insert_leave_query, (args.date, args.employee_id, args.reason))
                    conn.commit()
                    logger.info("Leave details successfully inserted")

    except psycopg2.Error as e:
        logger.error(f"Failed to add leave: {e}")

def get_leave_summary(args):
    try:
        psql_query = """
            SELECT e.employee_id, e.first_name, e.last_name, d.designation_name, 
            COUNT(l.id) AS leaves_taken, d.total_num_of_leaves - COUNT(l.id) AS leaves_remaining 
            FROM employees e 
            LEFT JOIN leaves l ON e.employee_id = l.employee 
            JOIN designation d ON e.designation_id = d.designation_id 
            WHERE  e.employee_id = %s 
            GROUP BY e.employee_id, e.first_name, e.last_name, d.designation_name, d.total_num_of_leaves
        """
        leaves = execute_query(psql_query, args.dbname, (args.employee_id,), fetch=True)

        if leaves:
            employee_id, first_name, last_name, designation, leaves_taken, leaves_remaining = leaves[0]
            print(f'''Employee ID: {employee_id}
            Name: {first_name} {last_name}
            Designation : {designation}
            Leaves Taken: {leaves_taken}
            Leaves Remaining: {leaves_remaining}''')

    except psycopg2.Error as e:
        logger.error(f"Failed to retrieve leave summary: {e}")


def export_leave_summary(args):
    try:
        query = """
            SELECT e.employee_id, e.first_name, e.last_name, d.designation_name, 
            COUNT(l.id) AS leaves_taken, d.total_num_of_leaves - COUNT(l.id) AS leaves_remaining 
            FROM employees e 
            LEFT JOIN leaves l ON e.employee_id = l.employee 
            JOIN designation d ON e.designation_id = d.designation_id 
            GROUP BY e.employee_id, e.first_name, e.last_name, d.designation_name, d.total_num_of_leaves"""
        rows = execute_query(query, args.dbname, fetch=True)

        directory = args.directory
        os.makedirs(directory, exist_ok=True)

        with open(os.path.join(directory, 'leave_summary.csv'), 'w', newline='') as csvfile:
            fieldnames = ['First Name', 'Last Name', 'Designation', 'Leaves Taken', 'Leaves Remaining']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

            for item in rows:
                employee_id, first_name, last_name, designation, leaves_taken, leaves_remaining = item
                writer.writerow({
                    'First Name': first_name,
                    'Last Name': last_name,
                    'Designation': designation,
                    'Leaves Taken': leaves_taken,
                    'Leaves Remaining': leaves_remaining})

        logger.info(f"Exported leave summary to {os.path.join(directory, 'leave_summary.csv')}")

    except psycopg2.Error as e:
        logger.error(f"Failed to export data: {e}")



def main():
    try:
        args = parse_args()
        init_logger(args.verbose)
        ops = {"initdb" : initialize_db,
               "import" : import_data_to_db,
               "query" : handle_query,
               "qr": generate_qr_code,
               "leave" : add_leaves,
               "summary":get_leave_summary,
               "export": export_leave_summary
               }
        ops[args.op](args)
    except HRException as e:
        logger.error("Program aborted, %s", e)
        sys.exit(-1)


if __name__=="__main__":
    main()


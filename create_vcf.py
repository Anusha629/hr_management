import argparse
import logging
import psycopg2
import sys
import csv

class HRException(Exception): pass

logger = False 


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

    query_parser = subparsers.add_parser("query", help="Get information for a single employee")
    query_parser.add_argument("--vcard", action="store_true", default=False, help="Generate vcard for employee")
    query_parser.add_argument("id", help="employee id")

    parser.add_argument("-n", "--number", help="Number of records to generate", action="store", type=int, default=10)
    parser.add_argument("-v", "--verbose", help="Print detailed logging", action="store_true", default=False)
    parser.add_argument("-q", "--add_qr", help="Add QR codes", action="store_true", default=False)
    parser.add_argument("-s", "--qr_size", help="Size of QR code", type=int, default=500)
    parser.add_argument("-a", "--address", help="Employee address", type=str, default="100 Flat Grape Dr.;Fresno;CA;95555;United States of America")

    args = parser.parse_args()
    return args 


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
            query = "INSERT INTO employees(last_name, first_name, designation, email, phone) VALUES (%s, %s, %s, %s, %s)"
            cur.execute(query, (lname, fname, designation, email, phone))
        con.commit()
        print("Successfully inserted")
        cur.close()
        con.close()


def handle_query(args):
    con = psycopg2.connect(dbname=args.dbname)
    cur = con.cursor()
    query = f"SELECT last_name, first_name, designation, email, phone from employees where employee_id = {args.id}"
    cur.execute(query)
    first_name, last_name, designation, email, phone = cur.fetchone()

    print (f"""Name        : {first_name} {last_name}
Designation : {designation}
Email       : {email}
Phone       : {phone}""")
    if (args.vcard):
        vcard = create_vcard(last_name, first_name, designation, email, phone)
        print (f"\n{vcard}")
    con.close()




def main():
    try:
        args = parse_args()
        init_logger(args.verbose)
        ops = {"initdb" : initialize_db,
               "import" : import_data_to_db,
               "query" : handle_query}
        ops[args.op](args)
    except HRException as e:
        logger.error("Program aborted, %s", e)
        sys.exit(-1)


if __name__=="__main__":
    main()




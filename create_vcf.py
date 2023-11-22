import argparse
import logging
import psycopg2
import sys

class HRException(Exception): pass

logger = False 


def create_vcard(file, address):
    last_name, first_name, title, email, phone = file
    content = f"""BEGIN:VCARD
    VERSION:2.1
    N:{last_name};{first_name}
    FN:{first_name} {last_name}
    ORG:Authors, Inc.
    TITLE:{title}
    TEL;WORK;VOICE:{phone}
    ADR;WORK:;;{address}
    EMAIL;PREF;INTERNET:{email}
    REV:20150922T195243Z
    END:VCARD
    """
    return content


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
        prog="sir.py", description="Generate employee database"
    )

    # Subcommand initdb
    subparsers = parser.add_subparsers(dest="op")
    parser_initdb = subparsers.add_parser("initdb", help="Initialize creation of database and table")

    parser_initdb.add_argument("--dbname", help="Adding user name of database", action="store", type=str, default='emp_db')
    parser_initdb.add_argument("--userdb", help="Adding database name", action="store", type=str, default='anusha')


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
    except psycopg2.OperationalError as e:
        raise HRException(f"Database '{args.dbname}' doesn't exist")


def main():
    try:
        args = parse_args()
        init_logger(args.verbose)
        ops = {"initdb" : initialize_db
               }        
        ops[args.op](args)
    except HRException as e:
        logger.error("Program aborted, %s", e)
        sys.exit(-1)
if __name__=="__main__":
    main()




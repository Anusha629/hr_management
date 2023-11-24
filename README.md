# HR Management

This Python script converts data from a database into VCards. Each row in database corresponds to an individual's contact information, and the script creates a VCard for each person.

    
   Data base contains with the following columns: Last Name, First Name, Designation, Email, and Phone

## Usage

The generated VCards include the following information:

    Full Name
    Organization and Title
    Work Phone
    Work Address
    Email Address


Run:

   python3 create_vcf.py initdb  - (initialize database )

   python3 create_vcf.py import names.csv - (import a csv file )

   python3 create_vcf.py query 11   - (get a single details for an employee)

   python3 create_vcf.py query 5 --vcard - (get a single vcard for an employee)







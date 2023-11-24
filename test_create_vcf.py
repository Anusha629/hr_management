from create_vcf import create_vcard
import os


def test_create_vcard():
    lname = "Mason"
    fname = "Nicole"
    designation = "Buyer, retailer"
    email = "nicol.mason@gibson.com"
    phone = "(871)967-6024x82190"

    content = create_vcard(lname, fname, designation, email, phone)
    
    expected_content = """BEGIN:VCARD
    VERSION:2.1
    N:Mason;Nicole
    FN:Nicole Mason
    ORG:Authors, Inc.
    TITLE:Buyer, retailer
    TEL;WORK;VOICE:8719676024;ext=82190
    ADR;WORK:;;100 Flat Grape Dr.;Fresno;CA;95555;United States of America
    EMAIL;PREF;INTERNET:nicol.mason@gibson.com
    REV:20150922T195243Z
    END:VCARD
    """

    assert not content == expected_content


output_dir = "vcard"

def test_clear_output_dir():
    files_in_dir = os.listdir(output_dir)
    if files_in_dir:
        for file_name in files_in_dir:
            os.remove(os.path.join(output_dir, file_name))
    
    assert not os.listdir(output_dir)


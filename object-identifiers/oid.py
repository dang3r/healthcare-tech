import json
import re
from typing import NamedTuple

class OID(NamedTuple):
    oid: str
    organization: str
    contact: str
    email: str
    description: str = ""

def iana_enterprise_db(fname: str = "enterprise-numbers.txt") -> dict:
    """
    File comes from https://www.iana.org/assignments/enterprise-numbers/enterprise-numbers

    Entries are in the format:
    \d+
      <org>
        <contact>
          <email>
    """
    with open(fname, "r") as f:
        text = f.read()
    db = dict()
    for match in re.finditer("^(\d+)\n\s+(.*)[\n]\s+(.*)[\n]\s+(.*)", text, re.MULTILINE):
        oid  = "1.3.6.1.4.1." + match.groups()[0]
        org, contact, email = match.groups()[1:]
        email = email.replace("&", "@").lower()
        result = OID(oid, org, contact, email)._asdict()
        db[oid] = result
    return db

if  __name__ == "__main__":
    db = iana_enterprise_db("enterprise-numbers.txt")
    open("db.json", "w").write(json.dumps(db))
    oid = input("What OID do you want information for? ").strip()
    print(db.get(oid))


"""Process club records."""
import csv
import ntpath
import os
import re
from pathlib import Path

from scm_helper.config import C_RECORDS, CONFIG_DIR, FILE_READ, RECORDS_DIR, get_config
from scm_helper.files import Files
from scm_helper.notify import notify

R_EVENT = "Event"
R_SWIMMER1 = "Swimmer 1"
R_SWIMMER2 = "Swimmer 2"
R_SWIMMER3 = "Swimmer 3"
R_SWIMMER4 = "Swimmer 4"
R_TIME = "Time"
R_LOCATION = "Location"
R_DATE = "Date"

RELAY_STROKES = {
    "Free": "Freestyle",
    "Medley": "Medley",
}

# A list would do, but this allows a lookup
RELAY_DISTANCE = {"200": 200, "400": 400, "800": 800}
PRINT_DISTANCE = {"200": "4 x 50", "400": "4 x 100", "800": "4 x 200"}
RELAY_AGES = {
    "72": "72+",
    "100": "100-119",
    "120": "120-159",
    "160": "160-199",
    "200": "200-239",
    "240": "240-279",
    "280": "280+",
}
RELAY_GENDER = {"M": "Male", "F": "Female", "Mixed": "Mixed"}

R_COURSE = {"25": "SC", "50": "LC"}

TAG_INNER_EVEN = "name=record-inner-even"
TAG_INNER_ODD = "name=record-inner-odd"


class Records:
    """Read and process record files."""

    def __init__(self):
        """Initialise."""
        self.scm = None
        self.records = []

    def read_baselines(self, scm):
        """Read each file."""
        self.scm = scm

        home = str(Path.home())
        mydir = os.path.join(home, CONFIG_DIR, RECORDS_DIR)

        cfg = get_config(scm, C_RECORDS)
        if cfg:
            for record in cfg:
                data = Record()
                filename = os.path.join(mydir, record)
                res = data.read_baseline(filename, scm)
                if res:
                    self.records.append(data)
                else:
                    return False
            return True
        return False

    def create_html(self):
        """Create HTML files for records."""
        for record in self.records:
            print(record.create_html())

    def delete(self):
        """Delete."""
        for record in self.records:
            del record


class Record:
    """Manage a records file."""

    def __init__(self):
        """Initilaise Records handling."""
        self._filename = None
        self.scm = None
        self.csv = []
        self.records = {}

    def read_baseline(self, filename, scm):
        """Read Facebook file."""
        self._filename = filename
        self.scm = scm

        shortfile = ntpath.basename(filename)

        try:
            count = 0
            with open(filename, newline="") as csvfile:
                dialect = csv.Sniffer().sniff(csvfile.read(1024))
                csvfile.seek(0)
                csv_reader = csv.DictReader(csvfile, dialect=dialect)

                for row in csv_reader:
                    count += 1
                    if count == 0:
                        continue
                    self.csv.append(row)
                    # TODO  split and tidy!
                    event = row[R_EVENT].split()
                    if RELAY_GENDER.get(event[0], None) is None:
                        notify(f"Line {count}: unknown gender '{event[0]}'\n")
                    if RELAY_AGES.get(event[1], None) is None:
                        notify(f"Line {count}: unknown age '{event[1]}'\n")

                    dist = RELAY_DISTANCE.get(event[2], None)
                    if dist is None:
                        mdist = RELAY_DISTANCE.get(event[2].rstrip("m"), None)
                        if mdist is None:
                            notify(f"Line {count}: unknown distance '{event[2]}'\n")
                        else:
                            event[2] = str(mdist)

                    if RELAY_STROKES.get(event[3], None) is None:
                        notify(f"Line {count}: unknown event '{event[3]}'\n")
                    if R_COURSE.get(event[4], None) is None:
                        notify(f"Line {count}: unknown course '{event[4]}'\n")

                    self.records[" ".join(event)] = row

            notify(f"Read {filename}...\n")
            return True

        except EnvironmentError:
            notify(f"Cannot open records file: {filename}\n")
            return False

        except csv.Error as error:
            notify(f"Error in records file: {filename}\n{error}\n")
            return False

        notify("Unknown error\n")
        return False

    def create_html(self):
        """create a records file."""
        # Get prefix
        header = os.path.splitext(self._filename)[0]
        header += ".header"

        with open(header, FILE_READ) as file:
            prefix = file.read()

        res = prefix

        for gender in RELAY_GENDER:

            o_gender = ""
            for stroke in RELAY_STROKES:

                o_dist = ""
                for dist in RELAY_DISTANCE:

                    o_age = ""
                    tag = TAG_INNER_ODD
                    for age in RELAY_AGES:
                        opt = ""

                        opt_sc = self.print_record(stroke, dist, age, "25", gender)
                        opt_lc = self.print_record(stroke, dist, age, "50", gender)

                        if opt_sc or opt_lc:
                            opt += "                <div class=divTable><div class=divTableBody>\n"
                            if opt_sc:
                                opt += opt_sc
                            if opt_lc:
                                opt += opt_lc
                            opt += "                </div></div>\n"
                        else:
                            opt += "                -\n"

                        if tag == TAG_INNER_EVEN:
                            tag = TAG_INNER_ODD
                        else:
                            tag = TAG_INNER_EVEN
                        o_age += f"""
            <div class=divTableRow {tag}>
                <div class=divTableCell>
                Age: {RELAY_AGES[age]}:
                </div>
                <div class=divTableCell>
{opt}
                </div>
            </div>
            """

                    if o_age:
                        o_dist += f"""
        <h3>{PRINT_DISTANCE[dist]}:</h3>
        <div class=divTable>
        <div class=divTableBody>
{o_age}
        </div>
        </div>
        """

                if o_dist:
                    o_gender += f"""
    <div class="divTable" name=\"record-{stroke.lower()}\">
{o_dist}
    </div>
    """

            if res:
                pgen = RELAY_GENDER[gender].lower()
                res += f"""
<div name=\"record-{pgen}\">
{o_gender}
</div>
"""

        return res

    def print_record(self, stroke, dist, age, course, gender):
        """Print a record."""
        lookup = f"{gender} {age} {dist} {stroke} {course}"
        if lookup in self.records:
            record = self.records[lookup]
            xtime = record[R_TIME]
            xdate = record[R_DATE]
            loc = record[R_LOCATION]
            swimmer1 = record[R_SWIMMER1]
            swimmer2 = record[R_SWIMMER2]
            swimmer3 = record[R_SWIMMER3]
            swimmer4 = record[R_SWIMMER4]
            if xtime:
                opt = "\n                   <div class=divTableRow>\n"
                opt += f"                   <div class=divTableCell>{xtime} ({R_COURSE[course]})</div>\n"
                opt += f"                   <div class=divTableCell>{xdate}</div>\n"
                opt += f"                   <div class=divTable><div class=divTableBody><div class=divTableRow>\n"
                opt += f"                      <div class=divTableCell>{loc}</div>\n"
                opt += f"                   </div><div class=divTableRow>\n"
                opt += f"                      <div class=divTableCell>{swimmer1}, {swimmer2}, {swimmer3}, {swimmer4}</div>\n"
                opt += "                    </div></div></div></div>\n"
                return opt
        return ""

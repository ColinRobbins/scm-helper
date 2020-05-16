"""Process club records."""
import csv
import datetime
import ntpath
import os
import re
from pathlib import Path

from scm_helper.config import (
    C_BASELINE,
    C_RECORDS,
    C_SWIMTIMES,
    CONFIG_DIR,
    FILE_READ,
    RECORDS_DIR,
    SCM_CSV_DATE_FORMAT,
    get_config,
)
from scm_helper.files import Files
from scm_helper.notify import notify

STROKES = {
    "Free": "Freestyle",
    "Back": "Backstroke",
    "Breast": "Breaststroke",
    "Fly": "Butterfly",
    "Medley": "Individual Medley",
}

# A list would do, but this allows a lookup
DISTANCE = {
    "50m": 50,
    "100m": 100,
    "200m": 200,
    "400m": 400,
    "800m": 800,
    "1500m": 1500,
}

AGES = {
    "8-9": "U10",
    "10-11": "U12",
    "12-13": "U14",
    "14-15": "U16",
    "16-17": "U18",
    "18-24": "18-24",
    "25-29": "25-29",
    "30-34": "30-34",
    "35-39": "35-39",
    "40-44": "40-44",
    "45-49": "45-49",
    "50-54": "50-54",
    "55-59": "55-59",
    "60-64": "60-64",
    "65-60": "65-69",
    "70-74": "70-74",
    "75-79": "75-79",
    "80-84": "80-84",
}

GENDER = {"M": "Male", "F": "Female"}

COURSE = {"25": "SC", "50": "LC"}

TAG_INNER_EVEN = "name=record-inner-even"
TAG_INNER_ODD = "name=record-inner-odd"

S_EVENT = "event"
S_ASA = "asa"
S_NAME = "name"
S_TIME = "time"
S_TIMESTR = "timestr"
S_LOCATION = "location"
S_DATE = "date"


class Records:
    """Read and process record files."""

    def __init__(self):
        """Initialise."""
        self.scm = None
        self.records = None

    def read_baseline(self, scm):
        """Read baseline."""
        self.scm = scm

        home = str(Path.home())
        mydir = os.path.join(home, CONFIG_DIR, RECORDS_DIR)

        cfg = get_config(scm, C_RECORDS, C_BASELINE)
        if cfg:
            self.records = Record()
            filename = os.path.join(mydir, cfg)
            res = self.records.read_baseline(filename, scm)
            return res

        return False

    def read_newtimes(self):
        """Read swimtimes."""

        home = str(Path.home())
        mydir = os.path.join(home, CONFIG_DIR, RECORDS_DIR)

        cfg = get_config(self.scm, C_RECORDS, C_SWIMTIMES)
        if cfg:
            times = SwimTimes(self.records)
            filename = os.path.join(mydir, cfg)
            res = times.merge_times(filename, self.scm)
            return res
        return False

    def create_html(self):
        """Create HTML files for records."""
        print(self.records.create_html())

    def delete(self):
        """Delete."""
        del record


class SwimTimes:
    """Read SwimTimes, and merge into Records."""

    def __init__(self, records):
        """Initilaise Records handling."""
        self._filename = None
        self.scm = None
        self.csv = []
        self.records = records

    def merge_times(self, filename, scm):
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
                    if count == 1:
                        continue

                    self.process_row(row)

            notify(f"Read {filename}...\n")
            return True

        except EnvironmentError:
            notify(f"Cannot open swim time file: {filename}\n")
            return False

        except csv.Error as error:
            notify(f"Error in swim time file: {filename}\n{error}\n")
            return False

        notify("Unknown error\n")
        return False

    def process_row(self, row):
        """Process and merge a row into records."""

        asa = row["SE Number"]
        swimmer = row["Swimmer"]
        xdate = row["Date"]
        pool = row["Pool Size"]
        dist = row["Swim Distance"]
        stroke = row["Stroke"]
        timestr = row["Time"]
        relay = row["Relay"]
        location = row["Location"]

        if "DQ" in timestr:
            return

        if "NT" in timestr:
            return

        if dist == "25m":
            return

        if relay == "Yes":
            return

        if (pool != "50") and (pool != "25"):
            return

        if location:
            pass
        else:
            Location = "Unknown"

        if dist not in DISTANCE:
            print("HERE 99")
            return

        if stroke not in STROKES:
            print("HERE 9c9")
            return

        if asa not in self.scm.members.by_asa:
            # print (f"NO ASA: {asa}, {swimmer}, {dist}, {stroke}")
            return

        swimtime = convert_time(timestr)

        member = self.scm.members.by_asa[asa]

        yob = member.dob.year

        swimdate = datetime.datetime.strptime(xdate, SCM_CSV_DATE_FORMAT)
        swimyear = swimdate.year
        swimage = swimyear - yob

        if member.date_joined and (swimdate < member.date_joined):
            return

        if swimage < 19:
            start_age = int(swimage / 2) * 2
            end_age = start_age + 1
        elif swimage == 19:
            start_age = 19
            end_age = 24
        else:
            start_age = int(swimage / 5) * 5
            # round it
            if start_age == 20:
                start_age = 19
            end_age = start_age + 4

        location = re.sub("19\d\d", "", location)  # get rid of date
        location = re.sub("20\d\d", "", location)
        location = re.sub("\(25m\)", "", location)
        location = re.sub("25m", "", location)
        location = re.sub("50m", "", location)

        agegroup = f"{start_age}-{end_age}"
        gender = member.gender

        event = f"{gender} {agegroup} {dist} {stroke} {pool}"

        swim = {
            S_EVENT: event,
            S_ASA: asa,
            S_NAME: member.name,
            S_TIMESTR: timestr,
            S_TIME: convert_time(timestr),
            S_LOCATION: location,
            S_DATE: xdate,
        }

        self.records.check_swim(swim)

        return


# TODO.
# CHange Records below for members


class Record:
    """Manage a records file."""

    def __init__(self):
        """Initilaise Records handling."""
        self._filename = None
        self.scm = None
        self.csv = []
        self.records = {}

    def check_swim(self, swim):
        """Check a swim time to see if it as a record."""
        if swim[S_EVENT] in self.records:
            event = self.records[swim[S_EVENT]]
            if swim[S_TIME] >= event[S_TIME]:
                return

        self.records[swim["event"]] = swim

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
                    if count == 1:
                        continue
                    self.csv.append(row)

                    event = row["event"]
                    row["ctime"] = convert_time(row["time"])
                    self.records[event] = row

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

        for gender in GENDER:

            o_gender = ""
            for stroke in STROKES:

                o_dist = ""
                for dist in DISTANCE:

                    o_age = ""
                    tag = TAG_INNER_ODD
                    for age in AGES:
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
                Age: {AGES[age]}:
                </div>
                <div class=divTableCell>
{opt}
                </div>
            </div>
            """

                    if o_age:
                        o_dist += f"""
        <h3>{dist}:</h3>
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
                pgen = GENDER[gender].lower()
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
            xtime = record[S_TIMESTR]
            xdate = record[S_DATE]
            name = record[S_NAME]
            loc = record[S_LOCATION]
            if xtime:
                opt = "\n                   <div class=divTableRow>\n"
                opt += f"                   <div class=divTableCell>{xtime} ({COURSE[course]})</div>\n"
                opt += f"                   <div class=divTableCell>{xdate}</div>\n"
                opt += f"                   <div class=divTableCell>{name}</div>\n"
                opt += f"                   <div class=divTableCell>{loc}</div>\n"
                opt += "                    </div></div>\n"
                return opt
        return ""


def convert_time(xtime):
    """Convert a time to a number of seconds."""

    hms = xtime.split(":")
    res = float(hms[0]) * 60 + float(hms[1])
    return res

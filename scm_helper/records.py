"""Process club records."""
import csv
import datetime
import os
import re
from pathlib import Path

from scm_helper.config import (
    C_RECORDS,
    C_RELAY,
    CONFIG_DIR,
    FILE_READ,
    RECORDS_DIR,
    SCM_CSV_DATE_FORMAT,
    get_config,
)
from scm_helper.issue import debug
from scm_helper.notify import notify

STROKES = {
    "Free": "Freestyle",
    "Back": "Backstroke",
    "Breast": "Breaststroke",
    "Fly": "Butterfly",
    "Medley": "Individual Medley",
}


DISTANCE = [
    "50m",
    "100m",
    "200m",
    "400m",
    "800m",
    "1500m",
]

STROKE_DISTANCE = {
    "Free": ["50m", "100m", "200m", "400m", "800m", "1500m"],
    "Back": ["50m", "100m", "200m"],
    "Breast": ["50m", "100m", "200m"],
    "Fly": ["50m", "100m", "200m"],
    "Medley": ["100m", "200m", "400m"],
}

AGES = {
    "6-7": 0,
    "8-9": 0,
    "10-11": 0,
    "12-13": 0,
    "14-15": 0,
    "16-17": 0,
    "18-24": 0,
    "25-29": 0,
    "30-34": 0,
    "35-39": 0,
    "40-44": 0,
    "45-49": 0,
    "50-54": 0,
    "55-59": 0,
    "60-64": 0,
    "65-69": 0,
    "70-74": 0,
    "75-79": 0,
    "80-84": 0,
    "85-89": 0,
    "90-94": 0,
    "95-99": 0,
}

GENDER = {"M": "Male", "F": "Female"}

COURSE = {"25": "SC", "50": "LC"}

R_EVENT = "event"
R_SWIMMER1 = "swimmer 1"
R_SWIMMER2 = "swimmer 2"
R_SWIMMER3 = "swimmer 3"
R_SWIMMER4 = "swimmer 4"
R_TIME = "time"
R_LOCATION = "location"
R_DATE = "date"

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

TAG_INNER_EVEN = "name=record-inner-even"
TAG_INNER_ODD = "name=record-inner-odd"

S_EVENT = "event"
S_ASA = "asa"
S_NAME = "name"
S_TIMESTR = "time"
S_FTIME = "ftime"
S_LOCATION = "location"
S_DATE = "date"

F_BASELINE = "records.csv"
F_RECORDS = "records.html"
F_RELAY_BASELINE = "relay_records.csv"
F_RELAY_RECORDS = "relay_records.html"

INNER_WRAP = """
<div class=divTableRow XX_TAG_XX>
<div class=divTableCell>
Age: XX_AGE_XX:
</div>
<div class=divTableCell>
XX_OPT_XX
</div>
</div>
"""

AGE_WRAP = """
<h3>XX_DIST_XX:</h3>
<div class=divTable>
<div class=divTableBody>
XX_AGE_XX
</div>
</div>
"""

DIST_WRAP = """
<div class="divTable" name=\"record-XX_STROKE_XX\">
XX_DIST_XX
</div>
"""

GENDER_WRAP = """
<div name=\"record-XX_GENDER_XX\">
XX_O_GENDER_XX
</div>
"""

WRAP_TABLE_OPEN = " <div class=divTable><div class=divTableBody>\n"
WRAP_TABLE_CLOSE = " </div></div>\n"


class Records:
    """Read and process record files."""

    def __init__(self):
        """Initialise."""
        self.scm = None
        self.records = None
        self.relay = None

    def read_baseline(self, scm):
        """Read baseline."""
        self.scm = scm

        home = str(Path.home())
        mydir = os.path.join(home, CONFIG_DIR, RECORDS_DIR)

        self.records = Record()
        filename = os.path.join(mydir, F_BASELINE)
        res = self.records.read_baseline(filename, scm)

        if res and get_config(self.scm, C_RECORDS, C_RELAY):
            self.relay = RelayRecord()
            filename = os.path.join(mydir, F_RELAY_BASELINE)
            res = self.relay.read_baseline(filename, scm)

        return res

    def read_newtimes(self, filename):
        """Read swimtimes."""

        times = SwimTimes(self.records)
        res = times.merge_times(filename, self.scm)
        del times
        return res

    def create_html(self):
        """Create HTML files for records."""

        home = str(Path.home())
        mydir = os.path.join(home, CONFIG_DIR, RECORDS_DIR)

        res = self.records.create_html(GENDER, STROKES, AGES, False)
        filename = os.path.join(mydir, F_RECORDS)
        with open(filename, "w") as htmlfile:
            htmlfile.write(res)
        notify(f"Created {filename}...\n")

        if self.relay:
            res = self.relay.create_html(RELAY_GENDER, RELAY_STROKES, RELAY_AGES, True)
            filename = os.path.join(mydir, F_RELAY_RECORDS)
            with open(filename, "w") as htmlfile:
                htmlfile.write(res)
            notify(f"Created {filename}...\n")

    def delete(self):
        """Delete."""
        del self.records
        if self.relay:
            del self.relay


class SwimTimes:
    """Read SwimTimes, and merge into Records."""

    def __init__(self, records):
        """Initilaise Records handling."""
        self._filename = None
        self.scm = None
        self.records = records

    def merge_times(self, filename, scm):
        """Read Facebook file."""
        self._filename = filename
        self.scm = scm

        notify(f"Reading {filename}...\n")

        try:
            count = 0
            with open(filename, newline="") as csvfile:
                csv_reader = csv.DictReader(csvfile, dialect="excel")

                for row in csv_reader:
                    count += 1
                    if count == 1:
                        continue

                    if (int(count / 1000)) == (count / 1000):
                        notify(f"{count} ")

                    if (int(count / 10000)) == (count / 10000):
                        notify("\n")

                    self.process_row(row, count)

            notify(f"\nRead {filename}...\n")
            return True

        except EnvironmentError:
            notify(f"Cannot open swim time file: {filename}\n")
            return False

        except csv.Error as error:
            notify(f"Error in swim time file: {filename}\n{error}\n")
            return False

        notify("Unknown error\n")
        return False

    def process_row(self, row, count):
        """Process and merge a row into records."""

        # pylint: disable=too-many-locals
        # pylint: disable=too-many-return-statements
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

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

        if pool not in ("50", "25"):
            return

        if location:
            pass
        else:
            location = "Unknown"

        if dist not in DISTANCE:
            debug(f"Line {count}: Unknown distance {dist}", 1)
            return

        if stroke not in STROKES:
            debug(f"Line {count}: Unknown stroke {stroke}", 1)
            return

        if asa not in self.scm.members.by_asa:
            debug(f"Line {count}: No SE Number {swimmer}", 2)
            return

        member = self.scm.members.by_asa[asa]

        yob = member.dob.year

        swimdate = datetime.datetime.strptime(xdate, SCM_CSV_DATE_FORMAT)
        swimyear = swimdate.year
        swimage = swimyear - yob

        if member.date_joined and (swimdate < member.date_joined):
            debug(f"Line {count}: Ignored, not a member at time of swim", 2)
            return

        if swimage < 18:
            start_age = int(swimage / 2) * 2
            end_age = start_age + 1
        elif swimage in (18, 19):
            start_age = 18
            end_age = 24
        else:
            start_age = int(swimage / 5) * 5
            # round it
            if start_age == 20:
                start_age = 18
                end_age = 24
            else:
                end_age = start_age + 4

        agegroup = f"{start_age}-{end_age}"
        AGES[agegroup] += 1

        gender = member.gender

        event = f"{gender} {agegroup} {dist} {stroke} {pool}"

        swim = {
            S_EVENT: event,
            S_ASA: asa,
            S_NAME: member.name,
            S_TIMESTR: timestr,
            S_FTIME: convert_time(timestr),
            S_LOCATION: location,
            S_DATE: xdate,
        }

        self.records.check_swim(swim)

        return


class Record:
    """Manage a records file."""

    def __init__(self):
        """Initilaise Records handling."""
        self._filename = None
        self.scm = None
        self.records = {}
        self.swimmers = {}

        self.worldrecord = 0
        self.europeanrecord = 0
        self.britishrecord = 0

    def check_swim(self, swim):
        """Check a swim time to see if it as a record."""
        if swim[S_EVENT] in self.records:
            event = self.records[swim[S_EVENT]]
            if swim[S_FTIME] >= event[S_FTIME]:
                return

        self.records[swim[R_EVENT]] = swim

    def check_row(self, row, count):
        """Check a row from the records file."""
        event = row[R_EVENT]
        test = event.split()

        if GENDER.get(test[0], None) is None:
            notify(f"Line {count}: unknown gender '{test[0]}'\n")
            return

        if AGES.get(test[1], None) is None:
            notify(f"Line {count}: unknown age '{test[1]}'\n")
            return

        if test[2] not in DISTANCE:
            notify(f"Line {count}: unknown distance '{test[2]}'\n")
            return

        if STROKES.get(test[3], None) is None:
            notify(f"Line {count}: unknown event '{test[3]}'\n")
            return

        if COURSE.get(test[4], None) is None:
            notify(f"Line {count}: unknown course '{test[4]}'\n")
            return

        if event in self.records:
            notify(f"Line {count}: duplicate '{event}'\n")
            return

        AGES[test[1]] += 1
        row[S_FTIME] = convert_time(row[S_TIMESTR])
        self.records[event] = row

    def read_baseline(self, filename, scm):
        """Read Facebook file."""
        self._filename = filename
        self.scm = scm

        try:
            count = 0
            with open(filename, newline="") as csvfile:
                csv_reader = csv.DictReader(csvfile)

                for row in csv_reader:
                    if count == 0:
                        count = 1
                        continue
                    count += 1
                    self.check_row(row, count)

            notify(f"Read {filename} ({count})...\n")
            return True

        except EnvironmentError:
            notify(f"Cannot open records file: {filename}\n")
            return False

        except csv.Error as error:
            notify(f"Error in records file: {filename}\n{error}\n")
            return False

        notify("Unknown error\n")
        return False

    def create_html(self, arg_gender, arg_strokes, arg_ages, arg_relay):
        """create a records file."""
        # Get prefix

        # pylint: disable=too-many-locals
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        header = os.path.splitext(self._filename)[0]
        header += "_header.txt"

        with open(header, FILE_READ) as file:
            prefix = file.read()

        res = prefix

        for gender in arg_gender:
            o_gender = ""
            for stroke in arg_strokes:
                o_dist = ""

                if arg_relay:
                    loopdist = RELAY_DISTANCE
                else:
                    loopdist = STROKE_DISTANCE[stroke]

                for dist in loopdist:
                    o_age = ""
                    tag = TAG_INNER_ODD
                    for age in arg_ages:

                        if (arg_relay is False) and (arg_ages[age] == 0):
                            continue

                        opt = ""
                        opt_sc = self.print_record(stroke, dist, age, "25", gender)
                        opt_lc = self.print_record(stroke, dist, age, "50", gender)

                        if opt_sc or opt_lc:
                            if arg_relay:
                                opt += WRAP_TABLE_OPEN
                            if opt_sc:
                                opt += opt_sc
                            if opt_lc:
                                opt += opt_lc
                            if arg_relay:
                                opt += WRAP_TABLE_CLOSE
                        else:
                            opt += " -\n"

                        if tag == TAG_INNER_EVEN:
                            tag = TAG_INNER_ODD
                        else:
                            tag = TAG_INNER_EVEN

                        html = INNER_WRAP
                        html = re.sub("XX_TAG_XX", tag, html)
                        if arg_relay:
                            html = re.sub("XX_AGE_XX", RELAY_AGES[age], html)
                        else:
                            html = re.sub("XX_AGE_XX", age, html)
                        html = re.sub("XX_OPT_XX", opt, html)
                        o_age += html

                    if o_age:
                        html = AGE_WRAP
                        if arg_relay:
                            html = re.sub("XX_DIST_XX", PRINT_DISTANCE[dist], html)
                        else:
                            html = re.sub("XX_DIST_XX", dist, html)
                        html = re.sub("XX_AGE_XX", o_age, html)
                        o_dist += html

                if o_dist:
                    html = DIST_WRAP
                    html = re.sub("XX_DIST_XX", o_dist, html)
                    html = re.sub("XX_STROKE_XX", stroke.lower(), html)
                    o_gender += html

            if res:
                pgen = arg_gender[gender].lower()

                html = GENDER_WRAP
                html = re.sub("XX_GENDER_XX", pgen, html)
                html = re.sub("XX_O_GENDER_XX", o_gender, html)
                res += html

        res = self.print_extra(res)
        return res

    def print_extra(self, res):
        """Some extra printing..."""
        num = 0
        top10 = "<p>Top 10 record holders:</p><ul>"
        for holder in sorted(self.swimmers.items(), key=lambda x: x[1], reverse=True):
            top10 += f"<li>{holder[0]}: {holder[1]}</li>"
            num += 1
            if num > 10:
                break
        top10 += "</ul>"

        tally = "<ul>"
        if self.worldrecord > 0:
            tally += f"<li>World Records: {self.worldrecord}</li>\n"
        if self.europeanrecord > 0:
            tally += f"<li>European Records: {self.europeanrecord}</li>\n"
        if self.britishrecord > 0:
            tally += f"<li>British Records: {self.britishrecord}</li>\n"
        tally += "</ul>"

        res = res.replace("RECORDHOLDERS", top10)
        res = res.replace("RECORDTALLY", tally)
        return res

    def print_record(self, stroke, dist, age, course, gender):
        """Print a record."""

        # pylint: disable=too-many-arguments

        lookup = f"{gender} {age} {dist} {stroke} {course}"

        if lookup in self.records:
            record = self.records[lookup]
            xtime = record[S_TIMESTR]
            xdate = record[S_DATE]
            name = record[S_NAME]
            location = record[S_LOCATION]

            if name in self.swimmers:
                self.swimmers[name] += 1
            else:
                self.swimmers[name] = 1

            if re.search("world record", location, re.IGNORECASE):
                self.worldrecord += 1

            if re.search("european record", location, re.IGNORECASE):
                self.europeanrecord += 1

            if re.search("british record", location, re.IGNORECASE):
                self.britishrecord += 1

            location = re.sub(r"19\d\d", "", location)  # get rid of date
            location = re.sub(r"20\d\d", "", location)
            location = re.sub(r"\(25m\)", "", location)
            location = re.sub("25m", "", location)
            location = re.sub("50m", "", location)

            if xtime:
                opt = "\n  <div class=divTableRow>\n"
                opt += f"  <div class=divTableCell>{xtime} ({COURSE[course]})</div>\n"
                opt += f"  <div class=divTableCell>{xdate}</div>\n"
                opt += f"  <div class=divTableCell>{name}</div>\n"
                opt += f"  <div class=divTableCell>{location}</div>\n"
                opt += "  </div>\n"
                return opt
        return ""


class RelayRecord(Record):
    """Manage a relay records file."""

    def check_row(self, row, count):
        """Check a row from the records file."""

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
        if COURSE.get(event[4], None) is None:
            notify(f"Line {count}: unknown course '{event[4]}'\n")

        jevent = " ".join(event)

        if jevent in self.records:
            notify(f"Line {count}: duplicate '{jevent}'\n")
            return

        self.records[jevent] = row

    def print_extra(self, res):
        """Some extra printing (none for relay..."""
        return res

    def print_record(self, stroke, dist, age, course, gender):
        """Print a record."""

        # pylint: disable=too-many-arguments
        # pylint: disable=too-many-locals

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
            swimmers = f"{swimmer1}, {swimmer2}, {swimmer3}, {swimmer4}"
            if xtime:
                opt = "\n <div class=divTableRow>\n"
                opt += f" <div class=divTableCell>{xtime} ({COURSE[course]})</div>\n"
                opt += f" <div class=divTableCell>{xdate}</div>\n"
                opt += " <div class=divTable><div class=divTableBody>"
                opt += "<div class=divTableRow>\n"
                opt += f"  <div class=divTableCell>{loc}</div>\n"
                opt += " </div><div class=divTableRow>\n"
                opt += f" <div class=divTableCell>{swimmers}</div>\n"
                opt += " </div></div></div></div>\n"
                return opt
        return ""


def convert_time(xtime):
    """Convert a time to a number of seconds."""

    hms = xtime.split(":")
    if len(hms) == 2:
        res = float(hms[0]) * 60 + float(hms[1])
    else:
        res = float(hms[0])
    return res

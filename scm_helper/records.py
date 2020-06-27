"""Process club records."""
import csv
import datetime
import os
import re
import time
from pathlib import Path
from shutil import copyfile

from scm_helper.config import (
    C_AGE_EOY,
    C_ALL_AGES,
    C_OVERALL_FASTEST,
    C_RECORDS,
    C_RELAY,
    C_SE_ONLY,
    C_VERIFY,
    CONFIG_DIR,
    FILE_READ,
    FILE_WRITE,
    PRINT_DATE_FORMAT,
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

RELAY_STROKES = {
    "Free": "Freestyle",
    "Medley": "Medley",
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

RELAY_DISTANCE = {"200": 200, "400": 400, "800": 800}
PRINT_DISTANCE = {"200": "4 x 50", "400": "4 x 100", "800": "4 x 200"}
OVERALL = "Overall"

AGES = {
    OVERALL: 1,
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

ALL_AGES = {
    OVERALL: 1,
    "6": 0,
    "7": 0,
    "8": 0,
    "9": 0,
    "10": 0,
    "11": 0,
    "12": 0,
    "13": 0,
    "14": 0,
    "15": 0,
    "16": 0,
    "17": 0,
    "18": 0,
    "19-24": 0,
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

RELAY_AGES = {
    "72": "72+",
    "100": "100-119",
    "120": "120-159",
    "160": "160-199",
    "200": "200-239",
    "240": "240-279",
    "280": "280+",
}

GENDER = {"M": "Male", "F": "Female"}
RELAY_GENDER = {"M": "Male", "F": "Female", "Mixed": "Mixed"}

COURSE = {"25": "SC", "50": "LC"}

R_SWIMMER1 = "swimmer 1"
R_SWIMMER2 = "swimmer 2"
R_SWIMMER3 = "swimmer 3"
R_SWIMMER4 = "swimmer 4"
R_TIME = "time"
R_LOCATION = "location"
R_DATE = "date"

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

HEADER = "_header.txt"
FOOTER = """<p>
Records page created using
<a href="https://github.com/ColinRobbins/scm-helper">SCM Helper</a>.
</p>
"""

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

    def __init__(self, scm):
        """Initialise."""
        self.scm = scm
        self.records = None
        self.relay = None

        try:
            home = str(Path.home())
            mydir = os.path.join(home, CONFIG_DIR, RECORDS_DIR)

            if os.path.exists(mydir) is False:
                os.mkdir(mydir)

            filename = os.path.join(mydir, F_BASELINE)
            if os.path.isfile(filename) is False:
                with open(filename, FILE_WRITE) as file:
                    file.write(DEFAULT_RECORDS)

            filename = os.path.splitext(filename)[0]
            filename += HEADER

            if os.path.isfile(filename) is False:
                with open(filename, FILE_WRITE) as file:
                    file.write(DEFAULT_HEADER)

        except EnvironmentError as error:
            notify(f"Cannot create default records:\n{error}\n")

    def read_baseline(self):
        """Read baseline."""

        home = str(Path.home())
        mydir = os.path.join(home, CONFIG_DIR, RECORDS_DIR)

        self.records = Record()
        filename = os.path.join(mydir, F_BASELINE)
        res = self.records.read_baseline(filename, self.scm)

        if res and get_config(self.scm, C_RECORDS, C_RELAY):
            self.relay = RelayRecord()
            filename = os.path.join(mydir, F_RELAY_BASELINE)
            res = self.relay.read_baseline(filename, self.scm)

        return res

    def read_newtimes(self, filename):
        """Read swimtimes."""

        times = SwimTimes(self.records)
        res = times.merge_times(filename, self.scm)
        if self.records.newrecords:
            for record in sorted(self.records.newrecords):
                notify(self.records.newrecords[record])

            self.records.write_records()

        del times
        return res

    def create_html(self):
        """Create HTML files for records."""

        home = str(Path.home())
        mydir = os.path.join(home, CONFIG_DIR, RECORDS_DIR)

        if get_config(self.scm, C_RECORDS, C_ALL_AGES):
            ages = ALL_AGES
        else:
            ages = AGES

        res = self.records.create_html(GENDER, STROKES, ages, False)
        filename = os.path.join(mydir, F_RECORDS)

        try:
            with open(filename, FILE_WRITE) as htmlfile:
                htmlfile.write(res)

        except EnvironmentError as error:
            notify(f"Cannot create HTML file: {filename}\n{error}\n")
            return False

        notify(f"Created {filename}...\n")

        if self.relay:
            res = self.relay.create_html(RELAY_GENDER, RELAY_STROKES, RELAY_AGES, True)
            filename = os.path.join(mydir, F_RELAY_RECORDS)

            try:
                with open(filename, FILE_WRITE) as htmlfile:
                    htmlfile.write(res)

            except EnvironmentError as error:
                notify(f"Cannot create HTML file: {filename}\n{error}\n")
                return False

            notify(f"Created {filename}...\n")

        return filename

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
            with open(filename, newline="", encoding="utf-8-sig") as csvfile:
                csv_reader = csv.DictReader(csvfile)

                for row in csv_reader:
                    count += 1

                    if (int(count / 1000)) == (count / 1000):
                        notify(f"{count} ")

                    if (int(count / 10000)) == (count / 10000):
                        notify("\n")

                    self.process_row(row, count)

            notify(f"\nRead {filename}...\n")
            return True

        except EnvironmentError as error:
            notify(f"Cannot open swim time file: {filename}\n{error}\n")
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

        if "Swimmer" not in row:
            if count == 1:
                notify("Is the header line missing in the CSV?\n")
            return

        swimmer = row["Swimmer"]
        asa = row["SE Number"]
        xdate = row["Date"]
        pool = row["Pool Size"]
        dist = row["Swim Distance"]
        stroke = row["Stroke"]
        timestr = row["Time"]
        relay = row["Relay"]
        location = row["Location"]
        gender = row["Gender"]
        gala = row["Gala"]

        swimage = None
        if row["Age"]:
            swimage = int(row["Age"])

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

        if gala:
            location = gala
        elif location:
            pass
        else:
            location = "Unknown"

        if dist not in DISTANCE:
            debug(f"Line {count}: Unknown distance {dist}", 1)
            return

        if stroke not in STROKES:
            debug(f"Line {count}: Unknown stroke {stroke}", 1)
            return

        verify = get_config(self.scm, C_RECORDS, C_VERIFY)
        age_eoy = get_config(self.scm, C_RECORDS, C_AGE_EOY)
        se_only = get_config(self.scm, C_RECORDS, C_SE_ONLY)
        all_ages = get_config(self.scm, C_RECORDS, C_ALL_AGES)

        member = None
        if asa not in self.scm.members.by_asa:
            debug(f"Line {count}: No SE Number {swimmer}", 2)
            # We can't check, so go with it...
            if se_only:
                return
            verify = False
            age_eoy = False
        else:
            member = self.scm.members.by_asa[asa]
            swimmer = member.knownas  # for consistency of spelling

        if swimage and swimage >= 25:
            age_eoy = True  # Masters are always EOY

        swimdate = datetime.datetime.strptime(xdate, SCM_CSV_DATE_FORMAT)

        if member and age_eoy:
            yob = member.dob.year
            swimyear = swimdate.year
            swimage = swimyear - yob

        if verify and member and member.date_joined and (swimdate < member.date_joined):
            debug(f"Line {count}: Ignored, not a member at time of swim", 2)
            return

        if swimage is None:
            return

        if swimage < 18:
            start_age = int(swimage / 2) * 2
            end_age = start_age + 1
        elif swimage in (18, 19):
            if all_ages:
                start_age = 19
            else:
                start_age = 18
            end_age = 24
        else:
            start_age = int(swimage / 5) * 5
            # round it
            if start_age == 20:
                if all_ages:
                    start_age = 19
                else:
                    start_age = 18
                end_age = 24
            else:
                end_age = start_age + 4

        agegroup = f"{start_age}-{end_age}"

        if all_ages:
            if swimage <= 18:
                agegroup = str(swimage)
            ALL_AGES[agegroup] += 1
        else:
            AGES[agegroup] += 1

        event = f"{gender} {agegroup} {dist} {stroke} {pool}"

        swim = {
            S_EVENT: event,
            S_ASA: asa,
            S_NAME: swimmer,
            S_TIMESTR: timestr,
            S_FTIME: convert_time(timestr),
            S_LOCATION: location,
            S_DATE: xdate,
        }

        self.records.check_swim(swim)

        return


class Record:
    """Manage a records file."""

    # pylint: disable=too-many-instance-attributes

    def __init__(self):
        """Initilaise Records handling."""

        self._filename = None
        self.scm = None
        self.records = {}
        self.swimmers = {}
        self.newrecords = {}
        self.fieldnames = None

        self.worldrecord = 0
        self.europeanrecord = 0
        self.britishrecord = 0

        self.date = None

    def check_swim(self, swim):
        """Check a swim time to see if it as a record."""
        check_event = swim[S_EVENT]
        if check_event in self.records:
            event = self.records[check_event]
            if swim[S_FTIME] >= event[S_FTIME]:
                return

        self.records[check_event] = swim

        sloc = swim[S_LOCATION]
        newrec = (
            f"New record: {check_event}, {swim[S_NAME]}, {swim[S_TIMESTR]}, {sloc}\n"
        )
        self.newrecords[check_event] = newrec

        if get_config(self.scm, C_RECORDS, C_OVERALL_FASTEST):
            split_event = swim[S_EVENT].split()
            split_event[1] = OVERALL
            o_event = " ".join(str(item) for item in split_event)
            if o_event in self.records:
                event = self.records[o_event]
                if swim[S_FTIME] >= event[S_FTIME]:
                    return

            o_swim = swim.copy()
            o_swim[S_EVENT] = o_event
            self.records[o_event] = o_swim

    def check_row(self, row, count):
        """Check a row from the records file."""
        event = row[S_EVENT]
        test = event.split()

        if GENDER.get(test[0], None) is None:
            notify(f"Line {count}: unknown gender '{test[0]}'\n")
            return

        if get_config(self.scm, C_RECORDS, C_ALL_AGES):
            ages = ALL_AGES
        else:
            ages = AGES

        if ages.get(test[1], None) is None:
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

        ages[test[1]] += 1
        row[S_FTIME] = convert_time(row[S_TIMESTR])
        self.records[event] = row

    def read_baseline(self, filename, scm):
        """Read Facebook file."""
        self._filename = filename
        self.scm = scm

        try:
            count = 0
            fdate = os.path.getmtime(filename)
            self.date = time.strftime(PRINT_DATE_FORMAT, time.localtime(fdate))

            with open(filename, newline="") as csvfile:
                csv_reader = csv.DictReader(csvfile, skipinitialspace=True)
                self.fieldnames = csv_reader.fieldnames

                for row in csv_reader:
                    count += 1
                    self.check_row(row, count)

            notify(f"Read {filename} ({count})...\n")
            return True

        except EnvironmentError as error:
            notify(f"Cannot open records file: {filename}\n{error}\n")
            return False

        except csv.Error as error:
            notify(f"Error in records file: {filename}\n{error}\n")
            return False

        notify("Unknown error\n")
        return False

    def write_records(self):
        """Write the new reords, and backup old."""

        try:
            home = str(Path.home())
            today = datetime.datetime.now()
            str_today = today.strftime("%y%m%d-%H%M%S")
            self.date = today.strftime(PRINT_DATE_FORMAT)

            filename = f"records-{str_today}.csv"

            mybackupdir = os.path.join(home, CONFIG_DIR, RECORDS_DIR, "backup")

            if os.path.exists(mybackupdir) is False:
                os.mkdir(mybackupdir)

            backupfile = os.path.join(home, mybackupdir, filename)
            copyfile(self._filename, backupfile)

        except EnvironmentError as error:
            notify(f"Error creating records backup file: {backupfile}\n{error}\n")
            return

        try:
            with open(self._filename, "w", newline="") as file:
                writer = csv.DictWriter(file, self.fieldnames, extrasaction="ignore")
                writer.writeheader()
                for record in sorted(self.records):
                    writer.writerow(self.records[record])

        except EnvironmentError as error:
            notify(f"Cannot open records file to update: {self._filename}\n{error}\n")
            return

        except csv.Error as error:
            notify(f"Error in writing records file: {self._filename}\n{error}\n")
            return

        notify(f"Updated records file: {self._filename}\n")

    def create_html(self, arg_gender, arg_strokes, arg_ages, arg_relay):
        """create a records file."""
        # Get prefix

        # pylint: disable=too-many-locals
        # pylint: disable=too-many-nested-blocks
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        header = os.path.splitext(self._filename)[0]
        header += HEADER

        try:
            with open(header, FILE_READ) as file:
                prefix = file.read()

        except EnvironmentError as error:
            notify(f"records header file not found: {header}\n{error}\n")
            prefix = ""

        res = prefix

        overall = get_config(self.scm, C_RECORDS, C_OVERALL_FASTEST)
        if overall is None:
            overall = False

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

                        if overall is False:
                            if age == OVERALL:
                                continue

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

        res = res.replace("##RECORDHOLDERS##", top10)
        res = res.replace("##RECORDTALLY##", tally)
        res = res.replace("##RECORDUPDATE##", self.date)
        res += FOOTER
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

            swimmer = name.split(",")
            if len(swimmer) == 2:
                name = f"{swimmer[1]} {swimmer[0]}"

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

        event = row[S_EVENT].split()
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
        """Some extra printing."""
        res = res.replace("##RECORDUPDATE##", self.date)
        res += FOOTER
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

    try:
        hms = xtime.split(":")
        if len(hms) == 2:
            res = float(hms[0]) * 60 + float(hms[1])
        else:
            res = float(hms[0])
        return res
    except ValueError:
        debug(f"invalid time {xtime} ", 3)
        return 999999


# pylint: disable=too-many-lines


DEFAULT_RECORDS = """event,name,time,location,date
"""

DEFAULT_HEADER = """<style>

input[type=radio],
input[type=checkbox] {
  display: none;
}

input[type=radio]+label,
input[type=checkbox]+label {
  display: inline-block;
  margin: -2px;
  padding: 4px 1em;
  margin-bottom: 0;
  font-size: 12px;
  line-height: 19px;
  color: #333;
  text-align: center;
  vertical-align: middle;
  cursor: pointer;
  background-color: #f5f5f5;
  background-image: -moz-linear-gradient(top, #fff, #e6e6e6);
  background-image: -webkit-gradient(linear, 0 0, 0 100%, from(#fff), to(#e6e6e6));
  background-image: -webkit-linear-gradient(top, #fff, #e6e6e6);
  background-image: -o-linear-gradient(top, #fff, #e6e6e6);
  background-image: linear-gradient(to bottom, #fff, #e6e6e6);
  background-repeat: repeat-x;
  border: 1px solid #ccc;
  border-color: #e6e6e6 #e6e6e6 #bfbfbf;
  border-color: rgba(0, 0, 0, 0.1) rgba(0, 0, 0, 0.1) rgba(0, 0, 0, 0.25);
  border-bottom-color: #b3b3b3;
  filter: progid: DXImageTransform.Microsoft.gradient(startColorstr='#ffffffff',
            endColorstr='#ffe6e6e6', GradientType=0);
  filter: progid: DXImageTransform.Microsoft.gradient(enabled=false);
  -webkit-box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
           0 1px 2px rgba(0, 0, 0, 0.05);
  -moz-box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
           0 1px 2px rgba(0, 0, 0, 0.05);
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.2),
           0 1px 2px rgba(0, 0, 0, 0.05);
}

input[type=radio]:checked+label,
input[type=checkbox]:checked+label {
  background-image: none;
  outline: 0;
  -webkit-box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15),
              0 1px 2px rgba(0, 0, 0, 0.05);
  -moz-box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15),
              0 1px 2px rgba(0, 0, 0, 0.05);
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.15), 0 1px 2px rgba(0, 0, 0, 0.05);
  background-color: #4CAF50;
  color: white;
}


.divTable{
  display: table;
}
.divTableRow {
  display: table-row;
}

.divTableCell {
  display: table-cell;
  border: 0px;
  font-size: 12px;
  display: table-cell;
  padding: 3px 10px;
  vertical-align: middle
}

[name=record-inner-even] .divTableCell {
  display: table-cell;
  background-color: #83c983;
  color: black;
}
[name=record-inner-odd] .divTableCell {
  display: table-cell;
  background-color: #b8e0b8;
  color: black;
}

.divTableBody {
  display: table-row-group;
}

</style>


<script>

function SetBlock(block, state) {

    var elms = document.querySelectorAll(block);
    for (var i = 0; i < elms.length; i++) {
        elms[i].style.display = state;
    }
}

function ClearRecord() {

    SetBlock('[name="record-medley"]', "none")
    SetBlock('[name="record-free"]', "none")
    SetBlock('[name="record-fly"]', "none")
    SetBlock('[name="record-breast"]', "none")
    SetBlock('[name="record-back"]', "none")
    SetBlock('[name="record-male"]', "none")
    SetBlock('[name="record-female"]', "none")

}

function ShowBlock(block) {

    var str = document.querySelector(block).value;

    var target = '[name=\"' + str + '\"]'
    var elms = document.querySelectorAll(target);
    for (var i = 0; i < elms.length; i++) {

        if (elms[i].style.display === "none") {
            elms[i].style.display = "block";
        } else {
            elms[i].style.display = "none";
        }
    }
}


function ShowRecord() {

    ClearRecord();

    ShowBlock('input[name="record-stroke"]:checked')
    ShowBlock('input[name="record-gender"]:checked')

}


function docReady(fn) {

    // see if DOM is already available
    if (document.readyState === "complete" || document.readyState === "interactive") {
        // call on next available tick
        setTimeout(fn, 1);
    } else {
        document.addEventListener("DOMContentLoaded", fn);
    }
}

function SetButton(btn) {
    var h = document.getElementById(btn);
    h.onchange = function() {
        ShowRecord()
    };
}


docReady(function() {

    ClearRecord();

    SetBlock('[name="record-free"]', 'block')
    SetBlock('[name="record-male"]', 'block')

    SetButton('btn-free')
    SetButton('btn-back')
    SetButton('btn-breast')
    SetButton('btn-fly')
    SetButton('btn-medley')
    SetButton('btn-male')
    SetButton('btn-female')


});


</script>

<h3>Swimming Records</h3>

<div class="row clearfix">
<div class="column two-third">

<p>Rules: Must have been a Club member at the time of the swim.
Age as of December 31st in the year of the swim.</p>

##RECORDTALLY##
</div>
<div class="column third">
##RECORDHOLDERS##
</div>
</div>


<h2>Records</h2>
<p>Last Update: ##RECORDUPDATE##</p>
<p>Event:
  <input checked="checked" class="radio-group" id="btn-free"
  name="record-stroke" type="radio" value="record-free" />
  <label for="btn-free">Freestyle</label>

   <input class="radio-group" id="btn-fly" name="record-stroke"
   type="radio" value="record-fly" />
  <label for="btn-fly">Fly</label>

   <input class="radio-group" id="btn-back" name="record-stroke"
   type="radio" value="record-back" />
  <label for="btn-back">Back</label>

   <input class="radio-group" id="btn-breast" name="record-stroke"
   type="radio" value="record-breast" />
  <label for="btn-breast">Breast</label>

  <input class="radio-group" id="btn-medley" name="record-stroke"
  type="radio" value="record-medley" />
  <label for="btn-medley">Individual Medley</label>
</p>

<p>Gender:
  <input checked="checked" class="radio-group" id="btn-male" name="record-gender"
  type="radio" value="record-male" />
  <label for="btn-male">Male</label>

  <input class="radio-group" id="btn-female" name="record-gender"
  type="radio" value="record-female" />
  <label for="btn-female">Female</label>
</p>


<!-- Text below script generated. -->

"""

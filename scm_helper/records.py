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
from scm_helper.issue import debug

STROKES = {
    "Free": "Freestyle",
    "Back": "Backstroke",
    "Breast": "Breaststroke",
    "Fly": "Butterfly",
    "Medley": "Individual Medley",
}

# A list would do, but this allows a lookup
DISTANCE = [
    "50m",
    "100m",
    "200m",
    "400m",
    "800m",
    "1500m",
]

STROKE_DISTANCE = {
    "Free": ["50m","100m","200m","400m","800m","1500m"],
    "Back": ["50m","100m","200m"],
    "Breast": ["50m","100m","200m"],
    "Fly": ["50m","100m","200m"],
    "Medley": ["100m","200m", "400m"],
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

TAG_INNER_EVEN = "name=record-inner-even"
TAG_INNER_ODD = "name=record-inner-odd"

S_EVENT = "event"
S_ASA = "asa"
S_NAME = "name"
S_TIMESTR = "time"
S_FTIME = "ftime"
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
                    
                    if (int(count/1000)) == (count/1000):
                        notify(f"{count} ")
                    
                    if (int(count/10000)) == (count/10000):
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
            debug(f"Line {count}: Unknown distance {dist}",1)
            return

        if stroke not in STROKES:
            debug(f"Line {count}: Unknown stroke {stroke}",1)
            return

        if asa not in self.scm.members.by_asa:
            debug(f"Line {count}: No SE Number {swimmer}",2)
            return

        swimtime = convert_time(timestr)

        member = self.scm.members.by_asa[asa]

        yob = member.dob.year

        swimdate = datetime.datetime.strptime(xdate, SCM_CSV_DATE_FORMAT)
        swimyear = swimdate.year
        swimage = swimyear - yob

        if member.date_joined and (swimdate < member.date_joined):
            debug(f"Line {count}: Ignored, not a member at time of swim",2)
            return

        if swimage < 18:
            start_age = int(swimage / 2) * 2
            end_age = start_age + 1
        elif (swimage == 18) or (swimage == 19):
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

        location = re.sub("19\d\d", "", location)  # get rid of date
        location = re.sub("20\d\d", "", location)
        location = re.sub("\(25m\)", "", location)
        location = re.sub("25m", "", location)
        location = re.sub("50m", "", location)

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


# TODO.
# CHange Records below for members


class Record:
    """Manage a records file."""

    def __init__(self):
        """Initilaise Records handling."""
        self._filename = None
        self.scm = None
        self.records = {}
        self.swimmers = {}

    def check_swim(self, swim):
        """Check a swim time to see if it as a record."""
        if swim[S_EVENT] in self.records:
            event = self.records[swim[S_EVENT]]
            if swim[S_FTIME] >= event[S_FTIME]:
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
                    event = row["event"]
                    
                    test = event.split()

                    if GENDER.get(test[0], None) is None:
                        notify(f"Line {count}: unknown gender '{test[0]}'\n")
                        continue
                    if AGES.get(test[1], None) is None:
                        notify(f"Line {count}: unknown age '{test[1]}'\n")
                        continue
                    if test[2] not in DISTANCE:
                        notify(f"Line {count}: unknown distance '{test[2]}'\n")
                        continue
                    if STROKES.get(test[3], None) is None:
                        notify(f"Line {count}: unknown event '{test[3]}'\n")
                        continue
                    if COURSE.get(test[4], None) is None:
                        notify(f"Line {count}: unknown course '{test[4]}'\n")
                        continue

                    row[S_FTIME] = convert_time(row[S_TIMESTR])
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
                for dist in STROKE_DISTANCE[stroke]:

                    o_age = ""
                    tag = TAG_INNER_ODD
                    for age in AGES:
                        if AGES[age] == 0:
                            continue
                        opt = ""

                        opt_sc = self.print_record(stroke, dist, age, "25", gender)
                        opt_lc = self.print_record(stroke, dist, age, "50", gender)

                        if opt_sc or opt_lc:
                            #opt += " <div class=divTable><div class=divTableBody>\n"
                            if opt_sc:
                                opt += opt_sc
                            if opt_lc:
                                opt += opt_lc
                            #opt += " </div></div>\n"
                        else:
                            opt += " -\n"

                        if tag == TAG_INNER_EVEN:
                            tag = TAG_INNER_ODD
                        else:
                            tag = TAG_INNER_EVEN
                        o_age += f"""
<div class=divTableRow {tag}>
<div class=divTableCell>
Age: {age}:
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
        num = 0
        top10 = "<p>Top 10 record holders:</p><ul>"
        for holder in sorted(self.swimmers.items(), key=lambda x: x[1], reverse=True):
            top10 += f"<li>{holder[0]}: {holder[1]}</li>"
            num += 1
            if num > 10:
                break

        top10 += "</ul>"
        
        res = res.replace("RECORDHOLDERS",top10)
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
            
            if name in self.swimmers:
                self.swimmers[name] += 1
            else:
                self.swimmers[name] = 1
                
            if xtime:
                opt = "\n  <div class=divTableRow>\n"
                opt += f"  <div class=divTableCell>{xtime} ({COURSE[course]})</div>\n"
                opt += f"  <div class=divTableCell>{xdate}</div>\n"
                opt += f"  <div class=divTableCell>{name}</div>\n"
                opt += f"  <div class=divTableCell>{loc}</div>\n"
                opt += "  </div>\n"
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

"""Process club records."""
import csv
import os
import re
import ntpath
from pathlib import Path

from scm_helper.config import C_RECORDS, CONFIG_DIR, RECORDS_DIR, FILE_READ, get_config
from scm_helper.files import Files
from scm_helper.notify import notify

R_EVENT = "Event"
R_SWIMMER1 = "Swimmer1"
R_SWIMMER2 = "Swimmer2"
R_SWIMMER3 = "Swimmer3"
R_SWIMMER4 = "Swimmer4"
R_TIME = "Time"
R_LOCATION = "Location"
R_DATE = "Date"

RELAY_STROKES = {
	"Free": "Freestyle",
	"Medley": "Medley",
}

RELAY_DISTANCE = [200, 400, 800]
RELAY_AGES = [72, 100, 120,160, 200, 240, 280]
RELAY_GENDER = {
    "M": "Male",
    "F": "Female",
    "Mixed": "Mixed"
}

R_COURSE = {
    25: "LC",
    50: "SC"
}

class Records():
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
            record.create_html()

    def delete(self):
        """Delete."""
        for record in self.records:
            del record


class Record():
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
                    #TODO  split and tidy!
                    event = row[R_EVENT]
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
        for stroke in RELAY_STROKES:

            o_stoke = ""
            for dist in RELAY_DISTANCE:

                o_age = ""
                for age in RELAY_AGES:
                    opt = ""
                    
                    opt += self.print_record(stroke, dist, age, 25, "M")
                    opt += self.print_record(stroke, dist, age, 50, "M")
                    
                    opt += self.print_record(stroke, dist, age, 25, "F")
                    opt += self.print_record(stroke, dist, age, 50, "F")
                    
                    opt += self.print_record(stroke, dist, age, 25, "Mixed")
                    opt += self.print_record(stroke, dist, age, 50, "Mixed")
                    
                    if opt:
                        o_age += f"        {age}:\n{opt}\n"
                        
                if o_age:
                    o_stoke += f"    {dist}:\n{o_age}\n"
        
            if o_stoke:
                print (f"{RELAY_STROKES[stroke]}:\n{o_stoke}\n")
                
    def print_record(self, stroke, dist, age, course, gender):
        """Print a record."""
        lookup = f"{gender} {age} {dist}m {stroke} {course}"
        if lookup in self.records:
            record = self.records[lookup]
            xtime = record[R_TIME]
            xdate = record[R_DATE]
            loc = record[R_LOCATION]
            if xtime:
                return (f"            {RELAY_GENDER[gender]} {xtime} {xdate} {loc} {course}\n")
        return ""
    

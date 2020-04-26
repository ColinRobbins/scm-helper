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
RELAY_AGES = {"72":72, "100":100, "120":120 ,"160": 160, "200": 200, "240": 240, "280": 280}
RELAY_GENDER = {
    "M": "Male",
    "F": "Female",
    "Mixed": "Mixed"
}

R_COURSE = {
    "25": "LC",
    "50": "SC"
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
            print(record.create_html())

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
                    event = row[R_EVENT].split()
                    if RELAY_GENDER.get(event[0], None) is None:
                        notify (f"Line {count}: unknown gender '{event[0]}'\n")
                    if RELAY_AGES.get(event[1], None) is None:
                        notify (f"Line {count}: unknown age '{event[1]}'\n")
                        
                    dist = RELAY_DISTANCE.get(event[2], None)
                    if dist is None:
                        mdist = RELAY_DISTANCE.get(event[2].rstrip("m"), None)
                        if mdist is None:
                            notify (f"Line {count}: unknown distance '{event[2]}'\n")
                        else:
                            event[2] = str(mdist)
                        
                    if RELAY_STROKES.get(event[3], None) is None:
                        notify (f"Line {count}: unknown event '{event[3]}'\n")
                    if R_COURSE.get(event[4], None) is None:
                        notify (f"Line {count}: unknown course '{event[4]}'\n")
                        
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
                    for age in RELAY_AGES:
                        opt = ""
                        
                        opt_sc = self.print_record(stroke, dist, age, "25", gender)
                        opt_lc = self.print_record(stroke, dist, age, "50", gender)
     
                        if opt_sc or opt_lc:
                            opt += "        <table class=record-inner><tbody>\n"
                            if opt_sc:
                                opt += opt_sc
                            if opt_lc:
                                opt += opt_lc
                            opt += "        </tbody></table>\n"
                        else:
                            opt += "      -\n"
                            
                        o_age += "   <tr>\n"
                        o_age += f"    <td>\n    Age: {age}:\n    {opt}    </td>\n"
                        o_age += "   </tr>\n"
                            
                    if o_age:
                        o_dist += "  <table class=record-outer ><tbody>\n"
                        o_dist += f"  Dist: {dist}:\n{o_age}\n"
                        o_dist += "  </tbody></table>\n"
            
                if o_dist:
                    o_gender += (f" <div id=\"record-{stroke}\">\n")
                    o_gender += (f" {RELAY_STROKES[stroke]}:\n{o_dist}\n")
                    o_gender += " </div><br/>\n"
          
            if res:
                res += f"<div id=\"record-{gender}\">\n"
                res += gender
                res += o_gender
                res += "</div><br/>\n"
                
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
                opt = "        <tr>\n"
                opt += f"        <td>{loc}</td>\n"
                opt += f"        <td>{xtime} ({R_COURSE[course]})</td>\n"
                opt += f"        <td>{xdate}</td>\n"
                opt += f"        <td>{swimmer1}, {swimmer2}, {swimmer3}, {swimmer4}</td>\n"
                opt += "        </tr>\n"
                return opt
        return ""
    
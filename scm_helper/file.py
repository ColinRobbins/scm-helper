"""Read and process CSV Files."""
import csv
import datetime
import ntpath
import re

from scm_helper.config import (
    A_ASA_CATEGORY,
    A_ASA_NUMBER,
    A_DOB,
    A_FIRSTNAME,
    A_KNOWNAS,
    A_LASTNAME,
    C_CHECK_SE_NUMBER,
    C_DOB_FORMAT,
    C_FILES,
    C_IGNORE_GROUP,
    C_MAPPING,
    SCM_DATE_FORMAT,
    get_config,
)
from scm_helper.files import Files
from scm_helper.notify import notify

CAT_RE = re.compile(r"\d")


class Csv(Files):
    """CSV file handling."""

    def __init__(self):
        """Initilaise CSV."""
        super().__init__()
        self._csv = []
        self.by_name = {}
        self.by_knownas = {}
        self.cfg_file = None

    def readfile(self, file, scm):
        """Read CSV file."""
        self._filename = file
        self._scm = scm

        self.cfg_file = ntpath.basename(file)

        notify(f"Reading {self.cfg_file}...\n")

        cfg_dob_format = get_config(
            scm, C_FILES, self.cfg_file, C_MAPPING, C_DOB_FORMAT
        )
        if cfg_dob_format is None:
            cfg_dob_format = SCM_DATE_FORMAT

        cfg_dob = get_config(scm, C_FILES, self.cfg_file, C_MAPPING, A_DOB)
        if cfg_dob is None:
            cfg_dob = A_DOB

        cfg_cat = get_config(scm, C_FILES, self.cfg_file, C_MAPPING, A_ASA_CATEGORY)
        if cfg_cat is None:
            cfg_cat = A_ASA_CATEGORY

        try:
            count = 0
            with open(file, newline="", encoding="utf-8-sig") as csvfile:
                csv_reader = csv.DictReader(csvfile)

                for row in csv_reader:
                    count += 1
                    if count == 0:
                        continue
                    self._csv.append(row)

                    # Fix DOB
                    if cfg_dob in row:
                        try:
                            row[cfg_dob] = datetime.datetime.strptime(
                                row[cfg_dob], cfg_dob_format
                            )
                        except ValueError as error:
                            notify(f"Date format error in CSV:\n{error}\n")
                            return False
                    if cfg_cat in row:
                        cat = CAT_RE.search(row[cfg_cat])
                        if cat:
                            row[cfg_cat] = cat.group(0)

            notify(f"Read {file}...\n")
            return True

        except EnvironmentError:
            notify(f"Cannot open csv file: {file}\n")
            return False

        except csv.Error as error:
            notify(f"Error in csv file: {file}\n{error}\n")
            return False

        notify("Unknown error\n")
        return False

    def analyse(self, scm):
        """Analyse the CSV."""
        # Yes, its complicated...
        # pylint: disable=too-many-locals
        # pylint: disable=too-many-branches
        # pylint: disable=too-many-statements

        cfg = get_config(scm, C_FILES, self.cfg_file)
        if cfg is None:
            # ODD structure to keep line length in black limit
            prefix = "No configuration for "
            postfix = ", name matching only & default headers\n"
            notify(f"{prefix}{self._filename}{postfix}")

            cfg_first = A_FIRSTNAME
            cfg_last = A_LASTNAME
            cfg_knownas = A_KNOWNAS
            cfg_asa = A_ASA_NUMBER
            cfg_cat = A_ASA_CATEGORY
            cfg_dob = A_DOB
        else:
            cfg_first = get_config(scm, C_FILES, self.cfg_file, C_MAPPING, A_FIRSTNAME)
            cfg_last = get_config(scm, C_FILES, self.cfg_file, C_MAPPING, A_LASTNAME)
            cfg_knownas = get_config(scm, C_FILES, self.cfg_file, C_MAPPING, A_KNOWNAS)
            cfg_asa = get_config(scm, C_FILES, self.cfg_file, C_MAPPING, A_ASA_NUMBER)
            cfg_cat = get_config(scm, C_FILES, self.cfg_file, C_MAPPING, A_ASA_CATEGORY)
            cfg_dob = get_config(scm, C_FILES, self.cfg_file, C_MAPPING, A_DOB)

        cfg_check_se = get_config(scm, C_FILES, self.cfg_file, C_CHECK_SE_NUMBER)

        members = self._scm.members

        for row in self._csv:
            name = f"{row[cfg_first]} {row[cfg_last]}"
            self.by_name[name] = row
            if cfg_knownas:
                knownas = f"{row[cfg_knownas]} {row[cfg_last]}"
                self.by_knownas[knownas] = row
            else:
                knownas = "XYZXYZXYZ"  # will not match

            member = members.find_member(name)
            if member is None:
                member = members.find_member(knownas)
                if member is None:
                    self.file_error(name, "In file, not in SCM")
                    continue
            else:
                if member.is_active is False:
                    self.file_error(name, "In file & SCM but inactive")
                    continue

        for member in members.entities:
            if member.is_active is False:
                continue

            if not (member.is_swimmer or member.is_polo or member.is_synchro):
                continue

            if self.check_ignore(member):
                continue

            row = None
            good_name_match = False
            if member.name in self.by_name:
                row = self.by_name[member.name]
                good_name_match = True
            elif member.name in self.by_knownas:
                row = self.by_knownas[member.name]
                good_name_match = True
            elif member.knownas in self.by_name:
                row = self.by_name[member.knownas]
                good_name_match = True
            elif member.knownas in self.by_knownas:
                row = self.by_knownas[member.knownas]

            if row is None:
                msg = "In SCM but not in file"
                extra = f"(Group: {member.first_group})"
                self.file_error(member.name, msg, extra)
                continue

            if good_name_match is None:
                self.file_error(member.name, "Partial name match using knownas")

            errmsg = ""
            if cfg_check_se:
                if member.asa_number:
                    if int(member.asa_number) != int(row[cfg_asa]):
                        errmsg += "Different SE Number"
                else:
                    errmsg += "SE Missing in SCM"

                if member.asa_category:
                    if member.asa_category != row[cfg_cat]:
                        if errmsg:
                            errmsg += ", "
                        errmsg += "Different SE Category"
                else:
                    if errmsg:
                        errmsg += ", "
                    errmsg += "SE Category Missing in SCM"

                if member.dob:
                    if member.dob != row[cfg_dob]:
                        if errmsg:
                            errmsg += ", "
                        errmsg += "Different Date of Birth"
                else:
                    if errmsg:
                        errmsg += ", "
                    errmsg += "DOB Missing in SCM"

            if errmsg:
                self.file_error(member.name, errmsg)

    def check_ignore(self, member):
        """Return true if swimmer in ignore list."""
        cfg_ignore = get_config(self._scm, C_FILES, self.cfg_file, C_IGNORE_GROUP)
        if cfg_ignore:
            for ignore in cfg_ignore:
                if member.find_group(ignore):
                    return True
        return False

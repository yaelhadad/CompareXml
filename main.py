import sys
import argparse
import os
import xml.dom.minidom
import json
import traceback
from collections import OrderedDict
import traceback
import collections


def parse_args():
    parser = argparse.ArgumentParser(description='''Compare results of xml files new VS old''')
    parser.add_argument('-old_xml', type=str,
                        help='path to xml that contains old results', required=True)
    parser.add_argument('-new_xml', type=str,
                        help='path to xml that contains new results', required=True)
    parser.add_argument('-report', type=str,
                        help='path to file that contains different results', required=True)

    args = parser.parse_args()

    return args

def main():
    args = parse_args()
    try:
        CompareXml(args.old_xml, args.new_xml, args.report).run()
        if os.path.getsize(args.report) > 0:
            sys.exit(2)

    except ValueError as e:
        print(e)
        sys.exit(1)
    except Exception as e:
        traceback.print_exc()
        sys.exit(1)


class TestReport:
    CHECK_TYPE = "Type"
    CHECK_STATUS = "Status"
    CHECK_EXPECTED = "Expected"
    CHECK_ACTUAL = "Actual"
    CHECK_REASON = "Reason"
    TYPE_LOG = "log_diff"
    TYPE_FILE = "file_diff"
    EXIT_CODE = "exit_code"
    RUN_TIME = "run_time"

    # [Name, Status, CHECKS]
    def __init__(self, test):
        self.name = self._get_name(test)
        self.status = self._get_status(test)
        self.checks = self._get_checks(test)

    def _get_name(self, test):
        assert (False)

    def _get_status(self, test):
        assert (False)

    def _get_checks(self, test):
        assert (False)


# Save all the results from the old xml for each test
class TestReportOld(TestReport):
    exit_code = "ExitCode"
    diff_in_files = "DIFF!"
    missing_actual_file = "MISSING_FILE"
    missing_gold = "MISSING_GOLD"
    invalid_path_file = "PATH"
    invalid_ignore = "IGNORE"
    WORKDIR = 'Original_workdir'
    PERFORMANCE = 'Performance'
    TESTEDFILE = 'TestedFile'
    NAME = 'Name'
    STATUS = "Status"
    PATH = "Path"
    EXPECTED = "Expected"
    ACTUAL = "Real"
    PASSED = "PASSED"
    INVALID = "INVALID"
    FAILED = "FAILED"
    possible_file_failures_old = {
        "ACTUAL TESTED FILE IS MISSED!",
        "MISSED GOLD!",
        "INVALID PATH TO TEST FILE!",
        "INVALID IGNORE/IGNORE_LOG STATEMENTS!",
    }

    def _get_name(self, test):

        extract_workdir = test.attributes[self.WORKDIR].value.rsplit('/', 1)[0]

        if (extract_workdir != test.attributes[self.NAME].value):
            name = extract_workdir + "/" + test.attributes[self.NAME].value
        else:
            name = test.attributes[self.NAME].value

        return name

    def _get_status(self, test):

        return test.attributes[self.STATUS].value

    def _get_checks(self, test):

        checks = []

        # Files
        checks_files_node = test.getElementsByTagName(self.TESTEDFILE)
        workdir = test.attributes[self.WORKDIR].value
        if checks_files_node:
            for node in checks_files_node:

                full_file_path = node.getAttribute(self.PATH)
                file_path = self._extract_tested_file(workdir, full_file_path)

                if "logs/" in file_path:
                    check = {}
                    check[self.CHECK_TYPE] = self.TYPE_LOG

                else:
                    check = {}
                    check[self.CHECK_TYPE] = self.TYPE_FILE
                if node.getAttribute(self.STATUS) in self.possible_file_failures_old:
                    check[self.CHECK_STATUS] = self.INVALID
                elif node.getAttribute(self.STATUS) == self.diff_in_files:
                    check[self.CHECK_STATUS] = self.FAILED
                else:
                    check[self.CHECK_STATUS] = node.getAttribute(self.STATUS)
                check[self.CHECK_EXPECTED] = file_path + ".gold"
                check[self.CHECK_ACTUAL] = file_path
                check[self.CHECK_REASON] = ""
                checks.append(check)

        # Exit code, its status is checked only if its list isn't empty
        exit_code_item = test.getElementsByTagName(self.exit_code)
        if exit_code_item:
            exit_code = exit_code_item[0]
            check = {}
            check[self.CHECK_TYPE] = self.EXIT_CODE
            check[self.CHECK_STATUS] = exit_code.getAttribute(self.STATUS)

            check[self.CHECK_EXPECTED] = exit_code.getAttribute(self.EXPECTED)
            check[self.CHECK_ACTUAL] = exit_code.getAttribute(self.ACTUAL)
            if check[self.CHECK_STATUS] == self.PASSED:
                check[self.CHECK_REASON] = ""
            else:
                check[self.CHECK_REASON] = "Expected value differ"

            checks.append(check)

        # Performance status
        performance_item = test.getElementsByTagName(self.PERFORMANCE)
        if performance_item:
            check = {}
            check[self.CHECK_TYPE] = self.RUN_TIME
            check[self.CHECK_STATUS] = performance_item[0].getAttribute(self.STATUS)
            check[self.CHECK_EXPECTED] = performance_item[0].getAttribute(self.EXPECTED)
            check[self.CHECK_ACTUAL] = performance_item[0].getAttribute(self.ACTUAL)
            check[self.CHECK_REASON] = ""
            checks.append(check)

        return checks

    def _extract_tested_file(self, workdir, full_path):

        return full_path.split("%s/" % workdir, 1)[1]


# Save all the results from the new xml for each test
class TestReportNew(TestReport):
    ### PUT ALL THE CONSTANTS HERE THAT REATED TO NEW.
    ## ONLY WHRN I BUILD NEW I'LL TAKE FROM THE CONST

    exit_code = "ExitCode"
    CHECK = 'Check'
    TYPE = "Type"
    ACTUAL = "Actual"
    EXPECTED = "Expected"
    FAIL_INFO = "FailInfo"
    DESC = "Description"
    AUTHOR = "Author"
    NAME = "Name"
    STATUS = "Status"

    def _get_name(self, test):

        return test.attributes[self.NAME].value

    def _get_status(self, test):

        return test.attributes[self.STATUS].value

    def _get_checks(self, test):

        checks = []
        checks_node = test.getElementsByTagName(self.CHECK)
        if not checks_node:
            return checks
        for node in checks_node:
            check = {}
            check[self.CHECK_TYPE] = node.getAttribute(self.TYPE)
            check[self.CHECK_STATUS] = node.getAttribute(self.STATUS).upper()
            check[self.CHECK_EXPECTED] = node.getAttribute(self.EXPECTED)
            check[self.CHECK_ACTUAL] = node.getAttribute(self.ACTUAL)
            check[self.CHECK_REASON] = node.getAttribute(self.FAIL_INFO)

            checks.append(check)

        return checks


class CompareXml():
    TEST = "Test"
    STATUS = "Status"
    ENV = "Environment"
    REPORT = "Report"
    SUM = "Summary"
    DATE = "Date"
    STATION = "WorkStation"
    RELEASE = "Release"
    NUM_TESTS = "Executed"
    DIFFERENT = "Tests results are different - New VS Old:"
    GENERAL_INFO = "General inf is different"
    DIFF_TESTS = "Tests names are different"
    possible_file_failures_old = {
        "ACTUAL TESTED FILE IS MISSED!",
        "MISSED GOLD!",
        "INVALID PATH TO TEST FILE!",
        "INVALID IGNORE/IGNORE_LOG STATEMENTS!",
    }
    PASSED = "PASSED"
    test_report = []
    checks = {}

    def __init__(self, old_xml, new_xml, report):

        # Init
        self.old_xml_path = old_xml
        self.new_xml_path = new_xml
        self.report = report

        self.general_info_old = {}
        self.general_info_new = {}
        self.diff_name_tests = []

    def run(self):

        list_old = self._extract_info_old_xml()
        list_new = self._extract_info_new_xml()

        # Open the report
        compare_summary = self.report
        f = open(compare_summary, "w+")

        # Check that the genral info is the same
        if self._dict_compare_info(self.general_info_old, self.general_info_new):
            print("\n%s:\n" % self.GENERAL_INFO, file=f)
            print("old", self.general_info_old, file=f)
            print("new", self.general_info_new, file=f)

        ## #Check that the same tests run
        num_tests = self._len_list(list_old, list_new)

        for i in range(num_tests):

            # check names and update the list if there is need
            self._find_diff_names(list_old[i].name, list_new[i].name)

            # check general status.
            is_same = self._compare_status_test(list_old[i].status, list_new[i].status)
            # check all the fields- (files, exit code, run time)
            new_checks = []
            old_chacks = []
            new_checks = list_new[i].checks
            old_checks = list_old[i].checks
            len_list = self._len_list(new_checks, old_checks)

            list_mod = []
            for j in range(len_list):
                old_dict = {}
                new_dict = {}
                new_dict = self._check_compare(new_checks[j], old_checks[j])

                if len(new_dict) != 0:
                    list_mod.append(new_dict)

            if list_mod:
                self.checks["TEST_NAME: " + list_old[i].name] = list_mod

                # Final prints to the report - diff names
        if self.diff_name_tests:
            print("\n%s:\n" % self.DIFF_TESTS, file=f)
            for item in self.diff_name_tests:
                print(item, file=f)

        # Final prints to the report - checks
        if self.checks:
            print("\n%s:\n" % self.DIFFERENT, file=f)
            print(json.dumps((self.checks), indent=2), file=f)

    def _find_diff_names(self, old_name, new_name):

        if old_name != new_name:
            self.diff_name_tests.append("Old:" + old_name + " -VS- New:" + new_name)

    def _compare_status_test(self, old_status, new_status):

        if (old_status == new_status.upper()) and (old_status == self.PASSED):
            return True

    def _get_general_info(self, xmldoc):

        gen_info = {}
        # Fetch Environment & Report
        environment = xmldoc.getElementsByTagName(self.ENV)[0]
        report = xmldoc.getElementsByTagName(self.REPORT)[0]
        date = report.attributes[self.DATE].value
        station = environment.attributes[self.STATION].value
        release = environment.attributes[self.RELEASE].value

        # Fetch summery
        summary = xmldoc.getElementsByTagName(self.SUM)[0]
        num_of_tests = summary.attributes[self.NUM_TESTS].value

        # Fill gen info
        gen_info[self.DATE] = date;
        gen_info[self.STATION] = station
        gen_info[self.RELEASE] = release
        gen_info[self.NUM_TESTS] = num_of_tests

        return gen_info

    # Extract all the information from old xml
    def _extract_info_old_xml(self):

        # Validation of the file
        if not os.path.exists(self.old_xml_path):
            raise ValueError("Fatal error: file {} does not exists".format(self.old_xml_path))
            sys.exit(1)

        # Parse file
        xmldoc = xml.dom.minidom.parse(self.old_xml_path)

        # Extract parametrs for general info
        self.general_info_old = self._get_general_info(xmldoc)

        # Extract parametrs for each test
        test_lists = xmldoc.getElementsByTagName(self.TEST)

        all_tests = []
        # for each test
        for t in test_lists:
            test_report = []
            test_report = TestReportOld(t)
            all_tests.append(test_report)

        # print (all_tests)
        return all_tests

    # Extract all the information from old xml
    def _extract_info_new_xml(self):

        # Validation of the file
        if not os.path.exists(self.new_xml_path):
            raise ValueError("Fatal error: file {} does not exists".format(self.new_xml_path))
            sys.exit(1)

        # Parse file
        xmldoc = xml.dom.minidom.parse(self.new_xml_path)

        # Extract parametrs for each test
        self.general_info_new = self._get_general_info(xmldoc)

        # extract parametrs for each test
        test_lists = xmldoc.getElementsByTagName(self.TEST)

        all_tests = []
        # for each test
        for t in test_lists:
            test_report = TestReportNew(t)
            all_tests.append(test_report)

        return all_tests

    def _len_list(self, list1, list2):

        if len(list1) == len(list2):
            return (len(list1))
        else:
            return min(len(list1), len(list2))

    def _check_compare(self, new_dict, old_dict):

        if new_dict[self.STATUS] != old_dict[self.STATUS]:
            return new_dict, old_dict
        else:
            return {}

    def _dict_compare_info(self, d1, d2):

        d1_keys = set(d1.keys())
        d2_keys = set(d2.keys())
        shared_keys = d1_keys.intersection(d2_keys)
        modified = {o: (d1[o], d2[o]) for o in shared_keys if d1[o] != d2[o]}
        return modified


main()
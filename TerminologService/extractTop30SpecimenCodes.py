import csv
import re
import urllib.request

import requests
from bs4 import BeautifulSoup

from geccoToUIProfiles import ONTOLOGY_SERVER_ADDRESS
from model.UiDataModel import TerminologyEntry, TermCode

if __name__ == '__main__':
    with open('SpecimenCodes.CSV', mode='r') as csv_file:
        values = set()
        csv_reader = csv.DictReader(csv_file, delimiter=";")
        for row in csv_reader:
            for key, value in row.items():
                if snomed_code := re.search(r'\d+', value):
                    if len(snomed_code.group()) > 4:
                        values.add(snomed_code.group())
        in_vs = set()
        for value in values:
            response = requests.get(
                ONTOLOGY_SERVER_ADDRESS + "ValueSet/sct-specimen-type-napkon-sprec/$validate-code?system=http://snomed.info/sct&code=" + value)
            json = response.json()
            for parameter in json.get("parameter"):
                if parameter.get("name") == "result":
                    if parameter.get("valueBoolean"):
                        in_vs.add(value)
        codes = {}
        for value in values:
            response = requests.get(
                ONTOLOGY_SERVER_ADDRESS + "CodeSystem/$lookup?system=http://snomed.info/sct&code=" + value)
            json = response.json()
            if issue := json.get("issue"):
                print(issue)
                continue
            response = requests.get(ONTOLOGY_SERVER_ADDRESS + "CodeSystem/$subsumes?system=http://snomed.info/sct&codeA=123038009&codeB=" + value)
            json = response.json()
            for parameter in json.get("parameter"):
                if parameter.get("name") == "outcome":
                    if valueString := parameter.get("valueCode"):
                        if valueString == "not-subsumed":
                            print(value)
                            continue
            for parameter in json.get("parameter"):
                if parameter.get("name") == "display":
                    codes[value] = parameter.get("valueString")
        with open("SpecimenCodes_clean" + '.csv', 'w', newline='') as f:
            sheet = csv.writer(f)
            for key, value in codes.items():
                sheet.writerow([value, key, "http://snomed.info/sct"])

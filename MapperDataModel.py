from UiDataModel import del_keys, del_none, TermCode
import json
import sys


class FixedCriteria:
    def __init__(self, criteria_type, search_parameter, fhir_path, value=[]):
        self.type = criteria_type
        self.value = value
        self.fhirPath = fhir_path
        self.searchParameter = search_parameter


class MapEntry:
    DO_NOT_SERIALIZE = ["DO_NOT_SERIALIZE"]

    def __init__(self, term_code, fhir_resource_type, term_code_target, value_target=None, value_fhir_path=None, fixed_criteria=[]):
        self.key = term_code
        self.termCodeSearchParameter = term_code_target
        self.valueSearchParameter = value_target
        self.fhirResourceType = fhir_resource_type
        self.fixedCriteria = fixed_criteria
        self.valueFhirPath = value_fhir_path

    def __eq__(self, other):
        return self.key == other.key

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.key)

    def to_json(self):
        return json.dumps(self, default=lambda o: del_none(
            del_keys(o.__dict__, self.DO_NOT_SERIALIZE)), sort_keys=True, indent=4)


class MapEntryList:
    def __init__(self):
        self.entries = set()

    def to_json(self):
        self.entries = list(self.entries)
        return json.dumps(self.entries, default=lambda o: del_none(o.__dict__), sort_keys=True, indent=4)

    def get_code_systems(self):
        code_systems = set()
        for entry in self.entries:
            code_systems.add(entry.key.system)
            for fixed_criteria in entry.fixedCriteria:
                if fixed_criteria.type == "coding":
                    for value in fixed_criteria.value:
                        code_systems.add(value.system)
        return code_systems


class QuantityObservationMapEntry(MapEntry):
    def __init__(self, term_code):
        self.termCodeSearchParameter = "code"
        self.valueSearchParameter = "value-quantity"
        self.fhirResourceType = "Observation"
        self.key = term_code
        self.fixedCriteria = []


class ConceptObservationMapEntry(MapEntry):
    def __init__(self, term_code):
        self.termCodeSearchParameter = "code"
        self.valueSearchParameter = "value-concept"
        self.fhirResourceType = "Observation"
        self.key = term_code
        self.fixedCriteria = []


class ConditionMapEntry(MapEntry):
    def __init__(self, term_code):
        self.termCodeSearchParameter = "code"
        self.valueSearchParameter = None
        self.fhirResourceType = "Condition"
        confirmed = TermCode("http://terminology.hl7.org/CodeSystem/condition-ver-status", "confirmed", "confirmed")
        self.fixedCriteria = [FixedCriteria("coding", "verification-status", "verificationStatus", [confirmed])]
        self.key = term_code


class ProcedureMapEntry(MapEntry):
    def __init__(self, term_code):
        self.termCodeSearchParameter = "code"
        self.valueSearchParameter = None
        self.fhirResourceType = "Procedure"
        self.fixedCriteria = [FixedCriteria("code", "status", "status", ["completed", "in-progress"])]
        self.key = term_code


class SymptomMapEntry(MapEntry):
    def __init__(self, term_code):
        self.termCodeSearchParameter = "code"
        self.valueSearchParameter = "severity"
        self.valueFhirPath = "severity"
        self.fhirResourceType = "Condition"
        confirmed = TermCode("http://terminology.hl7.org/CodeSystem/condition-ver-status", "confirmed", "confirmed")
        self.fixedCriteria = [FixedCriteria("coding", "verification-status", "verificationStatus", [confirmed])]
        self.key = term_code


class MedicationStatementMapEntry(MapEntry):
    def __init__(self, term_code):
        self.termCodeSearchParameter = "code"
        self.fhirResourceType = "MedicationStatement"
        self.valueSearchParameter = None
        self.fixedCriteria = [FixedCriteria("code", "status", "status", ["active", "completed"])]
        self.key = term_code


class ImmunizationMapEntry(MapEntry):
    def __init__(self, term_code):
        self.termCodeSearchParameter = "vaccine-code"
        self.valueFhirPath = "vaccineCode"
        self.fhirResourceType = "Immunization"
        self.valueSearchParameter = None
        self.fixedCriteria = [FixedCriteria("code", "status", "status", ["completed"])]
        self.key = term_code


class DiagnosticReportMapEntry(MapEntry):
    def __init__(self, term_code):
        self.termCodeSearchParameter = "code"
        self.fhirResourceType = "DiagnosticReport"
        self.valueSearchParameter = None
        self.fixedCriteria = []
        self.key = term_code


def generate_child_entries(children, class_name):
    result = set()
    for child in children:
        result.add(str_to_class(class_name)(child.termCode))
        result = result.union(generate_child_entries(child.children, class_name))
    return result


def generate_map(categories):
    result = MapEntryList()
    for category in categories:
        for terminology in category.children:
            if terminology.fhirMapperType:
                class_name = terminology.fhirMapperType + "MapEntry"
                result.entries.add(str_to_class(class_name)(terminology.termCode))
                result.entries = result.entries.union(generate_child_entries(terminology.children, class_name))
            else:
                pass
                # TODO: Once Age and Ethnic Group are handled throw here
                # print(terminology)
    return result


def str_to_class(class_name):
    return getattr(sys.modules[__name__], class_name)

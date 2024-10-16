from enum import Enum


class StudyType(Enum):
    """
    Enum variable that contains all the possible studies from a DICOMItem
    """
    CONTROL_POINT_METRICS = 8
    PLAN_DETAIL = 2
    PLAN_METRICS_IMG = 4
    PLAN_METRICS_DATA = 5


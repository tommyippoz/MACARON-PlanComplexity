import os

from macaron_plancomplexity.StudyType import StudyType
from macaron_plancomplexity.complexity_utils import calculate_RTPlan_lib_metrics, calculate_RTPlan_custom_metrics
from macaron_plancomplexity.dicom_manager.DICOMFileObject import DICOMFileObject
from macaron_plancomplexity.dicom_manager.DICOMType import DICOMType
from macaron_plancomplexity.utils import load_DICOM, extractPatientData, clear_folder, write_dict


class DICOMItem:
    """
    Class that contains information of a set of DICOM, including TC, RT_STRUCT, RT_DOSE, RT_PLAN
    """

    def __init__(self, rtp_file):
        """
        Initializes a DICOMItem
        :param rtp_file: the path to the RTPlan
        """
        self.id = rtp_file
        self.rtp_file = rtp_file
        f_ob, f_type = load_DICOM(rtp_file)
        if f_type == DICOMType.RT_PLAN:
            self.rtp_object = DICOMFileObject(rtp_file, f_ob, f_type)
            if hasattr(f_ob, "PatientName"):
                self.id = str(f_ob.PatientName)
        else:
            self.rtp_object = None
            print("Unable to read object '" + str(rtp_file) + "'")
        self.plan_details = None
        self.plan_metrics = None
        self.plan_custom_metrics = None

    def is_valid(self) -> bool:
        """
        Checks if the item contains a valid RTPlan
        :return:
        """
        return self.rtp_object is not None

    def get_name(self) -> str:
        """
        Gets the name of the DICOMItem
        :return:
        """
        return self.id

    def get_rtp_object(self) -> DICOMFileObject:
        """
        Gets the dicom object of the RTPlan
        :return:
        """
        return self.rtp_object

    def get_patient_info(self) -> dict:
        """
        Extracts patient data from RTPlan
        """
        if self.rtp_objects is not None:
            return extractPatientData(self.rtp_object.get_object())
        else:
            return None

    def get_plan(self) -> dict:
        """
        Gets the RT_PLAN from the DICOMGroup
        :return: a dictionary containing the detail of the RT_PLAN, and a supporting string
        """
        if self.rtp_object is not None:
            self.plan_details = {}
            # rt_plans = []
            # for plan in self.rtp_objects:
            #     plan_det, rt_plan = DICOM_utils.get_plan(plan.get_file_name())
            #     if hasattr(plan_det, "date") and len(plan_det["date"]) == 0:
            #         plan_det["date"] = plan.get_object().InstanceCreationDate
            #     else:
            #         plan_det["date"] = "1900-01-01"
            #     if hasattr(plan_det, "time") and len(plan_det["time"]) == 0:
            #         plan_det["time"] = plan.get_object().InstanceCreationTime
            #     else:
            #         plan_det["time"] = 1
            #     if hasattr(plan_det, "label") and len(plan_det["label"]) == 0:
            #         plan_det["label"] = plan.get_object().RTPlanLabel
            #     else:
            #         plan_det["label"] = self.name
            #     if hasattr(plan_det, "name") and len(plan_det["name"]) == 0:
            #         plan_det["name"] = plan.get_object().RTPlanName
            #     else:
            #         plan_det["name"] = self.name
            #
            #     self.plan_details.append(plan_det)
            #     rt_plans.append(rt_plan)

            return self.plan_details
        else:
            return None

    def calculate_RTPlan_metrics(self, metrics_list=None, generate_plots=True, output_folder=None):
        """
        Calculates Complexity indexes from RTPlan
        :param output_folder: folder to print plots to
        :param generate_plots: True if plots have to be generated and saved to file
        :param metrics_list: the list of metrics to be calculated, initialized as DEFAULT_RTP_METRICS when missing
        :return: a dictionary containing the metric value and the unit for the RTPlan
        """
        return calculate_RTPlan_lib_metrics(self.rtp_file, self.id, metrics_list, generate_plots, output_folder)

    def calculate_RTPlan_custom_metrics(self) -> dict:
        """
        Calculates Complexity indexes from RTPlan
        :return: a dictionary containing the metric value and the unit for each RTPlan metric
        """
        return calculate_RTPlan_custom_metrics(self.rtp_file)

    def report(self, studies, output_folder, clean_folder=True):
        if os.path.exists(output_folder) and os.path.isdir(output_folder):
            group_folder = output_folder + "/" + self.id + "/"
            if os.path.exists(group_folder):
                if clean_folder:
                    print("Deleting existing info inside '" + group_folder + "' folder")
                    clear_folder(group_folder)
            else:
                os.makedirs(group_folder)
            if (studies is not None) and (len(studies) > 0):
                for study in studies:
                    try:
                        if study is StudyType.PLAN_DETAIL:
                            out_file = group_folder + "plan_detail.csv"
                            if self.plan_details is None:
                                self.get_plan()
                            write_dict(dict_obj=self.plan_details, filename=out_file, header="attribute,value")
                        elif study is StudyType.PLAN_METRICS_DATA:
                            out_file = group_folder + "plan_metrics.csv"
                            if self.plan_metrics is None:
                                self.calculate_RTPlan_metrics()
                            write_dict(dict_obj=self.plan_metrics, filename=out_file, header="metric,value,unit")
                        elif study is StudyType.PLAN_METRICS_IMG:
                            self.calculate_RTPlan_metrics(output_folder=group_folder)
                        elif study is StudyType.CONTROL_POINT_METRICS:
                            self.calculate_RTPlan_custom_metrics()
                            out_file = group_folder + "plan_custom_complexity_metrics.csv"
                            write_dict(dict_obj=self.plan_custom_metrics, filename=out_file,
                                       header="beam,attribute,list_index,metric_name,metric_value")
                        else:
                            print("Cannot recognize study '" + study + "' to report about")
                    except:
                        print("Error while processing study")
            else:
                print("No valid studies to report. Please input a list containing DICOMStudy objects")
        else:
            print("Folder '" + output_folder + "' does not exist or is not a folder")

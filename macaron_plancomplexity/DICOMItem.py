import os

from macaron_plancomplexity.StudyType import StudyType
from macaron_plancomplexity.complexity_utils import calculate_RTPlan_lib_metrics, calculate_RTPlan_custom_metrics
from macaron_plancomplexity.DICOMFileObject import DICOMFileObject
from macaron_plancomplexity.DICOMType import DICOMType
from macaron_plancomplexity.utils import load_DICOM, extractPatientData, clear_folder, write_dict, \
    extractManufacturerData, extractStudyData, extractImageData


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
        if self.rtp_object is not None:
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
            new_dict = self.get_patient_info()
            if new_dict is not None:
                self.plan_details.update(new_dict)
            new_dict = extractManufacturerData(self.rtp_object.get_object())
            if new_dict is not None:
                self.plan_details.update(new_dict)
            new_dict = extractStudyData(self.rtp_object.get_object())
            if new_dict is not None:
                self.plan_details.update(new_dict)
            new_dict = extractImageData(self.rtp_object.get_object())
            if new_dict is not None:
                self.plan_details.update(new_dict)
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
        self.plan_metrics, plan_imgs = calculate_RTPlan_lib_metrics(self.rtp_file, self.id, metrics_list,
                                                                    generate_plots, output_folder)
        return self.plan_metrics

    def calculate_RTPlan_custom_metrics(self) -> dict:
        """
        Calculates Complexity indexes from RTPlan
        :return: a dictionary containing the metric value and the unit for each RTPlan metric
        """
        self.plan_custom_metrics = calculate_RTPlan_custom_metrics(self.rtp_file)
        return self.plan_custom_metrics

    def report_macaron(self, studies, output_folder: str, clean_folder: bool = True):
        if os.path.exists(output_folder) and os.path.isdir(output_folder):
            group_folder = os.path.join(output_folder, self.id)
            if os.path.exists(group_folder):
                if clean_folder:
                    print("Deleting existing info inside '" + group_folder + "' folder")
                    clear_folder(group_folder)
            else:
                os.makedirs(group_folder)
            if (studies is not None) and (len(studies) > 0):
                overall_dict = {}
                for study in studies:
                    # try:
                    if study is StudyType.PLAN_DETAIL:
                        out_file = os.path.join(group_folder, "plan_detail.csv")
                        self.get_plan()
                        write_dict(dict_obj=self.plan_details, filename=out_file, header="attribute,value")
                        overall_dict.update(dict(("plan_details." + key, value) for (key, value) in self.plan_details.items()))
                    elif study is StudyType.PLAN_METRICS_DATA:
                        out_file = os.path.join(group_folder, "plan_lib_metrics.csv")
                        self.calculate_RTPlan_metrics(generate_plots=False)
                        write_dict(dict_obj=self.plan_metrics, filename=out_file, header="metric,value,unit")
                        overall_dict.update(dict(("plan_metrics." + key, value[0]) for (key, value) in self.plan_metrics.items()))
                    elif study is StudyType.PLAN_METRICS_IMG:
                        self.calculate_RTPlan_metrics(output_folder=group_folder, generate_plots=True)
                    elif study is StudyType.CONTROL_POINT_METRICS:
                        self.calculate_RTPlan_custom_metrics()
                        out_file = os.path.join(group_folder, "plan_custom_metrics.csv")
                        write_dict(dict_obj=self.plan_custom_metrics, filename=out_file,
                                   header="beam,attribute,list_index,metric_name,metric_value")
                        overall_dict.update(dict(("cp_beam1." + key, value) for (key, value) in self.plan_custom_metrics["Beam1"].items()))
                        overall_dict.pop('cp_beam1.Sequence', None)
                        if "Beam2" in self.plan_custom_metrics.keys():
                            overall_dict.update(dict(("cp_beam2." + key, value) for (key, value) in self.plan_custom_metrics["Beam2"].items()))
                        else:
                            overall_dict.update(dict(("cp_beam2." + key, None) for (key, value) in self.plan_custom_metrics["Beam1"].items()))
                        overall_dict.pop('cp_beam2.Sequence', None)
                        overall_dict.update(dict(("cp_plan." + key, value) for (key, value) in self.plan_custom_metrics["plan"].items()))
                    else:
                        print("Cannot recognize study '" + study + "' to report about")
                    # except:
                    #    print("Error while processing study")
                return overall_dict
            else:
                print("No valid studies to report. Please input a list containing DICOMStudy objects")
        else:
            print("Folder '" + output_folder + "' does not exist or is not a folder")
        return {}
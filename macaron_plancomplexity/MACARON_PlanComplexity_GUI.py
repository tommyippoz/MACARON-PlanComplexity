import csv
import os
import shutil

import tkinter
import tkinter.font
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askdirectory

from PIL import Image, ImageTk

from macaron_plancomplexity.StudyType import StudyType
from macaron_plancomplexity.DICOMItem import DICOMItem
from macaron_plancomplexity.utils import clear_folder, write_dict

OUT_FOLDER = ".\\output"


def find_DICOM_groups(main_folder):
    """
    Returns an array of DICOMItem in the main folder
    @param main_folder: root folder
    @return: array of dicom groups
    """
    plans = []
    rec_find_DICOM_groups(main_folder, plans)
    return plans


def rec_find_DICOM_groups(main_path, plans):
    """
    Supports the function to find all RTPlans in a folder
    """
    if os.path.isdir(main_path):
        for sub_item in os.listdir(main_path):
            subfolder_path = os.path.join(main_path, sub_item)
            rec_find_DICOM_groups(subfolder_path, plans)
    else:
        if os.path.isfile(main_path) and main_path.endswith(".dcm"):
            new_item = DICOMItem(main_path)
            if new_item.is_valid():
                plans.append(new_item)
    return plans


class MacaronGUI(tkinter.Frame):

    @classmethod
    def main(cls):
        root = Tk()
        root.title('MACARON GUI')
        #root.iconbitmap('./MACARON_nobackground.ico')
        root.configure(background='white')
        root.resizable(False, False)
        default_font = tkinter.font.nametofont("TkDefaultFont")
        default_font.configure(size=11)
        cls(root)
        root.eval('tk::PlaceWindow . center')
        root.mainloop()

    def __init__(self, root):
        super().__init__(root)
        self.checkboxes = [
            ["Plan", BooleanVar(value=True), StudyType.PLAN_DETAIL],
            ["Plan Metrics Data", BooleanVar(value=True), StudyType.PLAN_METRICS_DATA],
            ["Plan Metrics Plots", BooleanVar(value=True), StudyType.PLAN_METRICS_IMG],
            ["Control Point Metrics", BooleanVar(value=True), StudyType.CONTROL_POINT_METRICS]]

        # Frame Init
        self.root = root
        self.header = Frame(root, bg="white")
        self.content = Frame(root, bg="white")

        self.dicom_folder = None
        self.group_label = None
        self.run_button = None
        self.patients = []

        self.store_data = None
        self.create_data = None
        self.clean_data = None
        self.overall_csv = None

        # Build UI
        self.build_ui()

    def build_ui(self):
        # Grid Setup
        self.header.grid(padx=20, pady=10)
        self.content.grid(padx=20, pady=10)

        # Header
        head_lbl = Label(self.header, text="MACARON: data collection and Machine leArning \n "
                                           "to improve radiomiCs And support Radiation ONcology",
                         font='Helvetica 12 bold', bg="white")
        head_lbl.grid(column=0, row=0, columnspan=2)

        folder_lbl = Label(self.header, text="Select Folder with RTPs (DICOMs)", bg="white")
        folder_lbl.grid(column=0, row=1, padx=10, pady=5)
        folder_button = Button(self.header, text="Browse Folder", command=self.select_folder, bg="white")
        folder_button.grid(column=1, row=1, padx=10, pady=5)

        folder_lbl = Label(self.header, text="Patients Found in Folder:", bg="white")
        folder_lbl.grid(column=0, row=2, padx=10, pady=5)
        self.group_label = Label(self.header, text="---", bg="white")
        self.group_label.grid(column=1, row=2, padx=10, pady=5)

        folder_lbl = Label(self.content, text="MACARON - Plan Complexity Calculators:", font='Helvetica 12 bold',
                           bg="white")
        folder_lbl.grid(column=0, row=0, columnspan=3, padx=10, pady=10)

        checkboxes = []

        # CheckBoxes for Python Functions
        for [item, variable, tag] in self.checkboxes:
            cb = Checkbutton(self.content, text=item, variable=variable, onvalue=True, bg="white")
            cb.grid(sticky="W", column=0, row=len(checkboxes) + 1, padx=10, pady=5)
            checkboxes.append(cb)

        folder_lbl = Label(self.content, text="MACARON Output:", font='Helvetica 12 bold', bg="white")
        folder_lbl.grid(column=0, row=len(checkboxes) + 1, columnspan=3, padx=10, pady=10)

        self.create_data = BooleanVar(value=True)
        db_cb = Checkbutton(self.content, text="Output per Patient",
                            variable=self.create_data, onvalue=True, bg="white")
        db_cb.grid(column=0, row=len(checkboxes) + 3, padx=10, pady=10)

        self.clean_data = BooleanVar(value=False)
        data_clean_cb = Checkbutton(self.content, text="Clean Files",
                                    variable=self.clean_data, onvalue=True, bg="white")
        data_clean_cb.grid(column=1, row=len(checkboxes) + 3, padx=10, pady=10)

        self.overall_csv = BooleanVar(value=True)
        summary_cb = Checkbutton(self.content, text="Summary File",
                            variable=self.overall_csv, onvalue=True, bg="white")
        summary_cb.grid(column=2, row=len(checkboxes) + 3, padx=10, pady=10)

        self.run_button = Button(self.content, text="Run Analysis", bg="white",
                                 command=self.run_analysis, state=DISABLED)
        self.run_button.grid(column=0, row=len(checkboxes) + 4, columnspan=3, padx=10, pady=10)

    def select_folder(self):
        folder = askdirectory(initialdir="./")
        if folder is not None:
            self.dicom_folder = folder
            patients = find_DICOM_groups(self.dicom_folder)
            if patients is not None:
                self.patients = patients
                self.group_label['text'] = str(len(patients))
                self.run_button['text'] = "Process DICOM Data"
                self.run_button['state'] = "normal"
        else:
            print("Not a valid DICOM folder")

    def run_analysis(self):
        self.run_button['state'] = "disabled"
        # start progress bar
        popup = tkinter.Toplevel()
        popup.resizable(False, False)

        Label(popup, text="MACARON Analysis").grid(row=0, column=0)

        progress_var = DoubleVar()
        progress_bar = ttk.Progressbar(popup, variable=progress_var, maximum=100)
        progress_bar.grid(row=1, column=0)
        info_label = Label(popup, text="---")
        info_label.grid(row=2, column=0)

        popup.pack_slaves()

        # Summarize Studies to run
        studies = []
        for [name, var, tag] in self.checkboxes:
            if var.get() is True:
                studies.append([name, tag])

        # Bar Setup
        progress_step = float(100.0 / (len(studies) * len(self.patients)))
        progress = 0

        # Analysis Loop
        if self.clean_data is True:
            clean_folder = True
        else:
            clean_folder = False
        summary = []
        for patient in self.patients:
            study_index = 1
            patient_dict = {}
            for [name, study] in studies:
                popup.update()
                info_label['text'] = "Processing '" + patient.get_name() + "' for study " + \
                                     name + "' [" + str(study_index) + "/" + str(len(studies)) + "]"
                if self.create_data.get() is True:
                    summary_dict = patient.report_macaron(studies=[study], output_folder=OUT_FOLDER,
                                                          clean_folder=clean_folder)
                    patient_dict.update(summary_dict)
                    print("Results of '" + str(study) + "' for patient '" + patient.get_name() +
                          "' were computed and stored as TXT/CSV files or Images")
                progress += progress_step
                progress_var.set(progress)
                clean_folder = False
                study_index = study_index + 1
            summary.append(patient_dict)

        progress_bar.stop()
        self.run_button['state'] = "normal"
        popup.destroy()

        # Saving Summary file
        keys = summary[0].keys()
        with open(os.path.join(OUT_FOLDER, "metric_all_patients.csv"), 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, keys)
            dict_writer.writeheader()
            for patient_dict in summary:
                dict_writer.writerow(patient_dict)


if __name__ == "__main__":

    # Checking and clearing OUT_FOLDER
    if not os.path.exists(OUT_FOLDER):
        os.makedirs(OUT_FOLDER)
    else:
        clear_folder(OUT_FOLDER)

    with open(os.path.join(OUT_FOLDER, "output_explanation.txt"), "w") as f:
        f.write("The tool computes the following custom metrics, which are printed in a CSV:\n\n" +
                "per Beam: \n\t- MUbeam\n\t- MUfinalweight \n\t- M     \n\t- MCS     \n\t- MCSV     \n\t- MFC     \n\t- BI     \n\t- avgApertureLessThan1cm     \n\t- yDiffLessThan1cm     \n\t- SAS2 \n\t- SAS5     \n\t- SAS10 \n\t- SAS20" +
                "\nper Plan:     \n\t- MUplan     \n\t- Mplan     \n\t- MCSplan     \n\t- MCSVplan     \n\t- MFCplan     \n\t- PI     \n\t- nCP     \n\t- avgApertureLessThan1cm \n\t- yDiffLessThan1cm" +
                "Moreover, it plots the following graphs, and the corresponding CSV file:" +
                "\n\t- ApertureIrregularityMetric     \n\t- AreaMetricEstimator \n\t- MeanAreaMetricEstimator     \n\t- PyComplexityMetric \n" +
                "using the library at https://github.com/victorgabr/ApertureComplexity, from Victor Gabriel Leandro Alves, D.Sc. University of Michigan, Radiation Oncology https://github.com/umro/Complexity" +
                "\n\nDependencies of the Python tool: \n\t- numpy     \n\t- matplotlib     \n\t- pydicom     \n\t- shutil     \n\t- and the GitHub library above")

    MacaronGUI.main()

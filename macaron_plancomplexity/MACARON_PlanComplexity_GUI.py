import configparser
import os

import tkinter
import tkinter.font
from tkinter import *
from tkinter import ttk
from tkinter.filedialog import askdirectory

from PIL import Image, ImageTk
#from PIL import ImageTk

from macaron_plancomplexity.StudyType import StudyType
from macaron_plancomplexity.dicom_manager.DICOMItem import DICOMItem
from macaron_plancomplexity.utils import clear_folder

TMP_FOLDER = "tmp"

OUT_FOLDER = "output"


def find_DICOM_groups(main_folder, tmp_folder):
    """
    Returns an array of DICOMItem in the main folder
    @param main_folder: root folder
    @return: array of dicom groups
    """
    plans = []
    rec_find_DICOM_groups(main_folder, tmp_folder, plans)
    return plans


def rec_find_DICOM_groups(main_path, tmp_folder, plans):
    if os.path.isdir(main_path):
        for sub_item in os.listdir(main_path):
            subfolder_path = os.path.join(main_path, sub_item)
            rec_find_DICOM_groups(subfolder_path, tmp_folder, plans)
    else:
        if os.path.isfile(main_path) and main_path.endswith(".dcm"):
            new_item = DICOMItem(main_path)
            if new_item.is_valid():
                plans.append(new_item)
    return plans


class MacaronGUI(tkinter.Frame):

    @classmethod
    def main(cls, config):
        root = Tk()
        root.title('MACARON GUI')
        root.iconbitmap('../resources/MACARON_nobackground.ico')
        root.configure(background='white')
        root.resizable(False, False)
        default_font = tkinter.font.nametofont("TkDefaultFont")
        default_font.configure(size=11)
        cls(root, config)
        root.eval('tk::PlaceWindow . center')
        root.mainloop()

    def __init__(self, root, config):
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
        folder_lbl.grid(column=0, row=0, columnspan=2, padx=10, pady=10)

        checkboxes = []

        # CheckBoxes for Python Functions
        for [item, variable, tag] in self.checkboxes:
            cb = Checkbutton(self.content, text=item, variable=variable, onvalue=True, bg="white")
            cb.grid(sticky="W", column=0, row=len(checkboxes) + 1, padx=10, pady=5)
            checkboxes.append(cb)

        photo = ImageTk.PhotoImage(Image.open('../resources/MACARON.png'))
        label = Label(self.content, image=photo, bg="white")
        label.image = photo
        label.grid(column=1, row=1, rowspan=len(checkboxes), padx=10, pady=5)

        folder_lbl = Label(self.content, text="MACARON Output:", font='Helvetica 12 bold', bg="white")
        folder_lbl.grid(column=0, row=len(checkboxes) + 1, columnspan=2, padx=10, pady=10)

        self.create_data = BooleanVar(value=True)
        db_cb = Checkbutton(self.content, text="File Output",
                            variable=self.create_data, onvalue=True, bg="white")
        db_cb.grid(column=0, row=len(checkboxes) + 3, padx=10, pady=10)

        self.clean_data = BooleanVar(value=False)
        data_clean_cb = Checkbutton(self.content, text="Clean Files",
                                    variable=self.clean_data, onvalue=True, bg="white")
        data_clean_cb.grid(column=1, row=len(checkboxes) + 3, padx=10, pady=10)

        self.run_button = Button(self.content, text="Run Analysis", bg="white",
                                 command=self.run_analysis, state=DISABLED)
        self.run_button.grid(column=0, row=len(checkboxes) + 4, columnspan=2, padx=10, pady=10)

    def select_folder(self):
        folder = askdirectory(initialdir="./")
        if folder is not None:
            self.dicom_folder = folder
            patients = find_DICOM_groups(self.dicom_folder, TMP_FOLDER)
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
        for patient in self.patients:
            study_index = 1
            for [name, study] in studies:
                popup.update()
                info_label['text'] = "Processing '" + patient.get_name() + "' for study " + \
                                     name + "' [" + str(study_index) + "/" + str(len(studies)) + "]"
                if self.create_data.get() is True:
                    patient.report(studies=[study], output_folder="output", clean_folder=clean_folder)
                    print("Results of '" + str(
                        study) + "' for patient '" + patient.get_name() + "' were computed and stored as TXT/CSV files or Images")
                progress += progress_step
                progress_var.set(progress)
                clean_folder = False
                study_index = study_index + 1

        progress_bar.stop()
        self.run_button['state'] = "normal"
        popup.destroy()


if __name__ == "__main__":

    # Load configuration parameters
    config = configparser.ConfigParser()
    config.read('../plancomplexity.config')

    # Checking and clearing TMP_FOLDER
    if not os.path.exists(TMP_FOLDER):
        os.makedirs(TMP_FOLDER)
    else:
        clear_folder(TMP_FOLDER)

    # Checking and clearing OUT_FOLDER
    if not os.path.exists(OUT_FOLDER):
        os.makedirs(OUT_FOLDER)
    else:
        clear_folder(OUT_FOLDER)

    MacaronGUI.main(config)

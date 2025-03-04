import os
import shutil

# Main dependency of the library
import pydicom
from pydicom import FileDataset

from macaron_plancomplexity.DICOMType import DICOMType


def clear_folder(folder: str) -> None:
    """
    Clears data in existing folder
    :param folder: the folder to clean
    :return: nothing
    """
    for filename in os.listdir(folder):
        file_path = os.path.join(folder, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))


def load_DICOM(file_path: str, sanitize: bool = True):
    """
    Loads a DICOM object from a file
    :param file_path: path to the DICOM file
    :param sanitize: True if a TransferSyntaxUID field may be missing from the DICOM file
    :return: the DICOMObject and its DICOMType
    """
    dicom_ob = pydicom.read_file(file_path, force=True)
    if sanitize and ("TransferSyntaxUID" not in dicom_ob.file_meta):
        sanitize_DICOM(file_path)
        dicom_ob = pydicom.read_file(file_path, force=True)
    dicom_type = get_DICOM_type_from_object(dicom_ob)
    return dicom_ob, dicom_type


def sanitize_DICOM(file_path: str) -> None:
    """
    Updates a DICOM file by adding a TransferSyntaxUID parameter (default value)
    :param file_path: file to sanitize
    """
    ds = pydicom.read_file(file_path, force=True)
    if "TransferSyntaxUID" not in ds.file_meta:
        ds.file_meta.TransferSyntaxUID = pydicom.uid.ImplicitVRLittleEndian
        print("Adding parameter 'TransferSyntaxUID' to DICOM")
        pydicom.write_file(file_path, ds)


def get_DICOM_type(dicom_ob: FileDataset) -> DICOMType:
    """
    Gets the DICOMType corresponding to the FileDataset object
    :param dicom_ob: the FileDataset object
    :return: the DICOMType
    """
    if dicom_ob is not None:
        if hasattr(dicom_ob, 'StructureSetROISequence'):
            return DICOMType.RT_STRUCT
        elif hasattr(dicom_ob, 'DoseUnits'):
            return DICOMType.RT_DOSE
        elif hasattr(dicom_ob, 'RTPlanDescription'):
            return DICOMType.RT_PLAN
        elif hasattr(dicom_ob, 'CTDIvol'):
            return DICOMType.TC
    return DICOMType.OTHER


def get_DICOM_type_from_object(dicom_ob: FileDataset) -> DICOMType:
    """
    Determines the DICOMType of the FileDataset using its SOPClassUID.
    :param dicom_ob: the FileDataset object
    :return: the DICOMType
    """
    uid = getattr(dicom_ob, 'SOPClassUID', None)
    return get_DICOM_type_from_ID(uid)


def get_DICOM_type_from_ID(uid: str) -> DICOMType:
    """
    Determines the DICOMType from a SOPClassUID value.
    :param uid: the SOPClassUID value
    :return: the DICOMType
    """
    if uid == '1.2.840.10008.5.1.4.1.1.481.2':
        return DICOMType.RT_DOSE
    elif uid == '1.2.840.10008.5.1.4.1.1.481.3':
        return DICOMType.RT_STRUCT
    elif uid == '1.2.840.10008.5.1.4.1.1.481.5':
        return DICOMType.RT_PLAN
    elif uid == '1.2.840.10008.5.1.4.1.1.2' or uid == '1.2.840.10008.5.1.4.1.1.4':
        return DICOMType.TC
    else:
        return None


def extractPatientData(dicom_ob: FileDataset) -> dict:
    """
    Gets a dictionary with patient data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of patient data
    """
    try:
        patient_data = {"PatientID": dicom_ob.PatientID,
                        "StudyID": dicom_ob.StudyID,
                        "StudyDate": dicom_ob.StudyDate,
                        "StudyDesc": dicom_ob.StudyDescription,
                        "PatientSex": dicom_ob.PatientSex}
    except:
        patient_data = None
    return patient_data


def extractDoseData(dicom_ob: FileDataset) -> dict:
    """
    Gets a dictionary with dose data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of dose data
    """
    try:
        dose_data = {"GridScaling": dicom_ob.DoseGridScaling,
                     "SumType": dicom_ob.DoseSummationType,
                     "Type": dicom_ob.DoseType,
                     "Units": dicom_ob.DoseUnits,
                     "RTPlanSequence": dicom_ob.ReferencedRTPlanSequence}
    except:
        dose_data = None
    return dose_data


def extractStructureData(dicom_ob: FileDataset) -> dict:
    """
    Gets a dictionary with structures data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of structures data
    """
    structure_data = {"StructureSetSequence": dicom_ob.ReferencedStructureSetSequence}
    return structure_data


def extractManufacturerData(dicom_ob: FileDataset) -> dict:
    """
    Gets a dictionary with manufacturer data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of manufacturer data
    """
    try:
        man_data = {"Name": dicom_ob.Manufacturer,
                    "ModelName": dicom_ob.ManufacturerModelName,
                    "SW_Version": dicom_ob.SoftwareVersions,
                    "CharSet": dicom_ob.SpecificCharacterSet}
    except:
        man_data = None
    return man_data


def extractStudyData(dicom_ob: FileDataset) -> dict:
    """
    Gets a dictionary with study data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of patient data
    """
    try:
        study_data = {"ID": dicom_ob.StudyID,
                      "UID": dicom_ob.StudyInstanceUID,
                      "Time": dicom_ob.StudyTime,
                      "Date": dicom_ob.StudyDate,
                      "Modality": dicom_ob.Modality,
                      "NumFrames": dicom_ob.NumberOfFrames,
                      "PhotometricInterpretation": dicom_ob.PhotometricInterpretation,
                      "Correction": dicom_ob.TissueHeterogeneityCorrection}
    except:
        study_data = None
    return study_data


def extractImageData(dicom_ob: FileDataset) -> dict:
    """
    Gets a dictionary with image data from the DICOM
    :param dicom_ob: the FileDataset from the DICOM
    :return: a dictionary of image data
    """
    try:
        image_data = {"Orientation": dicom_ob.ImageOrientationPatient,
                      "Position": dicom_ob.ImagePositionPatient,
                      "FrameIncrementPointer": dicom_ob.FrameIncrementPointer,
                      "GridOffsetVector": dicom_ob.GridFrameOffsetVector}
    except:
        image_data = None
    return image_data


def write_dict(dict_obj: dict, filename: str, header=None):
    """
    Allows for printing a dict object as a CSV file
    :param dict_obj: the object to print
    :param filename: the file to print
    :param header: header, if any
    :return: None
    """
    with open(filename, 'w') as f:
        if header is not None:
            f.write("%s\n" % header)
        write_rec_dict(f, dict_obj, "")


def write_rec_dict(out_f, dict_obj, prequel):
    """
    Supports dict writing to file (recursively)
    :param out_f: filehandler
    :param dict_obj: the object to print
    :param prequel: a prequel to rows, if any
    :return: None
    """
    if (type(dict_obj) is dict) or issubclass(type(dict_obj), dict):
        for key in dict_obj.keys():
            if (type(dict_obj[key]) is dict) or issubclass(type(dict_obj[key]), dict):
                if len(dict_obj[key]) > 20:
                    for inner in dict_obj[key].keys():
                        if (prequel is None) or (len(prequel) == 0):
                            out_f.write("%s,%s,%s\n" % (key, inner, dict_obj[key][inner]))
                        else:
                            out_f.write("%s,%s,%s,%s\n" % (prequel, key, inner, dict_obj[key][inner]))
                else:
                    new_prequel = prequel + "," + str(key) if (prequel is not None) and (len(prequel) > 0) else str(key)
                    write_rec_dict(out_f, dict_obj[key], new_prequel)
            elif type(dict_obj[key]) is list:
                item_count = 1
                for item in dict_obj[key]:
                    new_prequel = prequel + "," + str(key) + ",item" + str(item_count) \
                        if (prequel is not None) and (len(prequel) > 0) else str(key) + ",item" + str(item_count)
                    write_rec_dict(out_f, item, new_prequel)
                    item_count += 1
            else:
                if (prequel is None) or (len(prequel) == 0):
                    out_f.write("%s,%s\n" % (key, dict_obj[key]))
                else:
                    out_f.write("%s,%s,%s\n" % (prequel, key, dict_obj[key]))
    elif type(dict_obj) is list:
        item_count = 1
        for item in dict_obj:
            if (prequel is not None) and (len(prequel) > 0):
                new_prequel = prequel + ",item" + str(item_count)
            else:
                new_prequel = prequel
            write_rec_dict(out_f, item, new_prequel)
            item_count += 1
    else:
        if (prequel is None) or (len(prequel) == 0):
            out_f.write("%s\n" % dict_obj)
        else:
            out_f.write("%s,%s\n" % (prequel, dict_obj))

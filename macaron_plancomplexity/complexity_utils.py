import copy
import math
import os
import sys

import matplotlib.pyplot as plt
import numpy

from macaron_plancomplexity.PyComplexityMetric import (
    PyComplexityMetric,
    MeanAreaMetricEstimator,
    AreaMetricEstimator,
    ApertureIrregularityMetric)

from macaron_plancomplexity.dicomrt import RTPlan

# These are needed to interact with the complexity library
DEFAULT_RTP_METRICS = [
    PyComplexityMetric,
    MeanAreaMetricEstimator,
    AreaMetricEstimator,
    ApertureIrregularityMetric]

RTP_METRICS_UNITS = {
    PyComplexityMetric: "CI [mm^-1]",
    MeanAreaMetricEstimator: "mm^2",
    AreaMetricEstimator: "mm^2",
    ApertureIrregularityMetric: "dimensionless"}


def calculate_RTPlan_lib_metrics(rtp_filename: str, patient_name: str, metrics_list=None, generate_plots=True, output_folder=None):
    """
    Calculates Complexity indexes from RTPlan
    :param output_folder: folder to print plots to
    :param generate_plots: True if plots have to be generated and saved to file
    :param metrics_list: the list of metrics to be calculated, initialized as DEFAULT_RTP_METRICS when missing
    :return: a dictionary containing the metric value and the unit for each RTPlan metric
    """
    if (metrics_list is None) or (type(metrics_list) is not list):
        metrics_list = DEFAULT_RTP_METRICS

    if rtp_filename is not None:
        pm = {}
        plan_imgs = {}
        plan_info = RTPlan(filename=rtp_filename)
        if plan_info is not None:
            plan_dict = plan_info.get_plan()
            for metric in metrics_list:
                unit = RTP_METRICS_UNITS[metric]
                met_obj = metric()
                plan_metric = met_obj.CalculateForPlan(None, plan_dict)
                pm[metric.__name__] = [plan_metric, unit]
                if generate_plots:
                    for k, beam in plan_dict["beams"].items():
                        fig, ax = plt.subplots()
                        cpx_beam_cp = met_obj.CalculateForBeamPerAperture(None, plan_dict, beam)
                        ax.plot(cpx_beam_cp)
                        ax.set_xlabel("Control Point")
                        ax.set_ylabel(f"${unit}$")
                        txt = f"Patient: {patient_name} - {metric.__name__} per control point"
                        ax.set_title(txt)
                        if output_folder is not None:
                            img_path = os.path.join(output_folder, patient_name + "_" + metric.__name__ + ".png")
                        else:
                            img_path = patient_name + "_" + metric.__name__ + ".png"
                        fig.savefig(img_path, dpi=fig.dpi)
                        plan_imgs[metric.__name__] = img_path
            return pm, plan_imgs
        else:
            print("Supplied file is not an RT_PLAN")
    return None, None


def calculate_RTPlan_custom_metrics(rtp_filename: str) -> dict:
    """
    Calculates Custom Complexity indexes from RTPlan
    :return: a dictionary containing the metric value and the unit for each RTPlan metric
    """

    if rtp_filename is not None:

        plan_dict = RTPlan(filename=rtp_filename).get_plan()
        beam_index = 1
        pcm = {}

        for beam in list(plan_dict["beams"].values()):

            beam_name = "Beam" + str(beam_index)
            beam_mu = float(beam['MU'])
            beam_final_ms_weight = float(beam['FinalCumulativeMetersetWeight'])
            pcm[beam_name] = {"Sequence": [], "MUbeam": beam_mu, "MUfinalweight": beam_final_ms_weight}

            item_index = 0
            left_jaws = []
            right_jaws = []
            for item in beam["ControlPointSequence"]:
                item_index += 1
                cp_mu = float(item['CumulativeMetersetWeight'].value)
                if hasattr(item, "BeamLimitingDevicePositionSequence"):
                    if len(item.BeamLimitingDevicePositionSequence) == 3:
                        y_data = item.BeamLimitingDevicePositionSequence[1].LeafJawPositions
                        lj_arr = item.BeamLimitingDevicePositionSequence[2].LeafJawPositions
                    else:
                        y_data = item.BeamLimitingDevicePositionSequence[0].LeafJawPositions
                        lj_arr = item.BeamLimitingDevicePositionSequence[1].LeafJawPositions
                    cm, left, right = complexity_indexes(y_data, lj_arr)
                    left_jaws.append(left)
                    right_jaws.append(right)
                    if cm is not None:
                        cm["index"] = item_index
                        if item_index < len(beam["ControlPointSequence"]):
                            next_cp_mu = float(
                                beam["ControlPointSequence"][item_index]['CumulativeMetersetWeight'].value)
                            cm["MU"] = (next_cp_mu - cp_mu) * beam_mu / beam_final_ms_weight
                        else:
                            cm["MU"] = 0
                        cm["MUrel"] = cm["MU"] / beam_mu
                        cm["MUcumrel"] = cp_mu + cm["MUrel"]
                    pcm[beam_name]["Sequence"].append(cm)
                else:
                    print("Item " + str(item_index) + "of beam " + str(beam_index) + " not properly formatted")
            beam_index += 1

            # Compute Additional Beam metrics: M
            M = 0
            for cp_metrics in pcm[beam_name]["Sequence"]:
                M = M + cp_metrics["MU"] * cp_metrics["perimeter"] / cp_metrics["area"]
            pcm[beam_name]["M"] = M / pcm[beam_name]["MUbeam"]

            # Compute Additional CP/Beam metrics: AAV
            left_jaws = numpy.asarray(left_jaws)
            right_jaws = numpy.asarray(right_jaws)
            norm_factor = sum(abs(numpy.max(right_jaws, axis=0) - numpy.min(left_jaws, axis=0)))
            for i in range(len(pcm[beam_name]["Sequence"])):
                pcm[beam_name]["Sequence"][i]["AAV"] = \
                    pcm[beam_name]["Sequence"][i]["sumAllApertures"] / norm_factor

            # Compute Additional Beam metrics: MCS
            MCS = 0
            for cp_metrics in pcm[beam_name]["Sequence"]:
                MCS = MCS + cp_metrics["AAV"] * cp_metrics["LSV"] * cp_metrics["MUrel"]
            pcm[beam_name]["MCS"] = MCS

            # Compute Additional Beam metrics: MCSV
            MCSV = 0
            for i in range(len(pcm[beam_name]["Sequence"]) - 1):
                cpi = pcm[beam_name]["Sequence"][i]
                cpi1 = pcm[beam_name]["Sequence"][i + 1]
                MCSV = MCSV + (cpi["AAV"] + cpi1["AAV"]) / 2 * (cpi["LSV"] + cpi1["LSV"]) / 2 * cpi["MUrel"]
            pcm[beam_name]["MCSV"] = MCSV

            # Compute Additional Beam metrics: MFC
            MFC = 0
            for cp_metrics in pcm[beam_name]["Sequence"]:
                MFC = MFC + cp_metrics["area"] * cp_metrics["MUrel"]
            pcm[beam_name]["MFC"] = MFC

            # Compute Additional Beam metrics: BI
            BI = 0
            for cp_metrics in pcm[beam_name]["Sequence"]:
                BI = BI + cp_metrics["MUrel"] * (
                            math.pow(cp_metrics["perimeter"], 2) / (4 * math.pi * cp_metrics["area"]))
            pcm[beam_name]["BI"] = BI

            # Compute Additional Beam metrics: average aperture less than 10mm / 1cm
            aal10 = 0
            for cp_metrics in pcm[beam_name]["Sequence"]:
                if cp_metrics["avgAperture"] <= 10:
                    aal10 = aal10 + 1
            pcm[beam_name]["avgApertureLessThan1cm"] = aal10

            # Compute Additional Beam metrics: average aperture less than 10mm / 1cm
            ydl10 = 0
            for cp_metrics in pcm[beam_name]["Sequence"]:
                if cp_metrics["yDiff"] <= 10:
                    ydl10 = ydl10 + 1
            pcm[beam_name]["yDiffLessThan1cm"] = ydl10

            # Compute Additional Beam metrics: SAS
            SAS = {"nAperturesLeq2": 0, "nAperturesLeq5": 0, "nAperturesLeq10": 0, "nAperturesLeq20": 0}
            for cp_metrics in pcm[beam_name]["Sequence"]:
                for key in SAS:
                    SAS[key] = SAS[key] + cp_metrics[key] / cp_metrics["nAperturesG0"] * cp_metrics["MUrel"]
            pcm[beam_name]["SAS2"] = SAS["nAperturesLeq2"]
            pcm[beam_name]["SAS5"] = SAS["nAperturesLeq5"]
            pcm[beam_name]["SAS10"] = SAS["nAperturesLeq10"]
            pcm[beam_name]["SAS20"] = SAS["nAperturesLeq20"]

        # Computing Plan Metrics
        beams = copy.deepcopy(list(pcm.keys()))
        pcm["plan"] = {}

        MU = 0
        for beam_name in beams:
            MU = MU + pcm[beam_name]["MUbeam"]
        pcm["plan"]["MUplan"] = MU

        M = 0
        for beam_name in beams:
            M = M + pcm[beam_name]["MUbeam"] * pcm[beam_name]["M"]
        pcm["plan"]["Mplan"] = M / MU

        MCS = 0
        for beam_name in beams:
            MCS = MCS + pcm[beam_name]["MUbeam"] * pcm[beam_name]["MCS"]
        pcm["plan"]["MCSplan"] = MCS / MU

        MCSV = 0
        for beam_name in beams:
            MCSV = MCSV + pcm[beam_name]["MUbeam"] * pcm[beam_name]["MCSV"]
        pcm["plan"]["MCSVplan"] = MCSV / MU

        MFC = 0
        for beam_name in beams:
            MFC = MFC + pcm[beam_name]["MUbeam"] * pcm[beam_name]["MFC"]
        pcm["plan"]["MFCplan"] = MFC / MU

        PI = 0
        for beam_name in beams:
            PI = PI + pcm[beam_name]["MUbeam"] * pcm[beam_name]["BI"]
        pcm["plan"]["PI"] = PI / MU

        nCP = 0
        for beam_name in beams:
            nCP = nCP + len(pcm[beam_name]["Sequence"])
        pcm["plan"]["nCP"] = nCP

        al10 = 0
        for beam_name in beams:
            al10 = al10 + pcm[beam_name]["avgApertureLessThan1cm"]
        pcm["plan"]["avgApertureLessThan1cm"] = al10

        yl10 = 0
        for beam_name in beams:
            yl10 = yl10 + pcm[beam_name]["yDiffLessThan1cm"]
        pcm["plan"]["yDiffLessThan1cm"] = yl10

        return pcm

    else:
        print("Supplied file is not an RT_PLAN")

    return None


def complexity_indexes(y12, lj_array: numpy.ndarray, jawSize:int=5):
    """
    Computes complexity indexes over a set of jaws
    :param y12: size of relevant area
    :param lj_array: jaws array
    :param jawSize: size of jaws
    :return:
    """

    minActiveIndex = int(len(lj_array)/4) + int(y12[0] / jawSize)
    maxActiveIndex = int(len(lj_array)/4) + int(y12[1] / jawSize)

    # Pre-Scan of the MLCs
    max_right = -sys.float_info.max
    min_left = sys.float_info.max
    for i in range(minActiveIndex, maxActiveIndex):
        # Computing Aperture
        left = lj_array[i]
        right = lj_array[int(len(lj_array) / 2) + i]
        # Finding minleft / maxright
        if left < min_left:
            min_left = left
        if right > max_right:
            max_right = right
    pos_max =  abs(max_right - min_left)

    # Computing most of the Metrics
    apertures = []
    left_old = 0
    right_old = 0
    lsv_l = 0
    lsv_r = 0
    perimeter = 0

    for i in range(minActiveIndex, maxActiveIndex):
        # Computing Aperture
        left = lj_array[i]
        right = lj_array[int(len(lj_array)/2)+i]
        apertures.append(abs(left - right))
        # Computing LSV iteratively (avoiding the last active control point)
        if i < maxActiveIndex - 1:
            lsv_l = lsv_l + (pos_max - abs(left - lj_array[i+1]))
            lsv_r = lsv_r + (pos_max - abs(right - lj_array[int(len(lj_array)/2)+i+1]))
        # Computing Perimeter iteratively
        ap_i = i - minActiveIndex
        if i == minActiveIndex:
            perimeter += apertures[ap_i]
        else:
            if (right <= left_old) or (left >= right_old):
                # Two apertures do not overlap
                contrib = apertures[ap_i] + apertures[ap_i-1]
            elif (right <= right_old) and (left >= left_old):
                # Old aperture wraps the new one
                contrib = apertures[ap_i-1] - apertures[ap_i]
            elif (right > right_old) and (left < left_old):
                # New aperture wraps the old one
                contrib = apertures[ap_i] - apertures[ap_i-1]
            else:
                # New aperture overlaps + exceeds on the right/left
                contrib = abs(left - left_old) + abs(right - right_old)
            perimeter += contrib
        left_old = left
        right_old = right

    # Finalizing Perimeter
    perimeter += apertures[-1]

    # Finalizing LSV
    lsv = lsv_l*lsv_r/pow(len(apertures)*pos_max, 2)

    # Computing sum of all apertures (active and non active)
    ap_sum = 0
    for i in range(0, int(len(lj_array)/2)):
        left = lj_array[i]
        right = lj_array[int(len(lj_array)/2)+i]
        ap_sum = ap_sum + abs(right - left)

    cm = {
        # Minimum Aperture between aligned MLC
        "minAperture": min(apertures),
        # Maximum Aperture between aligned MLC
        "maxAperture": max(apertures),
        # Maximum Aperture between misaligned MLC
        "maxApertureNoAlign": pos_max,
        # Average Aperture between Active aligned MLCs
        "avgAperture": sum(apertures)/len(apertures),
        # Sum of all apertures (active and non active)
        "sumAllApertures": ap_sum,
        # Size of the window containing active MLCs
        "yDiff": abs(y12[0] - y12[1]),
        # Number of MLCs
        "totalMLC": int(len(lj_array)/2),
        # Number of Active MLCs
        "activeMLC": len(apertures),
        # Active MLC with the lowest index
        "lowestActiveMLC": minActiveIndex,
        # Active MLC with the highest index
        "highestActiveMLC": maxActiveIndex-1,
        # Perimeter of the area exposed to the beam
        "perimeter": perimeter + abs(y12[0] - y12[1])*2,
        # Perimeter of the area exposed to the beam without accounting for MLC thickness
        "perimeterNoMLCSize": perimeter,
        # Area of the area exposed to the beam
        "area": sum(apertures)*jawSize,
        # LSV metric
        "LSV": lsv,
        # Active MLCs which are opened
        "nAperturesG0": sum(ap > 0 for ap in apertures),
        # Active MLCs with aperture lower equal than 2
        "nAperturesLeq2": sum(ap <= 2 for ap in apertures),
        # Active MLCs with aperture lower equal than 5
        "nAperturesLeq5": sum(ap <= 5 for ap in apertures),
        # Active MLCs with aperture lower equal than 10
        "nAperturesLeq10": sum(ap <= 10 for ap in apertures),
        # Active MLCs with aperture lower equal than 20
        "nAperturesLeq20": sum(ap <= 20 for ap in apertures),
        }

    # Complexity measures, left jaws, right jaws
    return cm,  lj_array[0:int(len(lj_array)/2)], lj_array[int(len(lj_array)/2):]


def compute_metrics_stat(pcm, beams):
    cm_array = []
    for beam in beams:
        cm_array.extend(pcm[beam]["Sequence"])
    ms = {}
    for key in list(cm_array[0].keys()):
        num_list = []
        for cm in cm_array:
            num_list.append(cm[key])
        ms[key + "_avg"] = numpy.average(num_list)
        ms[key + "_std"] = numpy.std(num_list)
        ms[key + "_max"] = numpy.max(num_list)
        ms[key + "_min"] = numpy.min(num_list)
        ms[key + "_med"] = numpy.median(num_list)
    return ms
from os import listdir
from os.path import abspath, join
import sys

sys.path.insert(1, abspath(__file__ + 4 * "/..") + "\src")
import pandas as pd
from tqdm import tqdm
from validation.render import ECGRenderer

if __name__ == "__main__":
    INPUT_DIR = r"./validation/PTB-XL/digitized/signal"
    OUTPUT_DIR = r"./validation/PTB-XL/digitized/img"
    ecg_r = ECGRenderer(sample_rate=500, ref_pulse_at_right=True)
    dir_list = listdir(INPUT_DIR)
    for i in tqdm(range(len(dir_list)), desc="Progress"):
        file = dir_list[i]
        file_id = file[0:5]
        path = join(INPUT_DIR, file)
        signals = pd.read_csv(path)
        signals.columns = [
            "I",
            "II",
            "III",
            "aVR",
            "aVL",
            "aVF",
            "V1",
            "V2",
            "V3",
            "V4",
            "V5",
            "V6",
        ]
        output_fname = file_id + ".png"
        ecg_r.render(signals, OUTPUT_DIR + "/" + output_fname)

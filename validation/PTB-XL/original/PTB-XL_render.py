from os import listdir
from os.path import abspath, join
import sys

sys.path.insert(1, abspath(__file__ + 4 * "/.."))
import pandas as pd
from tqdm import tqdm
from validation.render import render

if __name__ == "__main__":
    INPUT_DIR = r"./validation/PTB-XL/original/signal"
    OUTPUT_DIR = r"./validation/PTB-XL/original/img"
    
    dir_list = listdir(INPUT_DIR)
    
    database = pd.read_csv(r"./validation/PTB-XL/ptbxl_database.csv")
    database["patient_id"] = database["patient_id"].astype(int)
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
        
        metadata = database.loc[database["ecg_id"] == int(file_id), :]
        metadata = metadata.astype("str")
        metadata = metadata.to_dict(orient="list")
        metadata = {k:v[0] for k,v in metadata.items()}
        metadata["ecg_id"] = file_id
        
        render(
            signals,
            OUTPUT_DIR + "/" + output_fname,
            sample_rate=500,
            ref_pulse_at_right=True,
            metadata=metadata,
        )

# ECG Miner

The increase in computing power, together with the popularization of algorithms to analyse bioelectrical signals, encourages the computer science community to design and implement software that serves as a support for medical community. 

In this repository we present ECGMiner: A Flexible Software for Accurately Digitizing ECG. The tool works with different ECG formats of 10 seconds duration (25mm/s).

![ecg](https://user-images.githubusercontent.com/68826642/189548326-acfaa335-b87a-4d5b-b4b9-b0f778e90d3b.PNG)


## Setup
1. Git clone this repository
    ```
    git clone https://github.com/adofersan/ecg-miner.git
    ``` 
2. Install Python 3.10.7 and add it to PATH.
3. Install "virtualenv" Python library.
    ```
    pip install virtualenv
    ```
4. Create a virtual environment named "venv" in project root folder.
    ```
    virtualenv venv
    ```
5. Activate the environment

    In Linux/macOS:
    ```
    source venv/bin/activate
    ```

    In Windows:
    ```
    ./venv/Scripts/activate
    ```
6. Install Python packages
    ```
    pip install -r requirements.txt
    ```
7. Build the project
    ```
    pyinstaller ECGMiner.spec
    ```
8. (Optional) Install Tesseract OCR engine to use the metadata extraction feature.

    In Linux/macOS:
    ```
    Install it and add it to the path
    ```

    In Windows:
    ```
    Install it in "C:\Program Files\Tesseract-OCR\tesseract.exe"
    ```

8. Execute the .exe

## ECG image corpus

The repository contains also contains the scripts to render the 12-lead ECG used in validation (see Figure below).

![00449_hr](https://user-images.githubusercontent.com/68826642/185110567-3c5c83e5-4312-4208-ac66-c0c0fc961f3c.png)

## Cites

**PTB-XL publication**

Wagner, P., Strodthoff, N., Bousseljot, R., Samek, W., & Schaeffter, T. (2020). PTB-XL, a large publicly available electrocardiography dataset (version 1.0.0). PhysioNet. https://doi.org/10.13026/qgmg-0d46.

**PTB-XL original publication**

Wagner, P., Strodthoff, N., Bousseljot, R.-D., Kreiseler, D., Lunze, F.I., Samek, W., Schaeffter, T. (2020), PTB-XL: A Large Publicly Available ECG Dataset. Scientific Data. https://doi.org/10.1038/s41597-020-0495-6

**PhysioNet**

Goldberger, A., Amaral, L., Glass, L., Hausdorff, J., Ivanov, P. C., Mark, R., ... & Stanley, H. E. (2000). PhysioBank, PhysioToolkit, and PhysioNet: Components of a new research resource for complex physiologic signals. Circulation [Online]. 101 (23), pp. e215–e220.

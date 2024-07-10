# AAL System  for Elderly Care
*Project for Multimodal Interaction class A.Y. 23-24*

In order to execute the system do the following steps:
1. Install the requirements (```pip3 -r requirements.txt```)
2. Download the model language [vosk-model-small-it-0.22](https://alphacephei.com/vosk/models)
3. Rename the .env.example file in .env and compile it as needed
4. Compile the *patient_registry.csv* file and the files in the *therapy_plan* folder as needed
5. In the root of the project create a folder called *medications* and inside that create a folder for each day of the week (i.e. *monday*, *tuesday*, *wednesday*, *thursday*, *friday*, *saturday*, *sunday*)
5. Execute the script for the bot (```python3 patient_helper.py```)
6. Execute the main application (```python3 app.py```)

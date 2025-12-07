# Install Python dependencies
& "$PSScriptRoot\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$PSScriptRoot\venv\Scripts\pip.exe" install -r "$PSScriptRoot\requirements.txt"


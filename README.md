# Installation/Setup
The current code and setup was tested on Ubuntu 19.01 only, and has been tested on both native Ubuntu and Ubuntu Linux Subsystem for Windows (WSL).

Use Python3, with pip3 installed.

1. Install these packages (just copy-paste them):
   ```
   sudo apt install libgeos-dev
   sudo apt install pkg-config
   sudo apt install tesseract-ocr
   sudo apt install python3-opencv
   sudo apt install python3-tk
   sudo pip3 install -r requirements.txt'
   ```
2. Set up a collection system, such as google forms, to gather screenshots of the scores page
3. Ensure the teams are informed about the guidelines as specified in `Usage`
4. (Depending on the service you're using, this is optional) install [FUSE for Drive](https://github.com/astrada/google-drive-ocamlfuse)
5. cd into the folder through a terminal
6. run `Demo.py`
7. Follow the prompts, which will request you to input various things, such as max. score, graph name, polling interval, and folder (with screenshots) to poll.

# Usage
Users have a suite of rules that need to be followed for optimal results.
- All users on a team use the same account
- The account name and team name should be the same
- The name next to the score should be the same as the name of the file
- The file should be named as the team name
- The files submitted are .jpg or .png, not .jpeg

The teams should upload images with just their team name as the name. For example, a team with the name `"Code Red"` would submit a file with with the name `"Code Red.jpg"`

Google forms, which this program was designed to be used with, saves the files in Drive with the (Google)
user's name as well, so it'll be saved as `"Code Red - [Insert Team Member's Name].jpg"`. The program uses this as an important feature, so please make sure teams are informed of this naming scheme. 

# Administration
Besides setup, there will be a window to run live commands, to ensure smooth operation and allow localized human interference.

The window will look somewhat like this:
<br>
![](https://raw.githubusercontent.com/JEF1056/Comp-Scoreboard/master/tutorial_images/txtbox.PNG)

## Commands
**THIS SECTION IS NOT FINISHED**
```
-r : run the poll immedietly, and update the scores
```

# Generated Example
<iframe> "https://raw.githubusercontent.com/JEF1056/Comp-Scoreboard/master/temp-plot.html" </iframe>
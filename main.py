from flask import Flask, redirect, url_for, render_template, request, send_from_directory
from waitress import serve
import dataset
import os
import json
from colormap import rgb2hex, rgb2hls, hls2rgb
import numpy as np
from werkzeug.utils import secure_filename
from flask_discord import DiscordOAuth2Session, requires_authorization, Unauthorized

app = Flask(__name__)
db = dataset.connect('sqlite:///scoreboard.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
config=json.loads(open("config.json","r").read())
app.secret_key = config["secret_key"]
app.config["DISCORD_CLIENT_ID"] = config["DISCORD_CLIENT_ID"]  # Discord client ID.
app.config["DISCORD_CLIENT_SECRET"] = config["DISCORD_CLIENT_SECRET"]  # Discord client secret.
app.config["DISCORD_REDIRECT_URI"] = config["DISCORD_REDIRECT_URI"]   # Redirect URI.
discord = DiscordOAuth2Session(app)

def hex_to_rgb(hex):
     hex = hex.lstrip('#')
     hlen = len(hex)
     return tuple(int(hex[i:i+hlen//3], 16) for i in range(0, hlen, hlen//3))

def adjust_color_lightness(r, g, b, factor):
    h, l, s = rgb2hls(r / 255.0, g / 255.0, b / 255.0)
    l = max(min(l * factor, 1.0), 0.0)
    r, g, b = hls2rgb(h, l, s)
    return (int(r * 255), int(g * 255), int(b * 255))

def darken_color(tup, factor=0.2):
    r, g, b = tup
    return adjust_color_lightness(r, g, b, 1 - factor)

def scale_teams(ctf_list):
    new_scale=[]
    for value in ctf_list:
        new_scale.append(100*(value/max(ctf_list)))
    return new_scale

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def root():
    teams=db["teams"]
    all_rows=teams.find(id={'>=': 0})
    teams=[]
    ctfs={}
    for row in all_rows:
        teams.append(row["team"])
        for ctf in row:
            if ctf != "id" and ctf !="team":
                if row[ctf] == None:
                    row[ctf]=0
                try:
                    ctfs[ctf].append(row[ctf])
                except:
                    ctfs[ctf] = [row[ctf]]
    color = hex_to_rgb("#"+str(hex(np.random.randint(1056000,16777215)))[2:])
    ctf_fixed=[]
    for ctf in ctfs:
        ctf_fixed.append({"label":ctf, "data":scale_teams(ctfs[ctf]), "backgroundColor":f"rgb{color}"})
        try:
            color=darken_color(color)
        except:
            print(color)
            print(type(color))
    return render_template("scoreboard.html", teams=teams, ctfs=ctf_fixed)

@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for(".login"))

@app.route("/login/")
def login():
  return discord.create_session(scope=["identify", "guilds"])

@app.route("/logout/")
@requires_authorization
def logout():
    discord.revoke()
    return redirect(url_for(".root"))

@app.route("/auth/")
def callback():
  discord.callback()
  return redirect(url_for(".upload"))

@app.route("/upload")
@requires_authorization
def upload():
    config=json.loads(open("../config.json","r").read())["ctfs"]
    return render_template("upload.html", ctfs=config)

@app.route("/upload", methods=["POST"])
@requires_authorization
def upload_accept():
    teams=db["teams"]
    users=db["users"]
    #this would require id'ing a user by discord username
    discord_id=discord.fetch_user()
    team=users.find_one(discord_id=str(discord_id.id))
    if team != None:
        print(request.files)
        file = request.files['screenshot']
        if file.filename == '':
            print('No selected file')
            return {"ERROR": "No screenshot"}
        if file and allowed_file(file.filename):
            try:
                file.save(os.path.join("teams", team['team'], request.form["ctf"]+".png"))
            except:
                os.mkdir(os.path.join("teams", team['team']))
                file.save(os.path.join("teams", team['team'], request.form["ctf"]+".png"))
            if request.form["ctf"].strip()=="":
                return {"ERROR": "CTF name is empty"}
            try:
                int(request.form["score"])
            except:
                return {"ERROR": "Score is not an integer"}
            teams.upsert({"team":team["team"], request.form["ctf"]:int(request.form["score"])}, ["team"], ensure=True)
            return teams.find_one(team=team["team"])
    else:
        return {"ERROR": "ya ain't part of no team!"}

if __name__ == "__main__":
    if os.name == 'nt':
        app.run()
    elif os.name == 'posix':
        serve(app, host=config["host"], port=config["port"], url_scheme='https')
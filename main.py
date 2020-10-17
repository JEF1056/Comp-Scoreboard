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

def darken_color(tup, factor=0.4):
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
    if discord.authorized:
        discord_id=discord.fetch_user()
        users=db["users"]
        team=users.find_one(discord_id=str(discord_id.id))
        if team != None:
            if team["team"] == "Admins" or team["team"] == "Intergalactic Irvin Helpers":
                return render_template("index-authed-admin.html")
            else:
                return render_template("index-authed.html")
        else:
            return {"ERROR":"Team/user not registered"}, 401
    else:
        return render_template("index.html")

@app.route("/scores")
def scores():
    teams=db["teams"]
    all_rows=teams.find(id={'>=': 0})
    teams=[]
    team_totals=[]
    unscaled_team_scores=[0]*(len(all_rows))
    scaled_ctfs=[]
    ctfs={}
    print(unscaled_team_scores)
    for i,row in enumerate(all_rows):
        teams.append(row["team"])
        for ctf in row:
            if ctf != "id" and ctf !="team":
                if row[ctf] == None:
                    row[ctf]=0
                try:
                    ctfs[ctf].append(row[ctf])
                except:
                    ctfs[ctf] = [row[ctf]]
                unscaled_team_scores[i]+=row[ctf]
    color = hex_to_rgb("#"+str(hex(np.random.randint(0,16777215)))[2:])
    ctf_fixed=[]
    for ctf in ctfs:
        ctf_fixed.append({"label":ctf, "data":scale_teams(ctfs[ctf]), "backgroundColor":f"rgb{color+(0.5,)}"})
        scaled_ctfs.append(scale_teams(ctfs[ctf]))
        try:
            color=darken_color(color)
        except:
            print(color)
            print(type(color))
    for i in range(len(teams)):
        scaled_team_total=0
        for val in scaled_ctfs:
            scaled_team_total+=val[i]
        team_totals.append((teams[i], scaled_team_total,unscaled_team_scores[i]))
    team_totals=sorted(team_totals, key=lambda x: x[1])
    return render_template("scoreboard.html", teams=teams, ctfs=ctf_fixed, team_totals=team_totals)

@app.errorhandler(Unauthorized)
def redirect_unauthorized(e):
    return redirect(url_for(".login"))

@app.route("/login/")
def login():
  return discord.create_session(scope=["identify"])

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
    discord_id=discord.fetch_user()
    users=db["users"]
    teams=db["teams"]
    team=users.find_one(discord_id=str(discord_id.id))
    if team != None:
        t_scores=teams.find_one(team=team["team"])
        scores={}
        for ctf in t_scores:
            if ctf != "id" and ctf != team["team"]:
                scores[ctf] = t_scores[ctf]
        config=json.loads(open("./config.json","r").read())["ctfs"]
        return render_template("upload.html", ctfs=config, user=str(discord_id), team=team["team"], scores=scores)
    else:
        return {"ERROR":"Team/User not registered"}, 401

@app.route("/upload", methods=["POST"])
@requires_authorization
def upload_accept():
    teams=db["teams"]
    users=db["users"]
    config=json.loads(open("./config.json","r").read())["ctfs"]
    #this would require id'ing a user by discord username
    discord_id=discord.fetch_user()
    team=users.find_one(discord_id=str(discord_id.id))
    t_scores=teams.find_one(team=team["team"])
    scores={}
    for ctf in t_scores:
        if ctf != "id" and ctf != team["team"]:
            scores[ctf] = t_scores[ctf]
    if team != None:
        print(request.files)
        file = request.files['screenshot']
        errors=[]
        if file.filename == '':
            errors.append("No Screenshot")
        elif file and allowed_file(file.filename):
            try:
                file.save(os.path.join("teams", team['team'], request.form["ctf"]+".png"))
            except:
                os.mkdir(os.path.join("teams", team['team']))
                file.save(os.path.join("teams", team['team'], request.form["ctf"]+".png"))
            if request.form["ctf"].strip()=="":
                errors.append("CTF name is empty")
            if str(request.form["ctf"].strip()) not in config:
                errors.append("CTF does not exist/is not enabled; contact an admin.")
            try:
                int(request.form["score"])
            except:
                errors.append("Score is not an integer")
                return render_template("upload.html", ctfs=config, user=str(discord_id), team=team["team"], scores=scores, errors=errors)
            teams.upsert({"team":team["team"], request.form["ctf"].strip():int(request.form["score"])}, ["team"], ensure=True)
            errors.append("Successfully uploaded a score!")
        else:
            errors.append("Invalid file")
    else:
        errors.append("ya ain't part of no team!")
    t_scores=teams.find_one(team=team["team"])
    for ctf in t_scores:
        if ctf != "id" and ctf != team["team"]:
            scores[ctf] = t_scores[ctf]
    return render_template("upload.html", ctfs=config, user=str(discord_id), team=team["team"], scores=scores, errors=errors)

@app.route("/admin")
@requires_authorization
def admin():
    discord_id=discord.fetch_user()
    users=db["users"]
    team=users.find_one(discord_id=str(discord_id.id))
    if team["team"] == "Admins" or team["team"] == "Intergalactic Irvin Helpers":
        return "heya"
    else:
        return {"ERROR":"100% not authorized"}, 404

@app.route("/admin", methods=["POST"])
@requires_authorization
def admin_accept():
    pass

if __name__ == "__main__":
    if os.name == 'nt':
        app.run()
    elif os.name == 'posix':
        serve(app, host=config["host"], port=config["port"], url_scheme='https')
import discord, json, dataset

intents = discord.Intents(messages=False, guilds=True, typing = False, presences = True, members=True)
client = discord.AutoShardedClient(intents=intents)
config=json.loads(open("config.json","r").read())
db = dataset.connect('sqlite:///scoreboard.db')

@client.event
async def on_ready():
    print('Logged in as '+client.user.name+' (ID:'+str(client.user.id)+') | Connected to '+str(len(client.guilds))+' servers')
    print('--------')
    print("Discord.py verison: " + discord.__version__)
    print('--------')
    print(str(len(client.shards))+" shard(s)")
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Setting up ✨✨"))
    server = client.get_guild(551179402122231828)
    users=db["users"]
    for user in config["teams"]:
        found=False
        for member in server.members:
            if str(member) == str(user):
                found=True
                users.upsert({"discord_id":str(member.id), "team":config["teams"][user]}, ["team"], ensure=True)
        if found==False:
            print(f"{user} not found")
    admins=server.get_role(607677887100747813)
    iih=server.get_role(626544492404539427)
    for member in server.members:
        if admins in member.roles:
            users.upsert({"discord_id":str(member.id), "team":"Admins"}, ["team"], ensure=True)
        elif iih in member.roles:
            users.upsert({"discord_id":str(member.id), "team":"Intergalactic Irvin Helpers"}, ["team"], ensure=True)
    all_rows=users.find(discord_id={'>=': 0})
    for row in all_rows:
        print(row)
    
client.run(config["token"])
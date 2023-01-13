import discord
import requests
import random
import time
import re
import json
import os

# Global variables
token = os.environ.get('RADSOL_TOKEN')
intents = discord.Intents.all()
client = discord.Client(intents=intents)

url = "https://e621.net/posts"
headers = { "accept" : "application/json",
            "user-agent" : "Radsol/1.0 (by Ecila on e621 / Sokks#5000 on Discord)",
            "login" : "Ecila",
            "api_key" : os.environ.get('ESIX_API_KEY')
            }

emb = discord.Embed()
posts = None
idx_start = 0
idx_end = 4

prefixFile = open("prefix.json", 'r')
prefix = json.load(prefixFile)
prefixFile.close()

blacklistFile = open("blacklist.json", 'r')
blacklist = json.load(blacklistFile)
blacklistFile.close()

async def getQuery(query, message):
    global posts
    global idx_start
    global idx_end
    global blacklist

    randomize = False

    if "shuffle" in query:
        randomize = True
        query.remove("shuffle")

    # Check for range and blacklist tags
    for word in query:
        if (word in blacklist[str(message.guild.id)]):
            await message.channel.send("Removed blacklisted tag {}.".format(word))
            query.remove(word)

        if (re.search("[a-zA-Z|_| |=|~|*|:|<|>|\(|\)|\+]", word) == None):
            nums = word.split('-')

            if ('-' in word and (len(nums[1]) == 0 or len(nums[0]) == 0)):
                continue

            if (len(nums) == 1):
                idx_end = int(nums[0])
            elif (len(nums) == 2):
                idx_start = int(nums[0]) - 1
                idx_end = int(nums[1])
            else:
                idx_start = 0
                idx_end = 4
            query.remove(word)
            break
        else:
            idx_start = 0
            idx_end = 4

    for black in blacklist[str(message.guild.id)]:
        query.append('-' + black)

    queryURL = url + ".json?tags=" + "+".join(query)
    response = requests.get(queryURL, headers=headers)

    code = response.status_code
    if code != 200:
        await message.channel.send("Status code {}: {}".format(code, response.json()["message"]))
        posts = None
        return None

    posts = response.json()["posts"]

    if randomize == True:
        random.shuffle(posts)

    return query

async def sendEmbed(query, message):
    if (posts == None):
        return None

    if (len(posts) == 0):
        await message.channel.send("No posts on e6, sorry!")
        return

    await message.channel.send("Gathered {} images".format(len(posts)))
    
    global emb
    global idx_start
    global idx_end

    if (idx_end < idx_start):
        idx_end, idx_start = idx_start, idx_end

    for i in range(max(idx_start, 0), min(idx_end, len(posts))):
        post = posts[i]
        postURL = url + "/" + str(post["id"])

        # Set embed details
        emb.title = "Artists: " + ", ".join(post["tags"]["artist"])
        emb.description = "Post: {}/{}".format(i + 1, len(posts))
        emb.colour = discord.Colour.from_str("#1981AF")
        emb.set_author(name=", ".join(query), icon_url=message.author.avatar.url)
        emb.set_footer(icon_url="http://i.imgur.com/RrHrSOi.png", text="Upvotes: {}".format(post["score"]["up"]))

        # Send embed
        await message.channel.send(postURL)
        await message.channel.send(content=None, embed=emb)
        time.sleep(0.5)

def editBlacklist(tags, key):
    global blacklist

    for tag in tags:
        if len(tag) == 1 or (tag[0] != '-' and tag[0] != '+'):
            continue

        if tag[0] == '-' and tag[1:] in blacklist[key]:
            blacklist[key].remove(tag[1:])

        elif tag[0] == '+' and tag[1:] not in blacklist[key]:
            blacklist[key].append(tag[1:])

    writer = open("blacklist.json", 'w')
    writer.write(json.dumps(blacklist, indent=4))
    writer.close()

@client.event
async def on_message(message):
    # Ignore messages from Radsol
    if message.author == client.user:
        return

    # Default prefix is $ and default blacklist is []
    global prefix
    global blacklist

    if not (str(message.guild.id) in prefix):
        prefix[str(message.guild.id)] = '$'
        writer = open("prefix.json", 'w')
        writer.write(json.dumps(prefix, indent=4))
        writer.close()

    if not (str(message.guild.id) in blacklist):
        blacklist[str(message.guild.id)] = []
        writer = open("blacklist.json", 'w')
        writer.write(json.dumps(blacklist, indent=4))
        writer.close()

    pre = prefix[str(message.guild.id)]

    # Ignore message if it doesn't start with the prefix
    if (not message.content.startswith(prefix[str(message.guild.id)])):
        return

    strings = message.content.split()

    # e621 Command
    if strings[0] == pre + 'e621' or strings[0] == pre + 'e926':
        if (message.channel.nsfw == False) and (strings[0] == pre + 'e621'):
            await message.channel.send("Sorry kiddo, no e621 allowed!")
            return

        # Change url accordingly
        global url
        if (strings[0] == pre + 'e621'):
            url = "https://e621.net/posts"
        else:
            url = "https://e926.net/posts"

        strings.pop(0)

        matches = re.split("[a-zA-Z|\-|_| |=|~|*|:|<|>|\(|\)|0-9|\+]", " ".join(strings))
        for word in matches:
            if len(word) > 0:
                await message.channel.send("sneaky fucker: [a-zA-Z|\-|_| |:|<|>|0-9]")
                return

        if (len(strings) == 0 or strings[0] == 'help'):
            await message.channel.send("Usage: {}'e621/e926 [Tags] [Range]' where [Range] is a single number (n = posts 1 to n) or two numbers separated by a dash (a-b = posts a to b).".format(pre))
            return

        strings = await getQuery(strings, message)
        await sendEmbed(strings, message)
        time.sleep(1)
        return

    # Echo command
    if strings[0] == pre + 'echo':
        strings.pop(0)
        await message.channel.send("\"{}\"".format(" ".join(strings)))
        return

    # Change prefix
    if strings[0] == pre + 'prefix':
        strings.pop(0)

        if (len(strings) == 1):
            prefix[str(message.guild.id)] = strings[0]
            await message.channel.send("New prefix: " + prefix)
        elif (len(strings) == 0):
            prefix[str(message.guild.id)] = ''
            await message.channel.send("Removed prefix")
        else:
            return

        writer = open("prefix.json", 'w')
        writer.write(json.dumps(prefix, indent=4))
        writer.close()
        return

    if strings[0] == pre + 'blacklist':
        strings.pop(0)

        matches = re.split("[a-zA-Z|\-|_| |=|~|*|:|<|>|\(|\)|0-9|\+]", " ".join(strings))
        for word in matches:
            if len(word) > 0:
                await message.channel.send("sneaky fucker")
                return

        if (len(strings) == 0):
            await message.channel.send("Current blacklist: " + ", ".join(blacklist[str(message.guild.id)]))
            await message.channel.send("To add/remove tags, follow the command with +tag or -tag")
        else:
            editBlacklist(strings, str(message.guild.id))


client.run(token)
import discord
import requests
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

prefix = '$'

async def getQuery(query, message):
    global posts
    global idx_start
    global idx_end

    # Check for range
    for word in query:
        if (re.search("[a-zA-Z|_| |:|*|~|=|(|)|<|>]", word) == None):
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
            query.pop(query.index(word))
            break

    queryURL = url + ".json?tags=" + "+".join(query)
    response = requests.get(queryURL, headers=headers)

    code = response.status_code
    if code != 200:
        await message.channel.send("e621 [{}]: {}".format(code, response.json()["message"]))
        posts = None
        return

    posts = response.json()["posts"]

    return query

async def sendEmbed(query, message):
    if (posts == None):
        return

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

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    matches = re.split("[a-zA-Z|\-|_| |=|~|*|:|<|>|(|)|0-9]", message.content)
    strings = message.content.split()

    if strings[0] == prefix + 'e621':
        if message.channel.nsfw == False:
            await message.channel.send("Sorry kiddo, no e621 allowed!")
            return

        for word in matches:
            if len(word) > 0:
                await message.channel.send("sneaky fucker: [a-zA-Z|\-|_| |:|<|>|0-9]")
                return

        strings.pop(0)

        if (len(strings) == 0 or strings[0] == 'help'):
            await message.channel.send("Usage: 'e621 [Tags] [Range]' where [Range] is a single number (n = posts 1 to n) or two numbers separated by a dash (a-b = posts a to b).")
            return

        strings = await getQuery(strings, message)
        await sendEmbed(strings, message)
        time.sleep(1)
        return

    if strings[0] == prefix + 'echo':
        strings.pop(0)
        await message.channel.send("\"{}\"".format(" ".join(strings)))
        return

    if strings[0] == prefix + 'prefix':
        strings.pop(0)
        if (len(strings) == 1):
            prefix = strings[0]
            await message.channel.send("New prefix: " + prefix)
            
        elif (len(strings) == 0):
            prefix = ''
            await message.channel.send("Removed prefix")

        return


client.run(token)
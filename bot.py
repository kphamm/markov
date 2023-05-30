import os
import discord
import markovify
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
MONGODB_URI = os.getenv('MONGODB_URI')

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True

client = discord.Client(intents=intents)

mongo_client = MongoClient(MONGODB_URI)
db = mongo_client['markov']
config_collection = db['config']
messages_collection = db['messages']

async def build_model(channel_id, author_id):
    # Query MongoDB for messages from the specific channel and user
    messages = messages_collection.find({"channel_id": channel_id, "author_id": author_id})
    text = ' '.join([message['content'] for message in messages])
    model = markovify.Text(text)
    return model

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # Store every incoming message to the database

    messages_collection.insert_one({"content": message.content, "channel_id": message.channel.id, "author_id": message.author.id})

    config = config_collection.find_one({"guild_id": message.guild.id})
    # Check if the message is from a channel the bot should learn from
    if config and "channels" in config and message.channel.id in config["channels"]:
        model = await build_model(message.channel.id, message.author.id)
        if model:
            reply = model.make_short_sentence(280)
            if reply:
                await message.channel.send(reply)

client.run(TOKEN)
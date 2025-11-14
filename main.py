from pyrogram import Client, filters
from config import Config
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

bot = Client(
    "bannerbot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)


# ------------- AniList API -------------
def get_anime_data(query):
    url = "https://graphql.anilist.co"
    json_data = {
        "query": """
        query ($search: String) {
          Media(search: $search, type: ANIME) {
            title { romaji }
            description(asHtml: false)
            genres
            averageScore
            coverImage { large }
            seasonYear
          }
        }""",
        "variables": {"search": query}
    }

    res = requests.post(url, json=json_data).json()
    return res["data"]["Media"]


# ------------- Banner Generator -------------
def make_banner(anime):
    bg = Image.new("RGB", (1280, 720), "#111")
    draw = ImageDraw.Draw(bg)

    # Anime image
    img_url = anime["coverImage"]["large"]
    img_data = requests.get(img_url).content
    anime_img = Image.open(BytesIO(img_data)).resize((420, 600))
    bg.paste(anime_img, (820, 60))

    # Fonts
    font_title = ImageFont.truetype("./fonts/Poppins-Bold.ttf", 60)
    font_small = ImageFont.truetype("./fonts/Poppins-Bold.ttf", 32)

    # Header text
    draw.text((40, 20), "ANIME UNIVERSE", fill="#ff0000", font=font_title)

    # Title
    draw.text((40, 120), anime["title"]["romaji"], fill="#ffffff", font=font_title)

    # Genres
    genres = ", ".join(anime["genres"])
    draw.text((40, 210), genres, fill="#ff4444", font=font_small)

    # Score
    draw.text((40, 260), f"Rating: {anime['averageScore']}%", fill="#cccccc", font=font_small)

    # Description
    desc = anime["description"].replace("<br>", "")
    desc = textwrap.fill(desc, 60)
    draw.text((40, 330), desc, fill="#eee", font=font_small)

    output = BytesIO()
    bg.save(output, "JPEG")
    output.seek(0)
    return output


# ------------ COMMANDS -------------
@bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text(Config.START_MSG)


@bot.on_message(filters.command("banner"))
async def banner_cmd(client, message):

    if len(message.command) < 2:
        return await message.reply("Use: /banner anime_name")

    query = " ".join(message.command[1:])
    searching = await message.reply("🔎 Searching anime...")

    try:
        anime = get_anime_data(query)
        banner = make_banner(anime)

        await searching.delete()
        await message.reply_photo(banner, caption="✨ Banner Generated!")
    except Exception as e:
        await searching.edit(f"❌ Error: {e}")


bot.run()

from pyrogram import Client, filters
from config import Config
import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import textwrap

# ------------ BOT CLIENT -------------
bot = Client(
    "bannerbot",
    api_id=Config.API_ID,
    api_hash=Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)


# ------------ AniList API -------------
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


# ------------ Banner Generator (Anime Fury Style) -------------
def make_banner(anime):

    # Canvas
    bg = Image.new("RGB", (1280, 720), "#0c0c0c")
    draw = ImageDraw.Draw(bg)

    # Fonts
    font_big = ImageFont.truetype("./fonts/Poppins-Bold.ttf", 70)
    font_mid = ImageFont.truetype("./fonts/Poppins-Bold.ttf", 38)
    font_small = ImageFont.truetype("./fonts/Poppins-Regular.ttf", 30)

    # ---------------- HEX PATTERN ----------------
    for x in range(0, 1280, 80):
        for y in range(0, 720, 70):
            draw.polygon(
                [(x+40, y), (x+80, y+35), (x+80, y+75),
                 (x+40, y+110), (x, y+75), (x, y+35)],
                outline="#191919"
            )

    # ---------------- RED GRADIENT SHAPES ----------------
    shape = Image.new("RGBA", (500, 500), (255, 0, 0, 90))
    shape = shape.rotate(25, expand=True)
    bg.paste(shape, (-120, -80), shape)
    bg.paste(shape, (900, 260), shape)

    # ---------------- ANIME IMAGE ----------------
    img_url = anime["coverImage"]["large"]
    img_data = requests.get(img_url).content
    anime_img = Image.open(BytesIO(img_data)).resize((420, 600))

    # Rounded mask
    mask = Image.new("L", (420, 600))
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, 420, 600), radius=40, fill=255)

    bg.paste(anime_img, (820, 60), mask)

    # ---------------- TEXT ----------------
    # Header
    draw.text((50, 40), "ANIME UNIVERSE", fill="#ff1a1a", font=font_big)

    # Title
    draw.text((50, 150), anime["title"]["romaji"], fill="#ffffff", font=font_mid)

    # Genres
    genres = ", ".join(anime["genres"])
    draw.text((50, 225), genres, fill="#ff4d4d", font=font_small)

    # Rating
    score = anime.get("averageScore", "N/A")
    draw.text((50, 270), f"Rating: {score}%", fill="#dddddd", font=font_small)

    # Description (short)
    desc = anime["description"].replace("<br>", "")
    desc = textwrap.shorten(desc, width=450, placeholder="...")
    wrapped = textwrap.fill(desc, 50)

    draw.text((50, 330), wrapped, fill="#e8e8e8", font=font_small)

    # Output
    output = BytesIO()
    bg.save(output, "JPEG", quality=95)
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


# ------------ RUN BOT -------------
bot.run()

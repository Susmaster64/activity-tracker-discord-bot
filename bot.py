"""
Does literally everything because cogs are stupid.
"""

# HEHEHE HAW. PYLINT HAS NO POWER OVER ME!!
# pylint: disable=unnecessary-lambda-assignment
# pylint: disable=consider-using-f-string
# pylint: disable=consider-using-dict-items
# TODO:
# 2. Leaderboards
# 3. User report cards.
# 4. Download db.
# 5. God mode (enter raw sql)
# 7. Rows of buttons for days in week.
# 8. Query on historical table?

import time as tim
from datetime import date, timedelta, datetime, time
import discord
from discord.ext import tasks
import aiosqlite
from table2ascii import table2ascii, Alignment, PresetStyle


with open("token.txt", "r", encoding="utf-8") as f:
    token = f.read()

bot = discord.Bot()

START_TIME = int(tim.time())


# Dropdown menuuuuu
class DropdownMenuView(discord.ui.View):
    """
    Jaking my methods. This is dropdown menu, duh.
    """

    def __init__(self, dynamic_options: list[discord.SelectOption], hobby):
        super().__init__()

        select = discord.ui.Select(
            placeholder="Select day to mark as completed.",
            options=dynamic_options,
            min_values=1,
            max_values=len(dynamic_options),
        )
        self.hobby = hobby
        select.callback = self.select_callback

        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        """
        Callback for when the selected the thingy.
        """
        # I think this works????
        value = interaction.data["values"]
        # This gets a list?????????????? Of responses? From the dictionary??? In terms of weekdays??

        with open("date_this_week_started_on.txt", "r", encoding="utf-8") as foole:
            week_start_day = foole.read()
        week_start_day = datetime.strptime(week_start_day, "%Y-%m-%d")
        # Hacky reverse day thingy.
        day_dict = {
            (week_start_day + timedelta(days=i))
            .strftime("%A"): (week_start_day + timedelta(days=i))
            .strftime("%Y-%m-%d")
            for i in range((datetime.today() - week_start_day).days + 1)
        }
        for n in value:
            await complete_hobby_db(
                interaction.user.id,
                str(interaction.user),
                self.hobby,
                day_dict[n],
            )

        await interaction.response.send_message(
            f"""
            Dates for {self.hobby} marked as completed: {value}.
-# ◉ Note that because of my dumpsterfire code, \
you cannot yet deselect to remove. \
To remove, use /remove.
            """,
            ephemeral=True,
        )


# Body snatcher, button catcher.
class LeButton(discord.ui.Button):
    """
    Dynamoc buttons for each hobby? What is this magic.
    """

    def __init__(self, label: str):
        style = discord.ButtonStyle.primary
        if label == "Help" or label == "Get Your Stats!":
            style = discord.ButtonStyle.secondary
        super().__init__(label=label, style=style, custom_id=f"btn_{label}")

    async def callback(self, interaction: discord.Interaction):

        with open("date_this_week_started_on.txt", "r", encoding="utf-8") as foole:
            week_start = foole.read()

        week_start = datetime.strptime(week_start, "%Y-%m-%d")
        # Imagine this, but in one line. Thank you black for formatting.
        options = [
            discord.SelectOption(
                label=option_weekday,
                description="Select to mark this day as completed.",
            )
            for option_weekday in [
                (week_start + timedelta(days=i)).strftime("%A")
                for i in range((datetime.today() - week_start).days + 1)
            ]
        ]
        # Help message
        # TODO
        if self.label == "Help":
            await interaction.response.send_message(
                """
For regular users, just play around with the buttons and drowdown menus in the leaderboard message.
The blue buttons are the activities that you can mark as done.
For admins, consult the documentation at 
            """,
                ephemeral=True,
            )

        # STATS CARD. SHOULD BE EASY???
        elif self.label == "Get Your Stats!":
            completed_dates_dict = await get_user_stats(str(interaction.user.id))
            completed_dates_as_weekdays_dict = {}
            keys = []
            # Keys in dict.
            for key in completed_dates_dict:
                completed_dates_as_weekdays_dict[key] = [
                    datetime.strptime(specific_day, "%Y-%m-%d").strftime("%A")
                    for specific_day in completed_dates_dict[key]
                ]
                keys.append(key)

            row = []
            rows = []
            list_of_weekdays = [
                (week_start + timedelta(days=i)).strftime("%A")
                for i in range((datetime.today().date() - week_start.date()).days + 1)
            ]
            # I hate myself
            for h in keys:
                for n in list_of_weekdays:
                    if n in completed_dates_as_weekdays_dict[h]:
                        row.append("🟩")
                    else:
                        row.append("🟥")
                row = [h] + row
                rows.append(row)
                row = []

            completion_table = table2ascii(
                # Programming warcrimes 101
                header=["Thingy"]
                + [
                    (week_start + timedelta(days=i)).strftime("%A")
                    for i in range(
                        (datetime.today().date() - week_start.date()).days + 1
                    )
                ],
                # I swear this is possible in a single list comprehension but ????
                body=rows,
                style=PresetStyle.double_thin_box,
                first_col_heading=True,
                alignments=Alignment.LEFT,
            )
            await interaction.response.send_message(
                "Your progress this week:\n```"
                + completion_table
                + "```\n-# More stats coming in the future maybe.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                f"""Select all the days you want to mark as completed for {self.label}. \
(You may select multiple.)""",
                view=DropdownMenuView(options, self.label),
                ephemeral=True,
            )


class ViewForLeButton(discord.ui.View):
    """
    Buttons. Happy?
    """

    def __init__(self, buttons):
        super().__init__()
        for label in buttons:
            self.add_item(LeButton(label))


@bot.event
async def on_ready():
    """
    Bot is ready. SQL be guuci.
    """
    print("I FEEL ALIVE AS FUCK")
    # SQL DO YOUR MAGIC
    async with aiosqlite.connect("hobby.db") as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS hobby_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                username TEXT NOT NULL,
                hobby_name TEXT NOT NULL,
                date TEXT NOT NULL
            )
        """
        )
        await db.commit()
    print("SQL DONE!")


@bot.command(
    description="Technical information about the (current) bot (session). Developer only."
)
async def techinfo(ctx):
    """
    Gets technical info.
    """
    # Developer command
    if ctx.author.id == 567962682154680322:
        await ctx.respond(
            f"Online since: <t:{START_TIME}:R>. (<t:{START_TIME}:f>)\nLatency: {bot.latency}s"
        )
    else:
        await ctx.respond("Nuh uh.", ephemeral=True)


@bot.command(description="Initialises database for historical record. Developer only.")
async def historicalinit(ctx):
    """
    Discord command for init of historical db.
    """
    # Deggegor commend or smuthin idk.
    if ctx.author.id == 567962682154680322:
        await initialise_historical_db()
        await ctx.respond("Historical table initialisation complete.")
    else:
        await ctx.respond("Nuh uh.", ephemeral=True)


@bot.command(
    description="Begins a new week and outputs last week's results. Admin only."
)
async def startweek(ctx):
    """
    Begins a new week
    """
    with open("date_this_week_started_on.txt", "w", encoding="utf-8") as foole:
        foole.write(str(date.today()))

    # FUCK
    # Uhhhhhhhhhhhhhhhhhhhhh can I get uhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh.
    if ctx.author.id == 567962682154680322 or ctx.author.id == 1090778405332602891:

        embed = discord.Embed(
            title="The results are in!",
            description=f"""
            Today is {str(date.today())}.\
            This week is predicted to end \
            <t:{int(datetime.combine(datetime.today(), time()).timestamp()) + 604801}:R>.\
             """,
            color=discord.Colour.green(),
        )
        # Just put this here because im lazy, ordinal is taken from some code golf guy idk.
        # This is brain damage
        ordinal = lambda n: "%d%s" % (
            n,
            "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
        )
        # goofy ahhh
        result = ""
        n = 1
        # Could do some while user id is not none, but then idk yes.
        while True:
            user_id = await get_nth_place_for_hobby("overall", n)
            if user_id is None:
                break
            result += f"{ordinal(n)}: {user_id[1]} with **{user_id[2]}** completions.\n"
            n += 1

        embed.add_field(
            name="This week's scores!",
            value=result,
        )

        embed.add_field(name="ㅤ", value="ㅤ", inline=True)
        embed.add_field(name="ㅤ", value="ㅤ", inline=True)

        # This is here because yes.
        with open("hobbies.txt", "r", encoding="utf-8") as foole:
            existing_hobbies = set(
                line.strip().lower() for line in foole if line.strip().lower()
            )

        for specific_hobby in existing_hobbies:

            result = ""
            n = 1
            while True:
                user_id = await get_nth_place_for_hobby(specific_hobby, n)
                if user_id is None:
                    break
                result += (
                    f"{ordinal(n)}: {user_id[1]} with **{user_id[2]}** completions.\n"
                )
                n += 1

            embed.add_field(
                name=f"Final results for {specific_hobby}.",
                value=result,
                inline=True,
            )

        embed.set_footer(text="If something is broken, ping @Bigbing.")
        embed.set_author(name="Final results!")

        await ctx.respond(embed=embed)
        await move_entries_to_historical_and_clear()
    else:
        await ctx.respond(
            "Nuh uh. But if you are someone who needs access to this command. Ping Bigbing",
            ephemeral=True,
        )


@bot.command(description="Create new hobby. Admin only.")
async def createhobby(ctx, hobby: str):
    """
    Creates a hobby category.
    """
    # Admin only command or something idk
    # could be easier with classes by OOP make me wanna wahoooooo. Second user ID is aqui's
    if ctx.author.id == 567962682154680322 or ctx.author.id == 1090778405332602891:

        with open("hobbies.txt", "r", encoding="utf-8") as foole:
            # This is disgusting
            existing_hobbies = set(
                line.strip().lower() for line in foole if line.strip().lower()
            )

        if hobby.lower().strip() in existing_hobbies:
            await ctx.respond(f"Hobby {hobby} already exists.")
        else:
            with open("hobbies.txt", "a", encoding="utf-8") as foole:
                foole.write("\n" + hobby + "\n")
            await ctx.respond(f"Created hobby {hobby}.")

    else:
        await ctx.respond("Nuh uh. This not for you to use.", ephemeral=True)


@bot.command(description="Remove an existing hobby. Admin only.")
async def removehobby(ctx, hobby: str):
    """
    Removes a hobby category.
    """
    # Admin only command or something idk
    # could be easier with classes by OOP make me wanna wahoooooo.
    if ctx.author.id == 567962682154680322 or ctx.author.id == 1090778405332602891:

        with open("hobbies.txt", "r", encoding="utf-8") as foole:
            # This is disgusting
            existing_hobbies = set(
                line.strip().lower() for line in foole if line.strip().lower()
            )

        if hobby.lower().strip() not in existing_hobbies:
            await ctx.respond(f"Hobby {hobby} doesn't exist.")
        else:
            with open("hobbies.txt", "w", encoding="utf-8") as foole:
                existing_hobbies.remove(hobby)
                foole.write("\n".join(existing_hobbies))
            await ctx.respond(f"Removed hobby {hobby}.")

    else:
        await ctx.respond("Nuh uh. This not for you to use.", ephemeral=True)


@bot.command(description="Lists available hobbies.")
async def listhobbies(ctx):
    """
    Gets all existing hobbies.
    """
    with open("hobbies.txt", "r", encoding="utf-8") as foole:
        existing_hobbies = set(
            line.strip().lower() for line in foole if line.strip().lower()
        )

    await ctx.respond(f"All hobbies: {str(existing_hobbies)}", ephemeral=True)


@bot.command(
    description="Mark activity complete for a date. Date format is yyyy-mm-dd."
)
async def complete(
    ctx,
    hobby: str,
    day: discord.Option(
        str, autocomplete=discord.utils.basic_autocomplete(["Today", "Yesterday"])
    ),
):
    """
    Marks a specific date for a hobby to be completed.
    """

    with open("hobbies.txt", "r", encoding="utf-8") as foole:
        existing_hobbies = set(
            line.strip().lower() for line in foole if line.strip().lower()
        )

    if day == "Today":
        day = str(date.today())
    elif day == "Yesterday":
        day = str(date.today() - timedelta(days=1))
    elif check_date_valid(day):
        pass
    else:
        await ctx.respond(
            "Invalid date(s). Date format is yyyy-mm-dd. Also, no time travelling.",
            ephemeral=True,
        )
        return
    if hobby.lower().strip() in existing_hobbies:
        await complete_hobby_db(str(ctx.author.id), str(ctx.author), hobby, day)
        await ctx.respond(
            f"Successfully marked selected days completed for {hobby}.", ephemeral=True
        )
    else:
        await ctx.respond(
            f"Invalid hobbies. Please enter one from {existing_hobbies}", ephemeral=True
        )


@bot.command(description="Unmarks specified day as complete.")
async def remove(
    ctx,
    hobby: str,
    day: discord.Option(
        str, autocomplete=discord.utils.basic_autocomplete(["Today", "Yesterday"])
    ),
):
    """
    Unmarks specified day as completed.
    """
    with open("hobbies.txt", "r", encoding="utf-8") as foole:
        existing_hobbies = set(
            line.strip().lower() for line in foole if line.strip().lower()
        )

    if day == "Today":
        day = str(date.today())
    elif day == "Yesterday":
        day = str(date.today() - timedelta(days=1))
    elif check_date_valid(day):
        pass
    else:
        await ctx.respond(
            "Invalid date(s). Date format is yyyy-mm-dd. Also, no time travelling.",
            ephemeral=True,
        )
        return
    if hobby.lower().strip() in existing_hobbies:
        await remove_completion_db(str(ctx.author.id), hobby, day)
        await ctx.respond(
            f"Successfully unmarked selected days completed for {hobby}.",
            ephemeral=True,
        )
    else:
        await ctx.respond(
            f"Invalid hobbies. Please enter one from {existing_hobbies}", ephemeral=True
        )


@bot.command(description="Starts loop for global report. Developer only.")
async def startreportloop(ctx):
    """
    Starts the loop for the global report card.
    """
    if ctx.author.id == 567962682154680322:
        refresh_report.start()
        await ctx.respond("Loop task started", ephemeral=True)
    else:
        await ctx.respond(
            "You do not have the nessicary permissions to use this command.",
            ephemeral=True,
        )


@tasks.loop(seconds=30)
async def refresh_report():
    """
    Task to automatically refresh global reportcard/leaderboard in the specified channel.
    """
    channel = bot.get_channel(1371419474229592124)
    embed = discord.Embed(
        title="Leaderboards",
        description=f"""
        Today is {str(date.today())}.\
        Tomorrow start <t:{int(datetime.combine(datetime.today(), time()).timestamp()) + 86400}:R>.\
         """,
        color=discord.Colour.blurple(),
    )
    # Just put this here because im lazy, ordinal is taken from some cold golf guy idk.
    # This is brain damage
    ordinal = lambda n: "%d%s" % (
        n,
        "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10 :: 4],
    )
    # goofy ahhh
    result = ""
    n = 1
    # Could do some while user id is not none, but then idk yes.
    while True:
        user_id = await get_nth_place_for_hobby("overall", n)
        if user_id is None:
            break
        result += f"{ordinal(n)}: {user_id[1]} with **{user_id[2]}** completions.\n"
        n += 1

    embed.add_field(
        name="Current Overall Weekly Leaderboards",
        value=result,
    )

    embed.add_field(name="ㅤ", value="ㅤ", inline=True)
    embed.add_field(name="ㅤ", value="ㅤ", inline=True)
    # This is here because yes.
    with open("hobbies.txt", "r", encoding="utf-8") as foole:
        existing_hobbies = set(
            line.strip().lower() for line in foole if line.strip().lower()
        )
    for specific_hobby in existing_hobbies:
        result = ""
        n = 1
        while True:
            user_id = await get_nth_place_for_hobby(specific_hobby, n)
            if user_id is None:
                break
            result += f"{ordinal(n)}: {user_id[1]} with **{user_id[2]}** completions.\n"
            n += 1
        if result == "":
            result = (
                f"Complete {specific_hobby} today to become number 1 in this category!"
            )
        embed.add_field(
            name=f"Current standings for {specific_hobby}.",
            value=result,
            inline=True,
        )

    embed.set_footer(
        text="""If something is broken, ping @Bigbing. \
This updates every 30s.
If you get pings when this updates, mute the channel."""
    )
    embed.set_author(name="Leaderboards!")

    # Future image support for graphs??
    # embed.set_thumbnail(url="")
    # embed.set_image(url="")

    buttons = list(existing_hobbies)
    buttons.append("Help")
    buttons.append("Get Your Stats!")

    await channel.send(embed=embed, delete_after=30, view=ViewForLeButton(buttons))


def check_date_valid(date_str):
    "Check if given date is in the valid format and is in a reasonable timeframe."
    try:
        checked_date = datetime.strptime(date_str, "%Y-%m-%d")
        return datetime(2020, 1, 1) <= checked_date <= date.today()
    except ValueError:
        return False


async def complete_hobby_db(user_id: str, user_name: str, hobby: str, day: str):
    """
    Adds entry into database for hobby completed on that day for a user.
    """
    async with aiosqlite.connect("hobby.db") as db:
        await db.execute(
            """
            INSERT INTO hobby_entries (user_id, username, hobby_name, date)
            VALUES (?, ?, ?, ?)
        """,
            (user_id, user_name, hobby, day),
        )
        await db.commit()


async def remove_completion_db(user_id: str, hobby: str, date_str: str):
    """
    Removes entries.
    """
    async with aiosqlite.connect("hobby.db") as db:
        await db.execute(
            """
            DELETE FROM hobby_entries
            WHERE user_id = ? AND hobby_name = ? AND date = ?
        """,
            (user_id, hobby, date_str),
        )
        await db.commit()


async def initialise_historical_db():
    """
    Generates the table for the historical database.
    """
    async with aiosqlite.connect("hobby.db") as db:
        await db.execute(
            """
            CREATE TABLE historical_entries AS
            SELECT * FROM hobby_entries WHERE 0;
            """
        )
        await db.commit()


async def move_entries_to_historical_and_clear():
    """
    DB actions for beginning new week.
    """
    async with aiosqlite.connect("hobby.db") as db:
        await db.execute(
            """
            INSERT INTO historical_entries
            SELECT * FROM hobby_entries;
            """
        )
        await db.commit()
        # Deletion because it can only do one command at a time???
        await db.execute(
            """
            DELETE FROM hobby_entries;
            """
        )
        await db.commit()


async def get_user_stats(user_id: str):
    """
    Returns various stats for specified user as dictionary.
    Includes: dates of this week completed for every hobby and  NO Streaks.
    """
    async with aiosqlite.connect("hobby.db") as db:
        # Add streaks in the future maybe idk im kinda a dummy.
        # list of dates that each hobby is completed
        # max days in a row completed for every hobby.
        # UNIQUE ONLY

        with open("hobbies.txt", "r", encoding="utf-8") as foole:
            existing_hobbies = set(
                line.strip().lower() for line in foole if line.strip().lower()
            )
        user_stats_dict = {}
        for hobby in existing_hobbies:
            async with db.execute(
                """
                SELECT DISTINCT date, hobby_name, user_id
                FROM hobby_entries
                WHERE hobby_name = ?
                  AND user_id = ?;
            """,
                (hobby, user_id),
            ) as cursor:
                rows = await cursor.fetchall()
                dates = [row[0] for row in rows]

            user_stats_dict[hobby] = dates
        return user_stats_dict


async def get_nth_place_for_hobby(hobby: str, place: int):
    """
    Gets the user currently in nth place
    """

    if hobby == "overall":
        async with aiosqlite.connect("hobby.db") as db:
            async with db.execute(
                """
        SELECT user_id, username, n
        FROM (
            SELECT user_id, username, COUNT(*) as n
            FROM (
                SELECT DISTINCT user_id, hobby_name, date FROM hobby_entries
            )
            GROUP BY user_id
            ORDER BY n DESC
            LIMIT 1 OFFSET ?
        );
        """,
                (place - 1,),
            ) as cursor:
                row = await cursor.fetchone()
                return row if row else None
    else:
        async with aiosqlite.connect("hobby.db") as db:
            async with db.execute(
                """
                SELECT user_id, username, n
                FROM (
                    SELECT user_id, username, COUNT(*) as n
                    FROM (
                        SELECT DISTINCT user_id, hobby_name, date FROM hobby_entries
                        WHERE hobby_name = ?
                    )
                    GROUP BY user_id
                    ORDER BY n DESC
                    LIMIT 1 OFFSET ?
                );
                """,
                (hobby, place - 1),
            ) as cursor:
                row = await cursor.fetchone()
                return row if row else None


bot.run(token)

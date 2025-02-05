import discord
import requests
from PIL import Image, ImageDraw
from fuzzywuzzy import fuzz
from data_preprocessing import *
import aiofiles

# Dragon Ravine of Dawn
GUILD_ID = '1225054729101377557'
# Color code for discord embed that match the units element
unit_themes = {'Light': 0xFFFF00, 'Fire': 0xFF0000, 'Water': 0x0000FF, 'Dark': 0x800080, 'Wind': 0x00FF00}
# Emoji id for units position
position_emojis = {'Vanguard': '<:frontline:1197603215185817682>', 'Midguard': '<:midline:1197603217484283944>', 'Rearguard': '<:backline:1197603211884888184>'}
# Emoji id for units skills
skill_emojis = {'Attack' :'<:AA:1197742933332463687>', 'Skill 1': '<:S1:1197770562940964904>', 'Skill 2': '<:S2:1197770561292615790>', 'EX Skill': '<:EX:1197770566007001088>',
                'SP 1': '<:L1:1197770578019504188>', 'SP 2': '<:L2:1197770576182394942>', 'SP 3': '<:L3:1197770572998918235>', 'SP Skill': '<:L:1197770569920294952>', 'SP': '<:L:1197770569920294952>'}
# List of units data (each entry is a dict holding many keys)
units_data = []
# Units index cache (key will be an units nickname, value will be its index in units_data)
units_index = {}
# List of units nickname (each entry is a string)
units = []
# Stored checksum to check for changes in sheet
checksum = None

async def check_for_update():
    global checksum
    current_data = fetch_data()
    if current_data:
        current_checksum = hashlib.md5(current_data).hexdigest()

        if not checksum or current_checksum != checksum:
            checksum = current_checksum
            await data_loading(current_data, option=1)
            print('Data loaded!')
        else:
            print('No changes detected in database!')
    else:
        await data_loading(option=2)
        print('Database not available at the moment!')

# Load data 
async def data_loading(data=None, option=1):
    global units_data, checksum
    if option == 1:
        units_data, checksum = preprocess_data(data)
    elif option == 2 and not units_data:
        await load_data_from_file()
        print('Data loaded from backup file!')
    await cache_units_data()

async def load_data_from_file():
    global units_data
    async with aiofiles.open('data.json', 'r') as file:
        units_data = json.loads(await file.read())

async def cache_units_data():
    global units, units_index
    if not (units and units_index):
        for i, unit in enumerate(units_data):
            nickname = unit.get('Nickname')
            units_index[nickname.lower()] = i
            units.append(nickname)

# Replace a dict key appearance in a given string with its value
def replace_keys_with_values(pattern: str):
    for key, value in skill_emojis.items():
        pattern = pattern.replace(key, value)
    return pattern

# Return discord embed with review of a given unit
def unit_review(unit_name: str):
    unit_data = None
    index = 0
    similarity_scores = []

    # Check if units name already cached
    if unit_name in units_index:
        unit_data = units_data[units_index[unit_name]]
    # If not cached iterare through every units name and store their similarity to the provided name
    else:
        for data in units_data:
            similarity_scores.append((similarity(unit_name, data['Nickname']), index))
            index += 1

    # Pick the unit with the most similarity and cache the result
    if not unit_data:
        similarity_scores = sorted(similarity_scores, reverse=True)
        unit_data = units_data[similarity_scores[0][1]]
        units_index[unit_name] = similarity_scores[0][1] 

    total_stars = 5

    if unit_data['Union Burst+'] and unit_data['Union Burst+'] != '-':
        total_stars = 6

    # Calculate the right number of stars to display on embed
    original_stars = '<:normal_star:1197600610359443477>' * unit_data['Rarity'].count('\u2605')
    stars_left = '<:no_star:1197600606915932251>' * (total_stars - unit_data['Rarity'].count('\u2605'))
    # Units position, name and stars  
    contents = f"{position_emojis[unit_data['Position']]} **{unit_data['Name']}** {original_stars}{stars_left}"
    # Units initial movement
    initial_movement = replace_keys_with_values(' '.join(''.join(unit_data['Initial Movement']).replace('\u2192', '').split()))
    # Units loop pattern
    loop_pattern = replace_keys_with_values(' '.join(''.join(unit_data['Loop Pattern']).replace('\u2192', '').split()))
    contents += f"\n\n**Initial Movement:** \n{initial_movement}\n**Loop Pattern:** \n{loop_pattern}"
    # Units UB initial movement 
    if unit_data['UB Initial Movement']:
        ub_initial_movement = replace_keys_with_values(' '.join(''.join(unit_data['UB Initial Movement']).replace('\u2192', '').split()))
        contents += f"\n**UB Initial Movement:** \n{ub_initial_movement}"
    # Units UB loop pattern
    if unit_data['UB Loop Pattern']:
        ub_loop_pattern = replace_keys_with_values(' '.join(''.join(unit_data['UB Loop Pattern']).replace('\u2192', '').split()))
        contents += f"\n**UB Loop Pattern:** \n{ub_loop_pattern}"
    # Units UB
    contents += f"\n\n<:UB:1197778528117203055> **({unit_data['Union Burst']}): **{unit_data['Union Burst Description']}"
    # Units ascended UB
    if unit_data['Union Burst+'] and unit_data['Union Burst+'] != '-':
        contents += f"\n<:ascend_star:1197600612360138923> **({unit_data['Union Burst+']}): **{unit_data['Union Burst+ Description']}"
    # Units skill 1
    contents += f"\n\n{skill_emojis['Skill 1']} **({unit_data['Skill 1']}): **{unit_data['Skill 1 Description']}"
    # Units skill 1 with UE 1 equipped
    if unit_data['Skill 1+'] and unit_data['Skill 1+'] != '-':
        contents += f"\n<:UE1:1197778523931291688> **({unit_data['Skill 1+']}): **{unit_data['Skill 1+ Description']}"
    # Units skill 2
    contents += f"\n\n{skill_emojis['Skill 2']} **({unit_data['Skill 2']}): **{unit_data['Skill 2 Description']}"
    # Units skill 2 with UE 2 equipped
    if unit_data['Skill 2+'] and unit_data['Skill 2+'] != '-':
        contents += f"\n<:UE2:1197778522148700251> **({unit_data['Skill 2+']}): **{unit_data['Skill 2+ Description']}"
    # Units special skill 1
    if unit_data['SP 1'] and unit_data['SP 1'] != '-':
        contents += f"\n\n{skill_emojis['SP 1']} **({unit_data['SP 1']}): **{unit_data['SP 1 Description']}"
    # Units special skill 1 with UE 1 equipped
    if unit_data['SP 1+'] and unit_data['SP 1+'] != '-':
        contents += f"\n<:UE1:1197778523931291688> **({unit_data['SP 1+']}): **{unit_data['SP 1+ Description']}"
    # Units special skill 2
    if unit_data['SP 2'] and unit_data['SP 2'] != '-':
        contents += f"\n\n{skill_emojis['SP 2']} **({unit_data['SP 2']}): **{unit_data['SP 2 Description']}"
    # Units special skill 2 with UE 2 equipped
    if unit_data['SP 2+'] and unit_data['SP 2+'] != '-':
        contents += f"\n<:UE2:1197778522148700251> **({unit_data['SP 2+']}): **{unit_data['SP 2+ Description']}"
    # Units special skill 3 (currently there is no UE 3 in game)
    if unit_data['SP 3'] and unit_data['SP 3'] != '-':
        contents += f"\n\n{skill_emojis['SP 3']} **({unit_data['SP 3']}): **{unit_data['SP 3 Description']}"
    # Units special skill
    if unit_data['SP Skill'] and unit_data['SP Skill'] != '-':
        contents += f"\n\n<:SP:1197770569920294952> **({unit_data['SP Skill']}): **{unit_data['SP Skill Description']}"
    # Units EX skill
    contents += f"\n\n{skill_emojis['EX Skill']} **({unit_data['EX Skill']}): **{unit_data['EX Skill Description']}"
    # Units UE 1 information
    if unit_data['Unique Equipment 1'] and unit_data['Unique Equipment 1'] != '-' and unit_data['Unique Equipment 1'] != 'Coming Soon!':
        contents += f"\n\n<:UE1:1197778523931291688> **({unit_data['Unique Equipment 1']}):** {', '.join(unit_data['Unique Equipment 1 Stats'])}"
    # Units UE 2 information
    if unit_data['Unique Equipment 2'] and unit_data['Unique Equipment 2'] != '-' and unit_data['Unique Equipment 2'] != 'Coming Soon!':
        contents += f"\n<:UE2:1197778522148700251> **({unit_data['Unique Equipment 2']}):** {', '.join(unit_data['Unique Equipment 2 Stats'])}"
    # Page 1 of the embed (general information of unit)
    # Units element reflected via embeds color
    page1 = discord.Embed(description=contents, color=unit_themes[unit_data['Element']])
    # Page 2 of the embed (detailed review of unit)
    if unit_data['Review']:
        page2 = discord.Embed(description=f"{position_emojis[unit_data['Position']]} **{unit_data['Name']}** {original_stars}{stars_left}\n\n**Review:**" + ', '.join(unit_data['Review'].split(',')),
                              color=unit_themes[unit_data['Element']])
        page2.set_footer(text='Page 2 of 2  / Based on aSadArtist\'s guide')
        page1.set_footer(text='Page 1 of 2 / Based on aSadArtist\'s guide')
        return [page1, page2]
    else:
        page1.set_footer(text='Based on aSadArtist\'s guide')
        return page1

# Return similar score of 2 given string using wuzzyfuzzy algorithm
def similarity(str1: str, str2: str):
    return fuzz.WRatio(str1, str2)

# Return strings to be used for discord embed fields value, the strings will represent units name sorted alphabetically
# Discord only support 3 embeds inline with each other
def unit_columns(units, num_columns=3):
    # Sort the names of units alphabetically
    units.sort()

    # Calculate the number of rows needed to spread the units name evenly across 3 columns
    num_rows = len(units) // num_columns
    if len(units) % num_columns:
        num_rows += 1

    # Each list will hold all the units name of a column
    field_values = [[] for _ in range(num_columns)]

    # Adding units name to lists
    for i in range(num_rows):
        for j in range(num_columns):
            if i + j * num_rows < len(units):
                unit_name = units[i + j * num_rows]
                field_values[j].append(unit_name)

    # Convert lists in to strings
    for i in range(len(field_values)):
        field_values[i] = '\n'.join(field_values[i]).rstrip()

    return field_values

# Utility method to work with images, specifically overlaying an image on top of another
def image_utility(url: str, option=1):
    # Get discord users pfp as png then resize it accordingly
    image = Image.open(io.BytesIO(requests.get(url).content))
    image = image.resize((160, 160))

    # Add alpha channel
    if image.mode != 'RGBA':
        image = image.convert('RGBA')

    # Draw a mask the size of image
    mask = Image.new('L', image.size, 0)
    draw = ImageDraw.Draw(mask)

    # Draw an ellipse to the mask
    draw.ellipse((0, 0) + image.size, fill=255)

    # Rounded pfp is obtained from overlaying mask on original image
    rounded_image = Image.new('RGBA', image.size)
    rounded_image.paste(image, (0, 0), mask)

    # Return the image to be used for /pat command
    if option==2:
        return rounded_image
    
    # Additional images to work with
    nozomi = Image.open('Images/nozomibless.png')
    overlay = Image.open('Images/overlay.png')
    overlay = overlay.resize((160, 160))

    # Add alpha channel
    if overlay.mode != 'RGBA':
        overlay = overlay.convert('RGBA')

    # Overlay the images accordingly, nozomi <- rounded pfp <- overlay
    nozomi.paste(rounded_image, (75, 195), rounded_image)
    nozomi.paste(overlay, (75, 195), overlay)

    # Write the image to a byte array to avoid saving
    byte_array = io.BytesIO()
    nozomi.save(byte_array, format='PNG')
    byte_array.seek(0)

    return byte_array
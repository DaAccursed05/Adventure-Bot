import discord
from discord.ext import commands
import newfile
import class_descriptions
import random
import sqlite3
import asyncio

conn = sqlite3.connect('database.db')	
conn.execute("PRAGMA foreign_keys = 1")	
def read_token ():
	with open("token.txt", "r") as f:
		lines = f.readlines()
		return lines[0].strip()
		
# Read the token
token = read_token()
AdventBot = commands.Bot(command_prefix = '--')

categlist = ["Cleric", "Knight", "Barbarian", "Castellan", "Hunter"]

#So that we know when our sweet bot is ready
@AdventBot.event
async def on_ready():
	print('Let\'s do this')
	
@AdventBot.command()
async def intro(ctx):
	await ctx.channel.send('Hello, thank you for adding me to your server. I am a bot framework specially made for playing games with people, especially RPG ones. \n You may start playing rn or do the ```--help``` to get the help prompt.')

#Joining commands so it works well
@AdventBot.command()
async def join(ctx, category):
	#Database init
	c = conn.cursor()
	newfile.create_table(conn, c)
	
	#Check if category is in there
	if category in categlist:
		categdict = {'Cleric': [5, 10, 25], 'Knight': [15, 20, 10], 'Barbarian': [15, 15, 15], 'Castellan': [25, 15, 5], 'Hunter': [10, 15, 20]}
		categitem = {'Cleric': 'Broken_Staff', 'Knight': 'Stone Crudesword', 'Barbarian': 'Wooden Mace', 'Castellan': 'Stone Gauntlet', 'Hunter': 'Wooden Bow'}

		#Database will return an error if there's an existing instance of the name joined. Thus, I'll exploit this to give back an explanatory response
		try:
			newfile.data_entry(c, ctx.author.name, category, 0, 0, 0, categdict[category], categitem[category], conn, list(dict.keys(class_descriptions.DefaultMovesets[category])))
			await ctx.send(f'You have joined the Adventure as {ctx.author.name}, a {category}.\nYou stand at level 0 and have 0 money. Let the adventure begin!!!')
		except sqlite3.Error:
			await ctx.send('You have already joined! You need not join again.')
			
	else:
		await ctx.send(f'{category} is not a valid category. Try joining as {categlist[0]}, {categlist[1]}, {categlist[2]}, {categlist[3]}, or {categlist[4]}.')
	
#The entirety of this command is self-explanatory
@AdventBot.command()
async def classinfo(ctx, vclass):
	if vclass in categlist:
		embedVar = discord.Embed(title=vclass, description = class_descriptions.categdesc[vclass], color = discord.Colour.blue())
		embedVar.add_field(name="Tip", value = random.choice(class_descriptions.categtip[vclass]), inline = False)
		await ctx.send(embed=embedVar)
	else:
		await ctx.send(f'{vclass} is not a suitable class. Try any one of {categlist[0]}, {categlist[1]}, {categlist[2]}, {categlist[3]}, or {categlist[4]}.')

#The standard Campaign command
@AdventBot.command()
@commands.cooldown(1, 1800, commands.BucketType.user)
async def campaign(ctx):
	c = conn.cursor()

	#The database will again return an error in case the user has not registered, since the database has no instance of the user name.
	try:
		c.execute('SELECT category, level, experience FROM UserCredentials WHERE name = (?)', (ctx.author.name,))
		data = c.fetchall()
		categ = data[0][0]
		experience = int(data [0][2])
		level = data[0][1]
	except:
		await ctx.send('You don\'t seem to have joined. You can do --join "category" now to do so.')
		
	#everything below this is database gibberish you might want to skip out.
	exp = random.randint(class_descriptions.level_exp_list[str(level)][0], class_descriptions.level_exp_list[str(level)][1])
	experience += exp
	
	dict1 = {'c': [f'You looked in your wizardry books to revise. You got {exp} experience.'], 'h': [f'You practiced hitting the target with your bow. You got {exp} experience.'], 'b':[f'You tried learning the tongue of the civilised. You got {exp} experience.'], 'k':[f'You went to the Priestess of the Church for some "Holy Training". You got {exp} experience.'], 'ca': [f'You reasoned with some traders to reduce the taxes. You succeeded, however getting a handful of curses and {exp} experience']}
	
	dict10 = class_descriptions.lvl_dict(dict1, int(level), exp)
	await ctx.send(random.choice(dict10[class_descriptions.Categ_determiner[categ]]))
	if experience < 2*100*(int(level)+1):
		newfile.campaign_update(ctx.author.name, c, experience, conn, level)
	else:
		await ctx.send("Level up!!!")
		newfile.campaign_update(ctx.author.name, c, experience, conn, int(level)+1)
	
@campaign.error
async def campaign_error(ctx, error):
	if isinstance(error, commands.CommandOnCooldown):
		await ctx.send(f"Your Character is tired from going on a campaign. Try again after resting {int(error.retry_after/60)} minutes and {int(error.retry_after%60)} seconds.")

#This too is pretty much self explanatory
@AdventBot.command()
@commands.cooldown(1, 900, commands.BucketType.user)
async def mine(ctx):
	rarity = class_descriptions.itemRarity()
	Item = random.choice(class_descriptions.Items[rarity])
	int1 = random.randint(class_descriptions.rarityItemRandom[rarity][0], class_descriptions.rarityItemRandom[rarity][1])
	woodResponses = {"c": f"After a lot of magical practice you could chop down the small tree in your backyard. You got {int1} wood.",
"h": f"You smashed down an entire tree using your strength. You got {int1} wood.",
'b': f"You just gutted an entire tree as if it were some small sapling. You got {int1} wood.",
'k': f"As the church ordered, you chopped down an unholy tree. The church lets you keep {int1} wood.",
'ca': f"You ordered your royal servants to chop you some wood. They got you {int1} wood."}

	mineResponses = { "c": f"You mined for an hour and could finally get {int1} {Item}.",
"h": f"You went into the cave to take whatever mother earth had to offer. You got {int1} {Item}.",
"b": f"You saw something shiny on the rock and kept hitting it for some minutes. It broke and gave you {int1} {Item}.",
"k": f"You went into the cave to mine into a vein of {Item}. You found {int1} of it.",
"ca": f'You ordered your miners to bring you a lot of {Item}. They couldn\'t find a lot there but only {int1}'}
	c = conn.cursor()
	try:
		categ = newfile.getCateg(ctx.author.name, c, conn)
	except sqlite3.Error:
		ctx.send("You haven't joined yet. Do the join command: --join to join now!!!")
	categChar = class_descriptions.Categ_determiner[categ]
	if Item == "Wood":
		await ctx.send(woodResponses[categChar])
	else:
		await ctx.send(mineResponses[categChar])
	data = newfile.collectibleUpdateInfo(c, ctx.author.name, Item)
	if not data:
		newfile.collectibleInsert(c, conn, ctx.author.name, Item, int1)
	else:
		int1 += data[0][0]
		newfile.collectibleUpdate(conn, c, ctx.author.name, Item, int1)

@mine.error
async def mine_error(ctx, error):
	if isinstance(error, commands.CommandOnCooldown):
		await ctx.send(f"Your Character can only mine once in 15 minutes. You can try again in {int(error.retry_after/60)} minutes and {int(error.retry_after%60)} seconds.")

#database gibberish you'd want to leave out again
@AdventBot.command()
async def craft(ctx, *, craftable):
	c = conn.cursor()
	if craftable in class_descriptions.Crafting_Dict:
		required = list(class_descriptions.Crafting_Dict[craftable].keys())[0]
		collected = newfile.getCraftData(c, conn, ctx.author.name, required)
		if collected:
			if collected[0][0] >= class_descriptions.Crafting_Dict[craftable][required]:
				await ctx.send(f"You have crafted a {collectible}!!")
				collectnum = newfile.getCraftableData(c, conn, ctx.author.name, craftable)
				if not collectnum:
					newfile.craftableEntry(c, conn, ctx.author.name, craftable)
				else:
					collectnum1 = collectnum[0][0]
					collectnum1 += 1
					newfile.updateCraftable(c, conn, collectnum1, ctx.author.name, craftable)
					newfile.collectibleUpdate(conn, c, ctx.author.name, required, collected[0][0] - class_descriptions.Crafting_Dict[craftable][required])
						
			else:
				await ctx.send(f"You have too less of {required} to craft {craftable}. You should try mining more.")
				
		elif not collected:
			await ctx.send("You don't have any material of this kind. Try collecting some by mining.")
	else:
		await ctx.send("You cannot craft this material.")
			

@AdventBot.command()
async def stats(ctx, member: discord.Member = None):
	if member is None:
		try:
			c = conn.cursor()
			c.execute('SELECT category, level, money, experience, defence, attack, magic, mainItem FROM UserCredentials WHERE name = (?)', (ctx.author.name,))
			data = c.fetchall()
			category = data [0][0]
			level = int(data[0][1])
			money = int(data[0][2])
			experience = int(data[0][3])
			defence = int(data[0][4])
			attack = int(data[0][5])
			magic = int(data[0][6])
			mainItem = data[0][7]
			embedVar = discord.Embed(title = ctx.author.name, description = f'You are a {category} and currently stand at Level {level} with {experience} experience. You have {money} money.\n\nDefence:{defence}\nAttack:{attack}\nMagic:{magic}\nYour main weapon right now is {mainItem}.')
			embedVar.set_author(name= ctx.author.name, icon_url=ctx.message.author.avatar_url)
			await ctx.send(embed = embedVar)
		except:
			await ctx.send("You haven't joined yet. Try joining now!")
	else:
		c = conn.cursor()
		c.execute('SELECT category, level, money, experience, defence, attack, magic, mainItem FROM UserCredentials WHERE name = (?)', (member.name,))
		data = c.fetchall()
		category = data [0][0]
		level = int(data[0][1])
		money = int(data[0][2])
		experience = int(data[0][3])
		defence = int(data[0][4])
		attack = int(data[0][5])
		magic = int(data[0][6])
		mainItem = data[0][7]
		embedVar = discord.Embed(title = member.name, description = f'You are a {category} and currently stand at Level {level} with {experience} experience. You have {money} money.\n\nDefence:{defence}\nAttack:{attack}\nMagic:{magic}\nYour main weapon right now is {mainItem}.')
		embedVar.set_author(name= member.name, icon_url=member.avatar_url)
		await ctx.send(embed = embedVar)

@AdventBot.command()
async def inventory(ctx, member: discord.Member = None):
	if member is None:
		member = ctx.author
		
	c = conn.cursor()
	try:
		data1 = newfile.collectibleInventory(c, conn, member.name)
		embedVar = discord.Embed(title = member.name , description = "Your inventory contains the following items:-")
		for collectible in data1:
			embedVar.add_field(name = collectible[0], value = collectible[1])
		await ctx.send(embed = embedVar)
	except:
		await ctx.send("You don't have any collectible in your inventory. You can do --mine per 30 minutes to collect some.")
	
@AdventBot.command()
async def craftable(ctx, *, ItemName = None):
	if ItemName is None:
		desc = ""
		for craft in class_descriptions.Craftables:
			desc += f"**{craft}**\n\n"
		embedVar2 = discord.Embed(title = "Craftable Items", description = desc)
		await ctx.send(embed= embedVar2)

	else:
		try:
			embedVar = discord.Embed(title = ItemName, description = class_descriptions.Craftables[ItemName]["Description"], colour = discord.Color(value=int(class_descriptions.rarityColour[class_descriptions.Craftables[ItemName]["Rarity"]], 16)))
			for key in class_descriptions.Craftables[ItemName]:
				if key != "Description":
					embedVar.add_field(name = key, value = class_descriptions.Craftables[ItemName][key])
			await ctx.send(embed = embedVar)
		except:
			await ctx.send("Item not found!!")

@AdventBot.command()
async def collectible(ctx, itemName = None):
	collectibleList = ["Wood", "Iron", "Amethyst", "Silver", 'Electrum',"Gold", "Petronacium", "Zyber", "Oharium"]
	if itemName is not None:
		if itemName in collectibleList:
			embedVar = discord.Embed(title = itemName, description = class_descriptions.collectibleDesc[itemName][0], colour = discord.Color(value=int(class_descriptions.rarityColour[class_descriptions.collectibleDesc[itemName][1]], 16)))
			embedVar.add_field(name = "Rarity",  value = class_descriptions.collectibleDesc[itemName][1])
			await ctx.send(embed = embedVar)
		else:
			embedVar =discord.Embed(title = "Collectible not found!", description = "The collectible you were looking for was not found. Try one of the following:-", color = discord.Color(value = int("ff0000", 16)))
			for stuff in collectibleList:
				embedVar.add_field(name=stuff, value = class_descriptions.collectibleDesc[stuff][1], inline = False)
			await ctx.send(embed = embedVar)
	else:
		desc = ""
		for collect in collectibleList:
			desc += f'**{collect}**\n\n'
		embed2 = discord.Embed(title = "Collectible Items", description = desc, colour = discord.Color(value=int('00ff00', 16)))
		await ctx.send(embed= embed2)
	
@AdventBot.command()
async def equip(ctx, *, itemName):
	c = conn.cursor()
	#Get data from the database
	try:
		data1 = newfile.getInventory(c, conn, ctx.author.name)
	except:
		await ctx.send("Selected item cannot be found. Perhaps try seeing if you can craft it.")
	#Iteration happens here
	for key in data1:
		if key[0] == itemName:
			newItemNum = key[1] - 1
			#Below this I'll update the db since equipment decreases 1 amount from the inventory
			if newItemNum >= 0:
				newfile.updateCraftable(c, conn, newItemNum, ctx.author.name, itemName)
				#Now, we can go ahead and check what type of equipment it is so we can equip it in the specified slot
				if class_descriptions.Craftables[itemName]["Type"] in class_descriptions.Main_equipment_dict:
					newfile.EquipMainItem(ctx.author.name, c, conn, itemName)
					await ctx.send("Main Item has been equipped!!")
				else:
					newfile.EquipOtherItems(c, conn, ctx.author.name, itemName, class_descriptions.Equipment_db_dict[class_descriptions.Craftables[itemName]["Type"]])
					await ctx.send(f"{itemName} has been equipped!!")
			else:
				await ctx.send("Selected Item cannot be found!!")

@AdventBot.command()
async def moves(ctx, *, ItemName = None):
	if ItemName is None:
		c = conn.cursor()
		try:
			#Get data from the db
			categ = newfile.getCateg(ctx.author.name, c, conn)
			data1 = newfile.getInventory(c, conn, ctx.author.name)
			
			embed1 = discord.Embed(title = "Moves" , description = "The moves available for you are listed below", color = discord.Color(value= int("ff8700", 16)))
			embed1.set_author(name= ctx.author.name, icon_url=ctx.message.author.avatar_url)
			for key in data1:
				movedict = class_descriptions.Move_Dict[key[0]]
				for key2 in movedict:
					embed1.add_field(name= key2, value=class_descriptions.Move_Dict[key[0]][key2])
			for move in class_descriptions.DefaultMovesets[categ]:
				embed1.add_field(name= move, value= class_descriptions.DefaultMovesets[categ][move])
			await ctx.send(embed= embed1)

		except sqlite3.Error as error:
			await ctx.send("You have either not joined, or do not have any craftable in Inventory.")
			print(error)
	
	else:
		embed1 = discord.Embed(title = ItemName, description = "The moves for the given equipment are listed below", color = discord.Color(value= int("ff8700", 16)))
		for key in class_descriptions.Move_Dict[ItemName]:
			embed1.add_field(name= key, value= class_descriptions.Move_Dict[ItemName][key])

		await ctx.send(embed = embed1)

@AdventBot.command()
async def addmove(ctx, move):
	if '[p]' in move:
		movetype = "passive"
	else:
		movetype = "normal"
	try:
		c = conn.cursor()
		deterchar = 'n'
		#Get data from the db
		data1 = newfile.getMainEquipment(c, ctx.author.name)
		data2 = newfile.getOtherEquipment(c, ctx.author.name)
		movesetData = newfile.getMoveset(c, ctx.author.name)
		NorMove1 = movesetData[0][0]
		NorMove2 = movesetData[0][1]
		NorMove3 = movesetData[0][2]
		NorMove4 = movesetData[0][3]
		NorMove5 = movesetData[0][4]
		PassMove1 = movesetData[0][5]
		PassMove2 = movesetData[0][6]
		Movelist = [NorMove1, NorMove2, NorMove3, NorMove4, NorMove5, PassMove1, PassMove2]

		for move1 in class_descriptions.Move_Dict[data1[0][0]]:
			if  move1 == move:
				deterchar = 'c'
			else:
				for equipment in data2:
					for key in equipment:
						if key != "none":
							movedict = class_descriptions.Move_Dict[key]
							for key2 in movedict:
								if move == key2:
									#Ima do stuff here
									deterchar = 'c'
				
		if deterchar == 'c':
			desc = ""
			await ctx.send("Move is available to be added. Loading prompt.")
			for key in range(0, 7):
				desc += f"{key + 1} = {Movelist[key]}\n"

			ChangemoveEmbed = discord.Embed(title= "Change your moves", description= desc)
			await ctx.send(embed=ChangemoveEmbed)

			def check(m):
				return m.author.id == ctx.author.id and m.channel.id == ctx.channel.id and m.content in ['1', '2', '3', '4', '5', '6', '7']

			try:
				msg = await AdventBot.wait_for('message', check= check, timeout= 30.0)
			except asyncio.TimeoutError:
				await ctx.send("Time ran out! Try again!")
				return

			else:
				if movetype == 'normal' and int(msg.content) < 6:
					movesetType = "move"+ msg.content
					newfile.moveUpdate(c, conn, ctx.author.name, movesetType, move)
					await ctx.send("Move replaced successfully!")
				elif movetype == 'passive' and int(msg.content) > 5:
					movesetType = "passive"+ str(int(msg.content) - 5)
					newfile.moveUpdate(c, conn, ctx.author.name, movesetType, move)
					await ctx.send("Move replaced successfully!")
				else:
					await ctx.send("You can only replace Passives with Passives, and Normals with Normal moves.")
		else:
			await ctx.send("This move is currently unavailable.")

	except sqlite3.Error as error:
		await ctx.send("You have either not joined, or do not have any available Moves.")
		print(error)

@AdventBot.command()
async def moveset(ctx):
	c = conn.cursor()

	movesetDat = newfile.getMoveset(c, ctx.author.name)
	categdat = newfile.getCateg(ctx.author.name, c, conn)

	try:
		MovesetEmbed = discord.Embed(title= "Moves")
		MovesetEmbed.set_author(name=ctx.author.name, icon_url=ctx.message.author.avatar_url)
		for move in movesetDat[0]:
			if move in class_descriptions.DefaultMovesets[categdat]:
				MovesetEmbed.add_field(name= move, value= class_descriptions.DefaultMovesets[categdat][move])

			for equipment in class_descriptions.Move_Dict:
				if move in class_descriptions.Move_Dict[equipment]:
					MovesetEmbed.add_field(name= move, value= class_descriptions.Move_Dict[equipment][move])

		await ctx.send(embed=MovesetEmbed)
	except sqlite3.Error as error:
		await ctx.send("Error encountered!")
		print(error)

AdventBot.run(token)
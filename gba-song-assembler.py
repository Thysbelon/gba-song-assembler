import os, sys, struct, subprocess

#TODO: 
# Metroid Zero Mission sound table cannot be detected by sappy_detector. Copy VG Music Studio's MP2K.yaml to use as a fallback.
# Mainline Pokemon and Golden Sun (and metroid zero mission?) may need more testing, but I will leave that to users.

# To write command-line output to a log text file, use "python gba-song-assembler.py ... > log.txt" on Windows (cmd), and "python3 gba-song-assembler.py ... | tee log.txt" on Linux
def debugp(*instring):
	if debugBool==True:
		tempList=list(instring)
		for i in range(0, len(tempList)):
			if isinstance(tempList[i], str)==False:
				tempList[i]=str(tempList[i])
		print(' '.join(tempList))

def get_GBA_pointer():
	p=0
	p = struct.unpack('I', inGBA.read(4))[0] # file.read() seeks forward by the number of bytes read
	return p & 0x3FFFFFF

def evalConstants(myKeywords, defCount, defs):
	debugp('evaluating constants...')
	for wordi in range(1, len(myKeywords)):
		debugp(myKeywords[wordi])
		tempKeyword=myKeywords[wordi]
		mathSymbols='+-/*'
		for symbol in mathSymbols:
			tempKeyword=tempKeyword.replace(symbol, '@'+symbol+'@') # insert a unique symbol in between any math operators.
		debugp(tempKeyword)
		tempKeyword=tempKeyword.split('@') # use the unique symbol to separate the math operators from the numbers and constants
		debugp(tempKeyword)
		for term in range(0, len(tempKeyword)):
			debugp('term:', tempKeyword[term])
			if mathSymbols.count(tempKeyword[term])>0: # skip math operators
				debugp(tempKeyword[term], 'is a math operator.')
				continue
			if tempKeyword[term].isnumeric()==False: # check if term is a constant
				debugp(tempKeyword[term], 'is a constant.')
				for defi in range(defCount, 0, -1): # fold out all equs
					if tempKeyword[term] == defs[0][defi-1]:
						debugp(tempKeyword[term], 'is the same as', defs[0][defi-1])
						tempKeyword[term] = str(defs[1][defi-1])
						break # break out of the def loop, then continue the term loop
		myKeywords[wordi]=''.join(tempKeyword)
			
	debugp('myKeywords after evaluating constants:', myKeywords)

def compileS(sFilePath): # python doesn't have function hoisting
	debugp("compileS")
	global defs
	global defCount
	debugp('defCount:', defCount)
	global labelToWatchFor
	debugp('labelToWatchFor:', labelToWatchFor)
	global watchedLabelOffset
	debugp('watchedLabelOffset:', watchedLabelOffset)
	global inGBA
	debugp('inGBA:', inGBA)
	global songDataOffset
	debugp('songDataOffset:', hex(songDataOffset))
	global songHeaderAddress
	debugp('songHeaderAddress:', hex(songHeaderAddress))
	global songTooLargeWarning
	global debugBool
	
	myKeywords=[]
	
	inGBA.seek(songDataOffset)
	debugp('cur seek:', hex(inGBA.seek(0,1)))
	
	with open(sFilePath) as inS:
		for sLine in inS:
			debugp('sLine:', sLine[:-1]) # do not print newline
			sLine = sLine.replace("\t", " ") # fold in the tabs
			if "@" in sLine: # strip away comments
				sLine = sLine[:sLine.find('@')]
			sLine = sLine.strip() # strip away spaces
			sLine = sLine.replace(',', ', ') # do some more folding
			sLine = sLine.replace('  ', ' ')
			sLine = sLine.replace('  ', ' ')
			sLine = sLine.replace(',', '')
			debugp('sLine after formatting:', sLine)
			
			if len(sLine) == 0: continue # did we end up with an empty line? then skip it.
			
			myKeywords=sLine.split() # split up the line into seperate keywords # Uses spaces as the delimiter.
			
			debugp('is it a label? myKeywords[0][-1]:', myKeywords[0][-1])
			if myKeywords[0][-1] == ':': # is this a label?
				debugp('it is a label.')
				defs[0][defCount] = myKeywords[0][:-1] # take out the label name
				debugp('label name:', defs[0][defCount])
				defs[1][defCount] = inGBA.seek(0, 1) + 0x8000000 # find and store the current target file position. seek(0, 1) is used to get the current seek position without changing seek.
				debugp('position:', hex(defs[1][defCount] - 0x8000000))
				if defs[0][defCount] == labelToWatchFor: # is this the song header's label?
					watchedLabelOffset = inGBA.seek(0, 1) # store header offset
					debugp("this is the song header's label. watchedLabelOffset:", hex(watchedLabelOffset))
					if sys.argv.count('--songDataOffset')==0 and isinstance(songHeaderAddress, int) and watchedLabelOffset>songHeaderAddress: # Don't run this check if there is a user-defined songDataOffset
						debugp("WARNING! The watchedLabelOffset", hex(watchedLabelOffset), "is greater than the original songHeaderAddress "+hex(songHeaderAddress)+". Data may be corrupted.")
						songTooLargeWarning=True
				defCount+=1
				continue # stop compiling. we can get away with this thanks to the well-formed Midi2AGB output.
			
			match myKeywords[0]:
				case ".include":
					if os.path.exists(myKeywords[1][1:-1])==False: # remove quotes from string
						print("Can't find file", myKeywords[1], """for inclusion. Assembly halted.
The file,""", myKeywords[1], "must be in the same folder as gba-song-assembler.py")
						quit()
					compileS(myKeywords[1][1:-1]) # fork out a new compiler
				case ".global":
					labelToWatchFor = myKeywords[1] # there's only one global: the header's label!
					debugp('global found:', labelToWatchFor)
				case ".equ":
					evalConstants(myKeywords, defCount, defs)
					debugp('defCount:', defCount)
					defs[0][defCount] = myKeywords[1] # simply store the keyword and value
					debugp('defs[0][defCount]:', defs[0][defCount])
					defs[1][defCount] = eval(myKeywords[2])
					debugp('defs[1][defCount]:', defs[1][defCount])
					defCount+=1
					debugp('defCount:', defCount)
				case ".byte":
					evalConstants(myKeywords, defCount, defs)
					debugp('writing bytes...')
					for i in range(1, len(myKeywords)):
						if myKeywords[i] != "":
							debugp('current keyword:', myKeywords[i])
							evaledKeyword=eval(myKeywords[i])
							debugp('evaledKeyword:', evaledKeyword)
							intedEval=int(evaledKeyword)
							debugp('intedEval:', intedEval)
							bytesToWrite=bytes([intedEval])
							debugp('bytesToWrite:', bytesToWrite)
							inGBA.write(bytesToWrite)
				case ".word":
					for i in range(defCount):
						if myKeywords[1] == defs[0][i]:
							inGBA.write(struct.pack('I', int(defs[1][i]))) # words in Sappy songs are always label names.
							break # this should only break the label loop
				case ".end":
					break
				case ".align":
					# https://stackoverflow.com/questions/17306784/what-does-the-align-directive-mean-in-x86-64-assembly
					debugp('align '+myKeywords[1]+', current seek: '+hex(inGBA.seek(0,1))+', forcing align to 4, aligning...')
					#alignVal=int(myKeywords[1])
					alignVal=4 # songs don't seem to play unless the start of song data AND the header are 4-byte aligned.
					if inGBA.seek(0,1) % alignVal != 0:
						for i in range(20):
							inGBA.seek(1,1)
							if inGBA.seek(0,1) % alignVal == 0: break
						debugp('alignment complete. new seek:', hex(inGBA.seek(0,1)))
					else:
						debugp('already aligned. No need to seek forward.')
				case _:
					debugp(myKeywords[0], "doesn't have a case defined for it. current GBA position:", hex(inGBA.seek(0,1)))
	print('DONE', sFilePath)


if len(sys.argv) < 4:
	print("""usage: assembler-rewrite.py <file.gba> <file.s> <songNumToReplace: number>
options:
--sappy_detector_path <path to directory>  : a path to the directory (a.k.a. folder) that contains the program sappy_detector. *Do not include the filename of sappy_detector*. Also, do not put a slash at the end of the path. Also, if your path contains spaces, please wrap it in quotes. By default, this program looks in "." (the folder from which this program is being run) for sappy_detector.
--songDataOffset <address>  : The address to which song data will be written. The program calculates this for you based on songNumToReplace by default. If you get a warning that your injected song data is too large, use this option to set songDataOffset to an area of free space in the GBA rom. Free space can be found by looking through the rom with a hex editor. Free space is filled with all 0x00 or 0xFF.
--voiceGroup <address>  : Address to the instruments that will be used for this song. By default, this is obtained from the header of the song being replaced.
--songTableEntry <address>  : Address to the song's entry in the song table. By default, this is calculated based on the location of the sound table as reported by sappy_detector, and the songNumToReplace.
--soundTableAddress <address>  : Address to the song table (a.k.a. sound table). If this option is set, sappy_detector will not be run. By default, this program runs sappy_detector to obtain the soundTableAddress.
--setSongTableEntryBool <true or false>  : If set, you will not be prompted for input on whether to write the header pointer to the song table entry.
--debugBool <true or false>  : If true, lots of debug messages will be printed. False by default.
All addresses must be written in hexadecimal.
All paths with spaces in them must be wrapped in quotes.
""")
	sys.exit()
else:
	#define variables that may or may not be set by command-line options. anything defined here is in global scope
	sappyDetectorPath='.'
	songDataOffset='nothing'
	voiceGroup='nothing'
	songTableEntry='nothing'
	soundTableAddress='nothing'
	optionParsed=False
	inGBApath='nothing'
	inSpath='nothing'
	songNumToReplace='nothing'
	setSongTableEntryBool='nothing'
	songHeaderAddress='nothing'
	debugBool=False
	
	# parse arguments
	for arg in range(1, len(sys.argv)):
		if optionParsed==True:
			optionParsed=False
			continue
		if sys.argv[arg].startswith('--'):
			match sys.argv[arg]:
				case '--sappy_detector_path': # This should function even with spaces.
					if os.path.exists(sys.argv[arg+1])==False:
						print("can't find", sys.argv[arg+1])
						sys.exit()
					sappyDetectorPath=sys.argv[arg+1]
				case '--songDataOffset':
					songDataOffset=int(sys.argv[arg+1], 16)
				case '--voiceGroup':
					voiceGroup=int(sys.argv[arg+1], 16)
				case '--songTableEntry':
					songTableEntry=int(sys.argv[arg+1], 16)
				case '--soundTableAddress':
					soundTableAddress=int(sys.argv[arg+1], 16)
				case '--setSongTableEntryBool':
					if sys.argv[arg+1].casefold()=='true':
						setSongTableEntryBool=True
					elif sys.argv[arg+1].casefold()=='false':
						setSongTableEntryBool=False
					else:
						print('warning: unrecognized value for setSongTableEntryBool.')
				case '--debugBool':
					if sys.argv[arg+1].casefold()=='true':
						debugBool=True
					elif sys.argv[arg+1].casefold()=='false':
						debugBool=False
					else:
						print('warning: unrecognized value for debugBool.')
				case _:
					print('invalid option '+sys.argv[arg]+'. Quitting...')
					sys.exit()
			optionParsed=True
		elif sys.argv[arg][-4:].count('.') != 0:
			# file path
			if os.path.exists(sys.argv[arg])==False:
				print("can't find", sys.argv[arg])
				sys.exit()
			else:
				if sys.argv[arg].endswith('.gba'):
					inGBApath=sys.argv[arg]
				elif sys.argv[arg].endswith('.s'):
					inSpath=sys.argv[arg]
				else:
					print('unrecognized file extension in '+sys.argv[arg]+'.')
					sys.exit()
		else:
			try: 
				songNumToReplace=int(sys.argv[arg])
			except:
				print('Unknown argument '+sys.argv[arg]+'. It cannot be used as songNumToReplace.')
				sys.exit()
	if inGBApath=='nothing' or inSpath=='nothing' or (songNumToReplace=='nothing' and songTableEntry=='nothing'): # if songTableEntry is defined, we don't need songNumToReplace
		print('One of the required files (.gba or .s) or songNumToReplace and songTableEntry are undefined.')
		sys.exit()
	
	# define global variables needed for the program
	defs = [['nothing' for i in range(4098)] for j in range(2)]
	defCount=0
	labelToWatchFor=""
	watchedLabelOffset=0
	songTooLargeWarning=False
	
	# run sappy_detector to get soundTableAddress, if it was not set with a command-line option.
	if soundTableAddress=='nothing':
		# https://www.geeksforgeeks.org/print-output-from-os-system-in-python/
		# TODO: see if paths containing apostrophes cause issues here
		# TODO: check if sappy_detector exists at sappyDetectorPath before attempting to run.
		if sys.platform.startswith('win'):
			sappyDetectorCommand = '"'+sappyDetectorPath+'\\sappy_detector.exe" "'+inGBApath+'"' # backslashes are an escape character, so to write an ordinary backslash, I need to write two backslashes.
		else:
			sappyDetectorCommand = '"'+sappyDetectorPath+'/sappy_detector" "'+inGBApath+'"'
		print('sappyDetectorCommand:', sappyDetectorCommand)
		sappyDetectorResult = subprocess.run(sappyDetectorCommand, capture_output=True, text=True, shell=True).stdout
		# TODO: gracefully handle the error of sappy_detector not finding the song table.
		sappyDetectorResult = sappyDetectorResult[sappyDetectorResult.find('Song table located at: ')+23:-1]
		print("sappyDetectorResult:", sappyDetectorResult)
		soundTableAddress = int(sappyDetectorResult, 16)
		print('soundTableAddress:', soundTableAddress, '. hex(soundTableAddress):', hex(soundTableAddress))
	if songTableEntry=='nothing':
		songTableEntry=soundTableAddress+songNumToReplace*8
		print('songTableEntry:', songTableEntry, '. hex(songTableEntry):', hex(songTableEntry))
	inGBA = open(inGBApath, "r+b") # https://docs.python.org/3/library/functions.html#open
	if voiceGroup=='nothing' or songDataOffset=='nothing':
		inGBA.seek(songTableEntry)
		songHeaderAddress=get_GBA_pointer()
		print('songHeaderAddress:', songHeaderAddress, '. hex(songHeaderAddress):', hex(songHeaderAddress))
		inGBA.seek(songHeaderAddress)
		# read necessary data from the song header. For your information, the song header is located at the *end* of the song data.
		inGBA.seek(1+1+1+1, 1) # totalTracks, unknownByte, priority, reverb
		debugp("current seek:", hex(inGBA.seek(0,1)))
		if voiceGroup=='nothing':
			voiceGroup = get_GBA_pointer()
			print('voiceGroup:', voiceGroup, '. hex(voiceGroup):', hex(voiceGroup))
		else:
			inGBA.seek(4,1) # seek forward and read songDataOffset
		debugp("current seek:", hex(inGBA.seek(0,1)))
		if songDataOffset=='nothing':
			songDataOffset = get_GBA_pointer() # start of song data / location of the first track
			print('songDataOffset:', songDataOffset, '. hex(songDataOffset):', hex(songDataOffset))
			# No need to write an else statement to seek forward here; we're done with the header
	
	defs[0][0]="voicegroup000";
	defs[1][0]=voiceGroup + 0x8000000;
	defCount=1;
	# m4a2s outputs song data s files with the soundbank constant named something like "bank_001". this trips up this assembler. TODO: fix.
	compileS(inSpath)
	print("Done")
	if songTooLargeWarning==True:
		print("WARNING! The size of the injected song is larger than the song it's replacing. The song immediately after may be corrupted, or other data may be corrupted.")
	if setSongTableEntryBool=="nothing":
		setSongTableEntryBool = input("Do you want to set the proper entry in the Song Table? Yes/No\n")
		match setSongTableEntryBool.casefold():
			case "yes":
				setSongTableEntryBool=True
			case "true":
				setSongTableEntryBool=True
			case "no":
				setSongTableEntryBool=False
			case "false":
				setSongTableEntryBool=False
	if setSongTableEntryBool==True:
		inGBA.seek(songTableEntry)
		inGBA.write(struct.pack('I', watchedLabelOffset + 0x8000000))
	inGBA.close()
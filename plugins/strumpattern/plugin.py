# StrumPattern MMA plugin 
#
# written by Ignazio Di Napoli
# <neclepsio@gmail.com> 

### This does NOT work with python3. Sorry :)

"""
This module is an integeral part of the program
MMA - Musical Midi Accompaniment.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

Bob van der Poel <bob@mellowood.ca>

"""


# This import will access the global variables in MMA.
# You can BUT SHOULD NOT change things. 

import MMA.gbl as gbl

# other imports

from MMA.common import error, warning



# ###################################
# # Plugin configuration            #
# ###################################

# The name of the plugin
NAME = "StrumPattern"

# Track types to which the plugin applies; None for non-track plugins.
TRACKTYPES = ["Plectrum"]

# A list of arguments for the plugin; each is specified with [name, default, doc]. 
# If no default is provided, use None to trigger an error if the user not specifies it.
ARGUMENTS = [
    ["Pattern",     None,  "see main documents"],
    ["Strum",       "5",   "strm value to use in sequence (see Plectrum docs)"],
    ["Volume",      "80",  "volume for strums, can be specified for each string (see Plectrum docs)"],
    ["VolumeMuted", "60",  "volume for mute, can be specified for each string (see Plectrum docs)"],
    ["VolumeEmph",  "100", "volume for emphatized strums, can be specified for each string (see Plectrum docs)"],
    ["VolumePick",  "90",  "volume for single string pick"],
]

# Simple documentation
DOC="""
Sets a pattern for Plectrum tracks.

The pattern is specified as a string of comma-separed values, that are
equally spaced into the bar.
Values can be:
    d   downward strum
    u   upward strum
    de  downward strum with emphasis
    ue  upward strum with emphasis
    dm  downward strum with muted strings
    um  upward strum with muted strings
    x   chunk
    -   do nothing (used to skip to next time division)
If only one-character codes are used, you can avoid commas.
    
Each time it's used, it creates a clone track of the provided one using the 
voice MutedGuitar for chucks and muted strums.
Its name is the name of the main track with an appended "-Muted", if you need 
to change it you must do so every time after using @StrumPattern.
"""



# ###################################
# # Utility functions               #
# ###################################

# If you don't send all the commands together the result is commands 
# are reversed since each is pushed as the very next command to be executed.
# So we save all the commands (with addCommand) and send them at the end
# (with sendCommands).

_commands = []
def addCommand(strings):
    if isinstance(strings, (str, unicode)):
        strings = [strings]
    _commands.extend(strings)

def sendCommands():
    # All values have to be lists of words. Not a string per line!
    ret = [l.split() for l in _commands]

    # The next line does the input stream push. Note that we are using
    # the current line number of the file for each line.
    gbl.inpath.push(ret, [gbl.lineno] * len(ret))

    
def parseCommandLine(line):
    s = " ".join(line)
    while " =" in s:
        s = s.replace(" =", "=")
    while "= " in s:
        s = s.replace("= ", "=")
    while "  " in s:
        s = s.replace("  ", " ")
    
    res = {name:default for name, default, _ in ARGUMENTS}
    positional = True
    for name, default, _ in ARGUMENTS:
        res[name] = default
        
    for i, value in enumerate(s.split(" ")):
        if "=" in value:
            n, _, v = value.partition("=")
            positional = False
        elif positional:
            n, _, _ = ARGUMENTS[i]
            v = value
        else:
            error("Plugin {}: positional argument after named argument is not allowed.".format(NAME))
        res[n] = v
    
    for k, v in res.items():
        if v is None:
            printUsage()
            error("Plugin {}: no value for argument {}.".format(NAME, k))
    
    return res
    

def printUsage():
    s = "Plugin {} usage:\n".format(plugInName['name'])
    if TRACKTYPES is not None:
        s += "Track "
    s += "@" + NAME + " "
        
    for name, _, _ in ARGUMENTS:
        s += name + " " 
    
    s += "\n"

    if TRACKTYPES is not None:
        if len(TRACKTYPES) == 1:
            s += "Track type must be {}.\n".format(TRACKTYPES[0])
        else:
            s += "Track type must be one of {}.\n".format(", ".join(TRACKTYPES[:-1]) + " or " + TRACKTYPES[-1])

    for name, default, doc in ARGUMENTS:
        s += "    {}:\t{}\n".format(name, doc + (" (default: "+default+")" if default is not None else ""))
    s += "\n"
    
    s += DOC.strip()
    
    print(s)
    
    
def checkTrackType(name):
    for t in TRACKTYPES:
        if name.upper() == t.upper() or name.upper().startswith(t.upper() + "-"):
            return
    
    if len(TRACKTYPES) == 1:
        error("Plugin {}: track type must be {}.".format(NAME, TRACKTYPES[0]))
    else:
        error("Plugin {}: track type must be one of {}.".format(NAME, ", ".join(TRACKTYPES[:-1]) + " or " + TRACKTYPES[-1]))
    
    

# ###################################
# # Entry point                     #
# ###################################

def trackRun(trackname, line):
    checkTrackType(trackname)
    args = parseCommandLine(line)
    
    pattern = args["Pattern"]
    strum   = args["Strum"]
    volumeN = args["Volume"]
    volumeM = args["VolumeMuted"]
    volumeE = args["VolumeEmph"]
    volumeP = args["VolumePick"]
        
    res_normal = []
    res_muted = []
    
    if "," in pattern:
        pattern = pattern.lower().split(",")
    else:
        #  you can avoid commas when not using ue, ux, de, dx
        pattern = pattern.lower()
    
    step = float(gbl.QperBar)/len(pattern)
    
    for i, c in enumerate(pattern):
        t = 1+step*i
    
        if c == "u":
            res_normal.append("{:0.2} +{} {}".format(t, strum, volumeN))
        elif c == "ue":
            res_normal.append("{:0.2} +{} {}".format(t, strum, volumeE))
        elif c == "um":
            res_normal.append("{:0.2} 0 0".format(t))
            res_muted.append("{:0.2} +{} {}".format(t, strum, volumeM))
            
        elif c == "d":
            res_normal.append("{:0.2} -{} {}".format(t, strum, volumeN))
        elif c == "de":
            res_normal.append("{:0.2} -{} {}".format(t, strum, volumeE))
        elif c == "dm":
            res_normal.append("{:0.2} 0 0".format(t))
            res_muted.append("{:0.2} -{} {}".format(t, strum, volumeM))
            
        elif c == "x":
            res_normal.append("{:0.2} 0 0".format(t))
            res_muted.append("{:0.2} 0 {}".format(t, volumeM))
            
        elif c == "0":
            res_normal.append("{:0.2} 0 0".format(t))
            
        elif c.lstrip("0").isdigit():
            res_normal.append("{:0.2} 0 {}:{}".format(t, c, volumeP))

        elif c == "-":
            pass
            
        else:
            printUsage()
            error("{}: unrecognized command in strum pattern: '{}'.".format(NAME, c))    
     
    res_normal = "{" + "; ".join(res_normal) + ";}"
    addCommand("{} Sequence {}".format(trackname, res_normal))
    addCommand("{}-Muted SeqClear".format(trackname))
    
    if len(res_muted) > 0:
        res_muted = "{" + "; ".join(res_muted) + ";}"
        addCommand("{}-Muted Copy {}".format(trackname, trackname))
        addCommand("{}-Muted Voice MutedGuitar".format(trackname))
        addCommand("{}-Muted Sequence {}".format(trackname, res_muted))
    
    # If you don't send all the commands together the result is commands 
    # are reversed since each is pushed as the very next command to be executed.
    # So we save all the commands (with addCommand) and send them at the end
    # (with sendCommands).
    sendCommands()


#!/usr/bin/env python3

"""

____   ____________ _____________________                            
\   \ /   /\______ \\______   \__    ___/__.__.______   ____   ______
 \   Y   /  |    |  \|     ___/ |    | <   |  |\____ \_/ __ \ /  ___/
  \     /   |    `   \    |     |    |  \___  ||  |_> >  ___/ \___ \ 
   \___/   /_______  /____|     |____|  / ____||   __/ \___  >____  >
                   \/                   \/     |__|        \/     \/ 

  Automatic formatting and generation of Agon VDP protocol data

  (c) 2025 James W. Hofmann

"""

"""

Current goals:

Add experimentals/undocumenteds

Add more tests (there is a lot of code that has never been run)
Add source code generation
Add functions for asset conversion
  bitmaps
  audio
  tiles?
  font?

"""

def _multiphase_array(config, level_duration, fieldname):
  """Convert list of tuples of (level, duration) to flat lists of bytecode data and size values."""
  count = len(level_duration)
  ans = {}
  if "render" in config:
    ans["data"] = []
    ans["size"] = []
    ans["field"] = []
    ans["data"].append(count)
    ans["size"].append(1)
    ans["field"].append(fieldname + "Length")
    for n in level_duration:
      ans["data"].append(n[0])
      ans["size"].append(1)
      ans["field"].append("level")
      ans["data"].append(n[1])
      ans["size"].append(2)
      ans["field"].append("duration")
  return ans

def _bytearray16(config, bytedata, fieldname):
  """Convert sequence of bytes to flat lists of bytecode data and size values."""
  count = len(bytedata)
  ans = {}
  if "render" in config:
    ans["data"] = []
    ans["size"] = []
    ans["field"] = []
    ans["log"] = []
    if count > 65535:
      lstr = f'{fieldname} of size {count} bytes is too large for 16-bit bytearray. Truncating.'
      ans["log"].append(lstr)
      bytedata = bytedata[:65535]
      count = 65535
    ans["data"].append(count)
    ans["size"].append(2)
    ans["field"].append(fieldname + "Length")
    idx = 0
    for n in bytedata:
      if (n < -128 or n > 255):
        ans["log"].append(f'bytearray {fieldname} has data that is out of range: byte {idx} is {n}. Zeroing.')
        n = 0
      ans["data"].append(n)
      ans["size"].append(1)
      ans["field"].append("v"+str(idx))
      idx += 1
  return ans

def _merge_dsf(ans0, ans1):
  ans0["data"] = ans0["data"] + ans1["data"]
  ans0["size"] = ans0["size"] + ans1["size"]
  ans0["field"] = ans0["field"] + ans1["field"]

def _array_default(ans, config, fieldname):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append(f'No array {fieldname} found, filling in with empty array.')
    config[fieldname] = []

def _array_display_char_default(ans, config, fieldname):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append(f'8-length char array {fieldname} not found, replacing with ascending sequence.')
    config[fieldname] = [0,1,2,3,4,5,6,7]
  elif len(config[fieldname])<8:
    ans["log"].append(f'8-length char array {fieldname} is smaller than 8, replacing with ascending sequence.')
    config[fieldname] = [0,1,2,3,4,5,6,7]

def _bits_default(ans, config, fieldname, minbits=1, maxbits=8):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append(f'No bits {fieldname} found, filling in with {minbits}.')
    config[fieldname] = minbits
  elif not (type(config[fieldname]) is int):
    ans["log"].append(f'int type in bits {fieldname} missing, filling in with {minbits}.')
    config[fieldname] = minbits
  elif (config[fieldname] < minbits or config[fieldname] > minbits):
    ans["log"].append(f'bits {fieldname} out of range: {config[fieldname]}, filling in with {minbits}.')
    config[fieldname] = minbits

def _u8_default(ans, config, fieldname):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append(f'No u8 {fieldname} found, filling in with empty array.')
    config[fieldname] = 0
  elif not (type(config[fieldname]) is int):
    ans["log"].append(f'int type in u8 {fieldname} missing, filling in with zero.')
    config[fieldname] = 0
  elif (config[fieldname] > 255 or config[fieldname] < -128):
    ans["log"].append(f'int type in u8 {fieldname} out of range({config[fieldname]}), filling in with zero.')
    config[fieldname] = 0

def _u16_default(ans, config, fieldname):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append(f'No u16 {fieldname} found, filling in with zero.')
    config[fieldname] = 0
  elif not (type(config[fieldname]) is int):
    ans["log"].append(f'int type in u16 {fieldname} missing, filling in with zero.')
    config[fieldname] = 0
  elif (config[fieldname] > 65535 or config[fieldname] < -32768):
    ans["log"].append(f'int type in u16 {fieldname} out of range({config[fieldname]}), filling in with zero.')
    config[fieldname] = 0

def _u24_default(ans, config, fieldname):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append(f'No u24 {fieldname} found, filling in with zero.')
    config[fieldname] = 0
  elif not (type(config[fieldname]) is int):
    ans["log"].append(f'int type in u24 {fieldname} missing, filling in with zero.')
    config[fieldname] = 0
  elif (config[fieldname] > 16777215 or config[fieldname] < -8388608):
    ans["log"].append(f'int type in u24 {fieldname} out of range({config[fieldname]}), filling in with zero.')
    config[fieldname] = 0

def _u32_default(ans, config, fieldname):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append(f'No u32 {fieldname} found, filling in with zero.')
    config[fieldname] = 0
  elif not (type(config[fieldname]) is int):
    ans["log"].append(f'int type in u32 {fieldname} missing, filling in with zero.')
    config[fieldname] = 0
  elif (config[fieldname] > 4294967295 or config[fieldname] < -2147483648):
    ans["log"].append(f'int type in u32 {fieldname} out of range({config[fieldname]}), filling in with zero.')
    config[fieldname] = 0

def _offset_default(ans, config, fieldname, is_advanced_offset):
  if is_advanced_offset:
    return _advoffset_default(ans, config, fieldname)
  else:
    return _u16_default(ans, config, fieldname)

def _advoffset_default(ans, config, fieldname):
  """Parse the input in config[fieldname] as an advanced offset, automatically rewriting it to a 2-tuple."""
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append(f'No advoffset {fieldname} found, filling in with zero.')
    config[fieldname] = (0, None)
  else:
      tc = type(config[fieldname])
      cd = config[fieldname]
      if (tc is int):
        config[fieldname] = (cd, None)
      elif (tc is list) or (tc is tuple):
        if len(cd)==1 and (type(cd[0]) is int):
          config[fieldname] = (cd[0], None)
        elif len(cd)>=2 and (type(cd[0]) is int) and ((type(cd[1]) is int) or ((cd[1]) is None)):
          config[fieldname] = (cd[0], cd[1])
        else:
          ans["log"].append(f'Advoffset {fieldname} has invalid types, filling in with zero.')
          config[fieldname] = (0, None)

def _offset(val, is_advanced_offset):
  """Emit bytecode-writable data. If advanced offset, takes tuple input, else u16."""
  if is_advanced_offset:
    return _advoffset(val)
  else:
    ans = {}
    ans["data"] = [val]
    ans["size"] = [2]
    ans["field"] = ["offset"]
    return ans

def _advoffset(tup):
  """Convert tuple of (offset, block) to bytecode-writable data."""
  ans = {}
  val = tup[0]
  if type(tup[1]) is int: # set the high bit
    val = val | 0x800
    ans["data"] = [val,tup[1]]
    ans["size"] = [3,2]
    ans["field"] = ["advoffset","block"]
  else:
    ans["data"] = [val]
    ans["size"] = [3]
    ans["field"] = ["advoffset"]
  return ans

def _buffetch_default(ans, config, fieldname, is_advanced_offset):
  """Parse the input in config[fieldname] as a buffer fetched value, using the advanced offset mode if toggled on,
    resulting in either (buffer id, offset) with 16-bit mode or (buffer id, (offset, block)) in advoffset mode."""
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append("No buffetch "+fieldname+" found, filling in with zero.")
    config[fieldname] = [0, 0]
  if not (type(config[fieldname]) is list):
    ans["log"].append("buffetch "+fieldname+" is not a list, filling in with zero.")
    config[fieldname] = [0, 0]
  if len(config[fieldname]) < 2:
    ans["log"].append("buffetch "+fieldname+" is not length 2, filling in with zero.")
    config[fieldname] = [0, 0]
  _u16_default(ans, config[fieldname], 0)
  _offset_default(ans, config[fieldname], 1, is_advanced_offset) 

def _buffetch(val, is_advanced_offset):
  ans = {}
  ans["data"] = [val[0]]
  ans["size"] = [2]
  ans["field"] = ["bufferid"]
  offsetdata = _offset(val[1], is_advanced_offset)
  _merge_dsf(ans, offsetdata)
  ans["field"][-1] = "operand-offset"
  return ans

def _operand_default(ans, config, fieldname, is_buffetch, is_advanced_offset):
  if is_buffetch:
    _buffetch_default(ans, config, fieldname, is_advanced_offset) # single buffetch
  else:
    _u8_default(ans, config, fieldname) # one byte operand

def _operand(val, fieldname, is_buffetch, is_advanced_offset):
  if is_buffetch:
    return _buffetch(val, is_advanced_offset)
  else:
    ans = {}
    ans["data"] = [val]
    ans["size"] = [1]
    ans["field"] = [fieldname]
    return ans

def _selectmap(ans, config, fieldname, strings, flags=None):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append("No selectmap "+fieldname+" found, filling in with "+strings[0]+".")
    config[fieldname] = strings[0]
  if not flags:
    flags = [n for n in range(len(strings))]
  for n in range(len(strings)):
    if config[fieldname].lower()==strings[n]:
      return flags[n]
  ans["log"].append("Invalid selectmap of field "+fieldname+": "+str(config[fieldname])+" - filling in with "+strings[0]+".")
  return flags[0]

def _flagmap(ans, config, fieldname, strings, flags=None):
  if ((type(fieldname) is str) and (not fieldname in config)) or ((type(fieldname) is int) and (len(config)<=fieldname)):
    ans["log"].append("No flagmap "+fieldname+" found, filling in with "+strings[0]+".")
    config[fieldname] = [strings[0]]
  if not flags:
    flags = [pow(2, n) for n in range(len(strings))]
  accum = 0
  for m in config[fieldname]:
    matched = False
    for n in range(len(strings)):
      if strings[n] == m.lower():
        accum = accum | flags[n]
        matched = True
    if not matched:
      ans["log"].append("Invalid flagmap of field "+fieldname+": "+str(config[fieldname])+". Ignoring.") 
  return accum

def vdu_null(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Null""")
  if "render" in config:
    ans["data"] = [0]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_printernext(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Send next character to "printer" (if "printer" is enabled)""")
  if "render" in config:
    ans["data"] = [1]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_printerenable(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Enable "printer\"""")
  if "render" in config:
    ans["data"] = [2]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_printerdisable(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Disable "printer\"""")
  if "render" in config:
    ans["data"] = [3]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_writetext(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Write text at text cursor""")
  if "render" in config:
    ans["data"] = [4]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_writegraphics(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Write text at graphics cursor""")
  if "render" in config:
    ans["data"] = [5]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_enablescreen(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Enable screen (opposite of VDU 21) """)
  if "render" in config:
    ans["data"] = [6]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_beep(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Make a short beep (BEL)""")
  if "render" in config:
    ans["data"] = [7]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_back(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Move cursor back one character""")
  if "render" in config:
    ans["data"] = [8]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_forward(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Move cursor forward one character""")
  if "render" in config:
    ans["data"] = [9]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_down(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Move cursor down one character""")
  if "render" in config:
    ans["data"] = [10]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_up(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Move cursor up one character""")
  if "render" in config:
    ans["data"] = [11]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_cls(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Clear text area (CLS)""")
  if "render" in config:
    ans["data"] = [12]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_cr(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Carriage return""")
  if "render" in config:
    ans["data"] = [13]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_pageon(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Page mode On""")
  if "render" in config:
    ans["data"] = [14]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_pageoff(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Page mode Off""")
  if "render" in config:
    ans["data"] = [15]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_clg(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Clear graphics area (CLG)""")
  if "render" in config:
    ans["data"] = [16]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_colour(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set text colour (COLOUR)""")
  if "render" in config:
    _u8_default(ans, config, "colour")
    ans["data"] = [17, config["colour"]]
    ans["size"] = [1, 1]
    ans["field"] = [None, "colour"]
  return ans

def vdu_colourmode(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set graphics colour (GCOL mode, colour)""")
  if "render" in config:
    _u8_default(ans, config, "colour")
    _u8_default(ans, config, "mode")
    ans["data"] = [18, config["mode"], config["colour"]]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, "mode", "colour"]
  return ans

def vdu_colourlogical(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Define logical colour""")
  if "render" in config:
    _u8_default(ans, config, "l")
    _u8_default(ans, config, "p")
    _u8_default(ans, config, "r")
    _u8_default(ans, config, "g")
    _u8_default(ans, config, "b")
    ans["data"] = [19, config["l"], config["p"], config["r"], config["g"], config["b"]]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, "l", "p", "r", "g", "b"]
  return ans

def vdu_colourreset(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Reset palette and text/graphics colours and drawing modes""")
  if "render" in config:
    ans["data"] = [20]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_screendisable(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Disable screen""")
  if "render" in config:
    ans["data"] = [21]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_screenmode(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Select screen mode (MODE n)""")
  if "render" in config:
    _u8_default(ans, config, "mode")
    ans["data"] = [22, config["mode"]]
    ans["size"] = [1, 1]
    ans["field"] = [None, "mode"]
  return ans

def mode_logicalscale(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Turn logical screen scaling on and off, where 1=on and 0=off.""")
  if "render" in config:
    _u8_default(ans, config, "setting")
    ans["data"] = [23, 0, 0xC0, config["setting"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "setting"]
  return ans

def mode_legacy(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Switch legacy modes on or off.""")
  if "render" in config:
    _u8_default(ans, config, "setting")
    ans["data"] = [23, 0, 0xC1, config["setting"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "setting"]
  return ans

def mode_swap(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Swap the screen buffer (double-buffered modes only) or wait for VSYNC (all modes).""")
  if "render" in config:
    ans["data"] = [23, 0, 0xC3]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def mode_flush(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Flush current drawing commands""")
  if "render" in config:
    ans["data"] = [23, 0, 0xca]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def vdu_charredefine(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Re-program display character""")
  if "render" in config:
    _u8_default(ans, config, "char")
    ch = config["char"]
    if ch < 32 or ch > 255:
      ans["log"].append(f'Char {ch} is out of range; redefining char 32 instead.')
      ch = 32
    _array_display_char_default(ans, config, "data")
    cd = config["data"]
    ans["data"] = [22, ch, cd[0], cd[1], cd[2], cd[3], cd[4], cd[5], cd[6], cd[7]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ans["field"] = [None, "char", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"]
  return ans

def vdu_cursorcontrol(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Cursor control""")
  if "render" in config:
    _selectmap(ans, config, "select", ["hide","show","steady","flash"],[0,1,2,3])
    ans["data"] = [23, 1, config["select"]]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, "select", None]
  return ans

def vdu_dottedlineredefine(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set dotted line pattern""")
  if "render" in config:
    _array_display_char_default(ans, config, "data")
    cd = config["data"]
    ans["data"] = [23, 6, cd[0], cd[1], cd[2], cd[3], cd[4], cd[5], cd[6], cd[7]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"]
  return ans

def vdu_scroll(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Scroll""")
  if "render" in config:
    _u8_default(ans, config, "extent")
    _selectmap(ans, config, "direction", ["right","left","down","up","+x","-x","+y","-y"])
    _u8_default(ans, config, "movement")
    ans["data"] = [23, 7, config["extent"], config["direction"], config["movement"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, "extent", "direction", "movement"]
  return ans

def vdu_cursormovementredefine(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Define cursor movement behaviour""")
  if "render" in config:
    _optionmap(ans, config, "setting", ["scrollprotect","direction","bottomborder","advance","rightborder","normal"],
      [1, 2|4|8, 16, 32, 64, 128])
    _optionmap(ans, config, "mask", ["scrollprotect","directionrotate","directionvflip","directionhflip","bottomborder","advance","rightborder","normal"],
      [1, 2, 4, 8, 16, 32, 64, 128])
    _u8_default(ans, config, "movement")
    ans["data"] = [23, 16, config["setting"], config["mask"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, "setting", "mask"]
  return ans

def vdu_linethickness(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set line thickness""")
  if "render" in config:
    _u8_default(ans, config, "thickness")
    ans["data"] = [23, 23, config["thickness"]]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, "thickness"]
  return ans

def vdu_hexload(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Hexload""")
  if "render" in config:
    ans["data"] = [23, 28]
    ans["size"] = [1, 1]
    ans["field"] = [None, None]
  return ans

def vdu_graphicsviewport(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set graphics viewport""")
  if "render" in config:
    _u16_default(ans, config, "left")
    _u16_default(ans, config, "bottom")
    _u16_default(ans, config, "right")
    _u16_default(ans, config, "top")
    ans["data"] = [24, config["left"], config["bottom"], config["right"], config["top"]]
    ans["size"] = [1, 2, 2, 2, 2]
    ans["field"] = [None, "left", "bottom", "right", "top"]
  return ans

def vdu_plot(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""PLOT commands""")
  if "render" in config:
    style = _selectmap(ans,config,"style",[
      "solid_ab",
      "solid_a",
      "dotdash_ab_restart",
      "dotdash_a_restart",
      "solid_b",
      "solid_",
      "dotdash_b_continue",
      "dotdash__continue",
      "point",
      "line_fill_non_bg",
      "triangle_fill",
      "line_fill_bg",
      "rectangle_fill",
      "line_fill_fg",
      "parallelogram_fill",
      "line_fill_non_fg",
      "__flood_non_bg",
      "__flood_fg",
      "circle",
      "circle_fill",
      "circle_arc",
      "circle_segment",
      "circle_sector",
      "rectangle_copy",
      "__ellipse",
      "__ellipse_fill",
      "__208",
      "fill_path",
      "__224",
      "bitmap",
      "__240",
      "__248"],[
      0,
      8,
      16,
      24,
      32,
      40,
      48,
      56,
      64,
      72,
      80,
      88,
      96,
      104,
      112,
      120,
      128,
      136,
      144,
      152,
      160,
      168,
      176,
      184,
      192,
      200,
      208,
      216,
      224,
      232,
      240,
      248])
    action = _selectmap(ans,config,"action",["move_rel","plot_rel_fg","plot_rel_inv","plot_rel_bg", "move_abs",
      "plot_abs_fg","plot_abs_inv","plot_abs_bg"],[0,1,2,3,4,5,6,7])
    code = style + action
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [25, code, config["x"], config["y"]]
    ans["size"] = [1, 1, 2, 2]
    ans["field"] = [None, "code", "x", "y"]
  return ans

def vdu_resetviewports(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Reset graphics and text viewports""")
  if "render" in config:
    ans["data"] = [26]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_charoutput(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Output character to screen""")
  if "render" in config:
    _u8_default(ans, config, "char")
    ans["data"] = [27, config["char"]]
    ans["size"] = [1, 1]
    ans["field"] = [None, "char"]
  return ans

def vdu_textviewport(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set text viewport""")
  if "render" in config:
    _u8_default(ans, config, "left")
    _u8_default(ans, config, "bottom")
    _u8_default(ans, config, "right")
    _u8_default(ans, config, "top")
    ans["data"] = [28, config["left"], config["bottom"], config["right"], config["top"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, "left", "bottom", "right", "top"]
  return ans

def vdu_graphicsorigin(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set graphics origin""")
  if "render" in config:
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [29, config["x"], config["y"]]
    ans["size"] = [1, 2, 2]
    ans["field"] = [None, "x", "y"]
  return ans

def vdu_home(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Home cursor""")
  if "render" in config:
    ans["data"] = [30]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def vdu_cursormove(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Move text cursor to x, y text position""")
  if "render" in config:
    _u8_default(ans, config, "x")
    _u8_default(ans, config, "y")
    ans["data"] = [31, config["x"], config["y"]]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, "x", "y"]
  return ans

def vdu_backspace(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Backspace""")
  if "render" in config:
    ans["data"] = [127]
    ans["size"] = [1]
    ans["field"] = [None]
  return ans

def sys_cursorstart(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set cursor start line and appearance""")
  if "render" in config:
    start = _u8_default(ans, config, "start")
    if start < 0 or start > 31:
      ans["log"].append("Start line {start} is out of range 0-31; defaulting to 0.")
      start = 0
    animate = _selectmap(ans,config,"animate",["steady","off","fast","slow"],[0,32,64,64|32])
    appearance = start | animate
    ans["data"] = [23, 0, 0x0A, appearance]
    ans["size"] = [1,1,1,1]
    ans["field"] = [None,None,None,"appearance"]
  return ans

def sys_cursorend(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set cursor end line""")
  if "render" in config:
    _u8_default(ans, config, "end")
    ans["data"] = [23, 0, 0x0B, config["end"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "end"]
  return ans

def sys_poll(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""General poll""")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 0, 0x80, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def sys_keyboardlocale(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set the keyboard locale""")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 0, 0x81, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def sys_get_textpos(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Request text cursor position""")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 0, 0x82]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def sys_get_textcode(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Get ASCII code of character at character position x, y""")
  if "render" in config:
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [23, 0, 0x83, config["x"], config["y"]]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "x", "y"]
  return ans

def sys_get_pixelcolour(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Get colour of pixel at pixel position x, y""")
  if "render" in config:
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [23, 0, 0x84, config["x"], config["y"]]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "x", "y"]
  return ans

def sys_get_screendimensions(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Fetch the screen dimensions""")
  if "render" in config:
    ans["data"] = [23, 0, 0x86]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def sys_get_rtc(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""RTC control""")
  if "render" in config:
    ans["data"] = [23, 0, 0x87, 0]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def sys_set_rtc(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""RTC control""")
  if "render" in config:
    _u8_default(ans, config, "y")
    _u8_default(ans, config, "m")
    _u8_default(ans, config, "d")
    _u8_default(ans, config, "hour")
    _u8_default(ans, config, "min")
    _u8_default(ans, config, "sec")
    ans["data"] = [23, 0, 0x87,  0, config["y"], config["m"],  config["d"], config["hour"], config["min"],  config["sec"]]
    ans["size"] = [1, 1, 1,  1, 1, 1,  1, 1, 1,  1]
    ans["field"] = [None, None, None,  None, "y", "m",  "d", "hour", "min",  "sec"]
  return ans

def sys_keyboardctl(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Keyboard Control""")
  if "render" in config:
    _u16_default(ans, config, "delay")
    _u16_default(ans, config, "rate")
    led = _flagmap(ans,config,"led",["scroll","caps","num"])
    ans["data"] = [23, 0, 0x88, config["delay"], config["rate"], led]
    ans["size"] = [1, 1, 1, 2, 2, 1]
    ans["field"] = [None, None, None, "delay", "rate", "led"]
  return ans

def sys_mouseenable(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Enable the mouse""")
  if "render" in config:
    ans["data"] = [23, 0, 0x89, 0]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def sys_mousedisable(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Disable the mouse""")
  if "render" in config:
    ans["data"] = [23, 0, 0x89, 1]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def sys_mousereset(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Reset the mouse""")
  if "render" in config:
    ans["data"] = [23, 0, 0x89, 2]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def sys_mousecursor(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set mouse cursor""")
  if "render" in config:
    _u16_default(ans,config,"cursor")
    ans["data"] = [23, 0, 0x89, 3, config["cursor"]]
    ans["size"] = [1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, None, "cursor"]
  return ans

def sys_mouseposition(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set mouse cursor position""")
  if "render" in config:
    _u16_default(ans,config,"x")
    _u16_default(ans,config,"y")
    ans["data"] = [23, 0, 0x89, 4, config["x"], config["y"]]
    ans["size"] = [1, 1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, None, "x", "y"]
  return ans

def sys_mousesamplerate(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set mouse sample rate""")
  if "render" in config:
    _u8_default(ans,config,"rate")
    ans["data"] = [23, 0, 0x89, 6, config["rate"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, None, "rate"]
  return ans

def sys_mouseresolution(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set mouse resolution""")
  if "render" in config:
    _u8_default(ans,config,"resolution")
    ans["data"] = [23, 0, 0x89, 7, config["resolution"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, None, "resolution"]
  return ans

def sys_mousescaling(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set mouse scaling""")
  if "render" in config:
    _u8_default(ans,config,"scaling")
    ans["data"] = [23, 0, 0x89, 8, config["scaling"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, None, "scaling"]
  return ans

def sys_mouseacceleration(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set mouse acceleration""")
  if "render" in config:
    _u16_default(ans,config,"acceleration")
    ans["data"] = [23, 0, 0x89, 9, config["acceleration"]]
    ans["size"] = [1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, None, "acceleration"]
  return ans

def sys_mousewheelacceleration(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set mouse wheel acceleration (accepts a 24-bit value)""")
  if "render" in config:
    _u24_default(ans,config,"acceleration")
    ans["data"] = [23, 0, 0x89, 10, config["acceleration"]]
    ans["size"] = [1, 1, 1, 1, 3]
    ans["field"] = [None, None, None, None, "acceleration"]
  return ans

def sys_cursorstartcol(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set the cursor start column""")
  if "render" in config:
    _u8_default(ans, config, "start")
    ans["data"] = [23, 0, 0x8a, config["start"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "start"]
  return ans

def sys_cursorendcol(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set the cursor end column""")
  if "render" in config:
    _u8_default(ans, config, "end")
    ans["data"] = [23, 0, 0x8b, config["end"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "end"]
  return ans

def sys_cursorrelmove(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Relative cursor movement (by pixels)""")
  if "render" in config:
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [23, 0, 0x8c, config["x"], config["y"]]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "x", "y"]
  return ans

def sys_charredefine(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Redefine character n (0-255) with 8 bytes of data""")
  if "render" in config:
    _u8_default(ans, config, "char")
    ch = config["char"]
    _array_display_char_default(ans, config, "data")
    cd = config["data"]
    ans["data"] = [23, 0, 0x90,  ch, cd[0], cd[1],  cd[2], cd[3], cd[4],  cd[5], cd[6], cd[7]]
    ans["size"] = [1, 1, 1,  1, 1, 1,  1, 1, 1,  1, 1, 1]
    ans["field"] = [None, None, None, "char", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8"]
  return ans

def sys_resetsysfont(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Reset all system font characters to original definition""")
  if "render" in config:
    ans["data"] = [23, 0, 0x91]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def sys_charbitmap(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Map character char to display bitmapId""")
  if "render" in config:
    _u8_default(ans, config, "char")
    _u16_default(ans, config, "bitmapid")
    ans["data"] = [23, 0, 0x92, config["char"], config["bitmapid"]]
    ans["size"] = [1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, "char", "bitmapid"]
  return ans

def sys_get_graphicscode(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Get ASCII code of character at graphics position x, y""")
  if "render" in config:
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [23, 0, 0x93, config["x"], config["y"]]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "x", "y"]
  return ans

def sys_get_palettecolour(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Read colour palette entry n (returns a pixel colour data packet)""")
  if "render" in config:
    _u16_default(ans, config, "n")
    ans["data"] = [23, 0, 0x94, config["n"]]
    ans["size"] = [1, 1, 1, 2]
    ans["field"] = [None, None, None, "n"]
  return ans

def sys_controlkeystoggle(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Turn control keys on and off""")
  if "render" in config:
    _u16_default(ans, config, "n")
    ans["data"] = [23, 0, 0x98, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def sys_printbuffer(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Print the contents of a buffer to the screen""")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0x9b, config["bufferid"]]
    ans["size"] = [1, 1, 1, 2]
    ans["field"] = [None, None, None, "bufferid"]
  return ans

def sys_textviewportfromplot(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set the text viewport using graphics coordinates""")
  if "render" in config:
    ans["data"] = [23, 0, 0x9c]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def sys_graphicsviewportfromplot(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set the graphics viewport using graphics coordinates""")
  if "render" in config:
    ans["data"] = [23, 0, 0x9d]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def sys_graphicsoriginfromplot(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set the graphics origin using graphics coordinates""")
  if "render" in config:
    ans["data"] = [23, 0, 0x9e]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def sys_graphicsoriginviewfromcursor(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Move the graphics origin and viewports""")
  if "render" in config:
    ans["data"] = [23, 0, 0x9f]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def sys_updatevdp(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Update VDP (for exclusive use of the agon-flash tool)""")
  if "render" in config:
    ans["data"] = [23, 0, 0xa1]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def sys_logicalscaling(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Turn logical screen scaling on and off""")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 0, 0xc0, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def sys_dotdashlength(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set dot-dash pattern length""")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 0, 0xf2, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def sys_testflag(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set a test flag""")
  if "render" in config:
    _u16_default(ans, config, "flagid")
    _u16_default(ans, config, "value")
    ans["data"] = [23, 0, 0xf8, config["flagid"], config["value"]]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "flagid", "value"]
  return ans

def sys_testflagclear(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Clear a test flag""")
  if "render" in config:
    _u16_default(ans, config, "flagid")
    ans["data"] = [23, 0, 0xf9, config["flagid"]]
    ans["size"] = [1, 1, 1, 2]
    ans["field"] = [None, None, None, "flagid"]
  return ans

def sys_consolemode(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Console mode""")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 0, 0xfe, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def sys_terminal(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Switch to or resume "terminal mode\"""")
  if "render" in config:
    ans["data"] = [23, 0, 0xff]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def aud_playnote(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Play note""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u8_default(ans, config, "volume")
    _u16_default(ans, config, "frequency")
    _u16_default(ans, config, "duration")
    ans["data"] = [23, 0, 0x85, config["channel"], 0, config["volume"],config["frequency"],config["duration"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "channel", None, "volume", "frequency", "duration"]
  return ans

def aud_status(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Status""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    ans["data"] = [23, 0, 0x85, config["channel"], 1]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None]
  return ans

def aud_set_volume(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set volume""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u8_default(ans, config, "volume")
    ans["data"] = [23, 0, 0x85, config["channel"], 2, config["volume"]]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None, "volume"]
  return ans

def aud_set_frequency(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set frequency""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u16_default(ans, config, "frequency")
    ans["data"] = [23, 0, 0x85, config["channel"], 3, config["frequency"]]
    ans["size"] = [1, 1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, "channel", None, "frequency"]
  return ans

def aud_set_waveform(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set waveform""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    waveform = _selectmap(ans, config, "waveform", ["square","triangle","sawtooth","sine","noise","vicnoise",None, None, "sample"])
    ans["data"] = [23, 0, 0x85, config["channel"], 4, waveform]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None, "waveform"]
    if waveform == 8: # sample buffer
      _u16_default(ans, config, "bufferid")
      ans["data"].append(config["bufferid"])
      ans["size"].append(2)
      ans["field"].append("bufferid")
  return ans

def aud_loadsample(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Load sample""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _array_default(ans, config, "sample")
    ans["data"] = [23, 0, 0x85, config["channel"], 5, 0, len(config["sample"])]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 3]
    ans["field"] = [None, None, None, "channel", None, None, "length"]
    count = 0
    for n in config["sample"]:
      ans["data"].append(n)
      ans["size"].append(1)
      ans["field"].append("s"+str(count))
      count += 1
  return ans

def aud_clearsample(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Clear sample""")
  if "render" in config:
    _u8_default(ans, config, "sample")
    ans["data"] = [23, 0, 0x85, config["sample"], 5, 1]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None, None]
  return ans

def aud_samplefrombuffer(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Create a sample from a buffer""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u16_default(ans, config, "bufferid")
    opt = _selectmap(ans, config, "format", ["unsigned8", "signed8"], [0, 1])
    if "samplerate" in config:
      opt = opt | 8
      _u16_default(ans, config, "samplerate")
    if "sampletuning" in config:
      opt = opt | 16
    ans["data"] = [23, 0, 0x85, config["channel"], 5, 2, config["bufferid"], opt]
    ans["size"] = [1, 1, 1, 1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "channel", None, None, "bufferid", "format"]
    if "samplerate" in config:
      ans["data"].append(config["samplerate"])
      ans["size"].append(2)
      ans["field"].append("samplerate")
    
  return ans

def aud_set_samplebasefrequency(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set sample base frequency""")
  if "render" in config:
    _u8_default(ans, config, "sample")
    _u16_default(ans, config, "frequency")
    ans["data"] = [23, 0, 0x85, config["sample"], 5, 3, config["frequency"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, "sample", None, None, "frequency"]    
  return ans

def aud_set_samplebufferbasefrequency(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set sample base frequency for a sample by buffer ID""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "frequency")
    ans["data"] = [23, 0, 0x85, config["channel"], 5, 4, config["bufferid"], config["frequency"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "channel", None, None, "bufferid", "frequency"]
  return ans

def aud_set_samplerepeatstart(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set sample repeat start point""")
  if "render" in config:
    _u8_default(ans, config, "sample")
    _u24_default(ans, config, "start")
    ans["data"] = [23, 0, 0x85, config["sample"], 5, 5, config["start"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 3]
    ans["field"] = [None, None, None, "sample", None, None, "start"]
  return ans

def aud_set_samplebufferrepeatstart(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set sample repeat start point by buffer ID""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u16_default(ans, config, "bufferid")
    _u24_default(ans, config, "start")
    ans["data"] = [23, 0, 0x85, config["sample"], 5, 6, config["bufferid"], config["start"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 2, 3]
    ans["field"] = [None, None, None, "sample", None, None, "bufferid", "start"]
  return ans

def aud_set_samplerepeatlength(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set sample repeat length""")
  if "render" in config:
    _u8_default(ans, config, "sample")
    _u24_default(ans, config, "repeatStart")
    ans["data"] = [23, 0, 0x85, config["sample"], 5, 7, config["length"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 3]
    ans["field"] = [None, None, None, "sample", None, None, "length"]
  return ans

def aud_set_samplebufferrepeatlength(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set sample repeat length by buffer ID""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u16_default(ans, config, "bufferid")
    _u24_default(ans, config, "length")
    ans["data"] = [23, 0, 0x85, config["sample"], 5, 8, config["bufferid"], config["length"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 2, 3]
    ans["field"] = [None, None, None, "sample", None, None, "bufferid", "length"]
  return ans

def aud_disable_envelope(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Volume envelope: None""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    ans["data"] = [23, 0, 0x85, config["channel"], 6, 0]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None, None]
  return ans

def aud_adsr(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Volume envelope: ADSR""")
  if "render" in config:
    _u16_default(ans, config, "attack")
    _u16_default(ans, config, "decay")
    _u8_default(ans, config, "sustain")
    _u16_default(ans, config, "release")
    _u8_default(ans, config, "channel")
    ans["data"] = [23, 0, 0x85, config["channel"], 6, 1, config["attack"], config["decay"], config["sustain"], config["release"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 2, 2, 1, 2]
    ans["field"] = [None, None, None, "channel", None, None, "attack", "decay", "sustain", "release"]
  return ans

def aud_multiphase_adsr(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Volume envelope: Multiphase ADSR""")
  if "render" in config:
    _array_default(ans, config, "attack")
    _array_default(ans, config, "sustain")
    _array_default(ans, config, "release")
    _u8_default(ans, config, "channel")
    atk = _multiphase_array(config, config["attack"], "attack")
    sus = _multiphase_array(config, config["sustain"], "sustain")
    rel = _multiphase_array(config, config["release"], "release")
    ans["data"] = [23, 0, 0x85, config["channel"], 6, 2]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None, None]
    for dsf in (atk, sus, rel):
      _merge_dsf(ans, dsf)
  return ans

def aud_freqenv_off(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Frequency envelope: Off""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    ans["data"] = [23, 0, 0x85, config["channel"], 7, 0]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None, None]
  return ans

def aud_freqenv_stepped(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Frequency envelope: Stepped""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _array_default(ans, config, "phases")
    count = 0
    for n in config["phases"]:
      if not ((type(n) is list) or (type(n) is tuple)):
        ans["log"].append(f'aud_freqenv_stepped: phase {count} isn\'t formed as (adjustment, stepcount); replacing with (100,100).')
        config["phases"][count] = (100,100)
      count+=1
    phasecount = len(config["phases"])
    controlbyte = _flagmap(ans, config, "control", ["repeats","cumulative","restrict"], [1,2,4])
    _u16_default(ans, config, "steplength")
    ans["data"] = [23, 0, 0x85, config["channel"], 7, 1, phasecount, controlbyte, config["steplength"]]
    ans["size"] = [1, 1, 1, 1, 1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, "channel", None, None, "phasecount", "controlbyte", "steplength"]
    count = 0
    for n in config["phases"]:
      ans["data"].append(n[0])
      ans["data"].append(n[1])
      ans["size"] += [2,2]
      ans["field"] += ["adj"+str(count), "steps"+str(count)]
      count += 1
  return ans

def aud_enable_channel(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Enable channel""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    ans["data"] = [23, 0, 0x85, config["channel"], 8]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None]
  return ans

def aud_disable_channel(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Disable channel""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    ans["data"] = [23, 0, 0x85, config["channel"], 9]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None]
  return ans

def aud_reset_channel(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Reset channel""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    ans["data"] = [23, 0, 0x85, config["channel"], 10]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None]
  return ans

def aud_seek(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Seek to position""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u24_default(ans, config, "position")
    ans["data"] = [23, 0, 0x85, config["channel"], 11, config["position"]]
    ans["size"] = [1, 1, 1, 1, 1, 3]
    ans["field"] = [None, None, None, "channel", None, "position"]
  return ans

def aud_set_duration(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set duration""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u24_default(ans, config, "duration")
    ans["data"] = [23, 0, 0x85, config["channel"], 12, config["duration"]]
    ans["size"] = [1, 1, 1, 1, 1, 3]
    ans["field"] = [None, None, None, "channel", None, "duration"]
  return ans

def aud_set_samplerate(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set sample rate""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    _u16_default(ans, config, "samplerate")
    ans["data"] = [23, 0, 0x85, config["channel"], 13, config["samplerate"]]
    ans["size"] = [1, 1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, "channel", None, "samplerate"]
  return ans

def aud_set_waveform_parameter(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("""Set channel waveform parameters""")
  if "render" in config:
    _u8_default(ans, config, "channel")
    param = _selectmap(ans, config, "parameter", ["duty","volume","frequency"],[0,2,3])
    if "value16" in config:
      param = param | 0x80 # set the high byte to indicate a 16-bit value
    ans["data"] = [23, 0, 0x85, config["channel"], 14, param]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "channel", None, "parameter"]
    if "value16" in config:
      _u16_default(ans, config, "value16")
      ans["data"].append(config["value16"])
      ans["size"].append(2)
      ans["field"].append("value16")
    else:
      _u8_default(ans, config, "value")
      ans["data"].append(config["value"])
      ans["size"].append(1)
      ans["field"].append("value")
  return ans

def buf_write_block(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Write block to a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _array_default(ans, config, "buffer")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 0]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "bufferid", None]
    bufdata = _bytearray16(config, config["buffer"], "buffer")
    _merge_dsf(ans, bufdata)
  return ans

def buf_call(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Call a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 1]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "bufferid", None]
  return ans

def buf_clear(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Clear a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 2]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "bufferid", None]
  return ans

def buf_create_writeable(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Create a writeable buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "length")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 3, config["length"]]
    ans["size"] = [1, 1, 1, 2, 1, 2]
    ans["field"] = [None, None, None, "bufferid", None, "length"]
  return ans

def buf_set_output_stream(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Set output stream to a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 4]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "bufferid", None]
  return ans

def buf_adjust_contents(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Adjust buffer contents")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    op_low = _selectmap(ans, config, "operation", ["not","neg","set","add","adc","and","or","xor"])
    op_hi = _flagmap(ans, config, "advanced", ["offset","buffetch","multitarget","multioperand"], [0x10,0x20,0x40,0x80])
    op = op_low | op_hi

    is_advanced_offset = (op & 0x10) == 0x10
    is_buffer_fetch = (op & 0x20) == 0x20
    is_counted = ((op & 0x40) == 0x40) or ((op & 0x80) == 0x80)
    is_multioperand = ((op & 0x80) == 0x80)

    ans["data"] = [23, 0, 0xA0, config["bufferid"], 5, op]
    ans["size"] = [1, 1, 1, 2, 1, 1]
    ans["field"] = [None, None, None, "bufferid", None, "operation"]

    _offset_default(ans, config, "offset", is_advanced_offset)
    _merge_dsf(ans, _offset(config["offset"], is_advanced_offset))

    if is_counted:
      if is_multioperand:
        # test to see if it is actually a sequence:
        if not (type(config["operand"]) is tuple or type(config["operand"]) is list):
          ans["log"].append("Operand is requested as a sequence type, but got "+str(type(config["operand"]))+". Replacing with zero.")
          config["operand"] = [0]
        # append count prelude
        ans["data"].append(len(config["operand"]))
        ans["size"].append(2)
        ans["field"].append("count")
        # then iterate over the sequence:
        for n in range(len(config["operand"])):
          _operand_default(ans, config["operand"], n, is_buffer_fetch, is_advanced_offset)
          _merge_dsf(ans, _operand(config["operand"][n], f'operand{n}', is_buffer_fetch, is_advanced_offset))
      else:
        # use the "count" parameter.
        _u16_default(ans, config, "count")
        ans["data"].append(config["count"])
        ans["size"].append(2)
        ans["field"].append("count")
        # just write the operand the one time
        _operand_default(ans, config, "operand", is_buffer_fetch, is_advanced_offset)
        _merge_dsf(ans, _operand(config["operand"], 'operand', is_buffer_fetch, is_advanced_offset))
    else:
      # also just write it the one time (but without the count)
      _operand_default(ans, config, "operand", is_buffer_fetch, is_advanced_offset)
      _merge_dsf(ans, _operand(config["operand"], 'operand', is_buffer_fetch, is_advanced_offset))


  return ans

def _cond_op(ans, config):
    op_low = _selectmap(ans, config, "operation", ["!=0","=0","=","!=","<",">","<=",">=","and","or"])
    op_hi = _flagmap(ans, config, "advanced", ["offset","buffetch"], [0x10,0x20])
    op = op_low | op_hi

    is_advanced_offset = (op & 0x10) == 0x10
    is_buffer_fetch = (op & 0x20) == 0x20

    return op, is_advanced_offset, is_buffer_fetch
  

def buf_condcall(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Conditionally call a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")

    op, is_advanced_offset, is_buffer_fetch = _cond_op(ans, config)

    ans["data"] = [23, 0, 0xA0, config["bufferid"], 6, op, config["checkbufferid"]]
    ans["size"] = [1, 1, 1, 2, 1, 2]
    ans["field"] = [None, None, None, "bufferid", None, "operation", "checkbufferid"]

    _offset_default(ans, config, "checkoffset", is_advanced_offset)
    _merge_dsf(ans, _offset(config["checkoffset"], is_advanced_offset))
  return ans

def buf_jump(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Jump to a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 7]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "bufferid", None]
  return ans

def buf_condjump(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Conditional Jump to a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "checkbufferid")

    op, is_advanced_offset, is_buffer_fetch = _cond_op(ans, config)

    ans["data"] = [23, 0, 0xA0, config["bufferid"], 8, op, config["checkbufferid"]]
    ans["size"] = [1, 1, 1, 2, 1, 1, 2]
    ans["field"] = [None, None, None, "bufferid", None, "checkbufferid"]
    
    _offset_default(ans, config, "checkoffset", is_advanced_offset)
    _merge_dsf(ans, _offset(config["checkoffset"], is_advanced_offset))

  return ans

def buf_jumpoffset(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Jump to an offset in a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _offset_default(ans, config, "offset", True)
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 9]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "bufferid", None]
    od = _offset(config["offset"], True)
    _merge_dsf(ans, od)
  return ans

def buf_condjumpoffset(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Conditional jump to an offset in a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "checkbufferid")
    _offset_default(ans, config, "offset", True)

    op, is_advanced_offset, is_buffer_fetch = _cond_op(ans, config)

    ans["data"] = [23, 0, 0xA0, config["bufferid"], 10]
    ans["size"] = [1, 1, 1, 2, 1, 1, 2]
    ans["field"] = [None, None, None, "bufferid", None]
    
    _offset_default(ans, config, "checkoffset", is_advanced_offset)
    _merge_dsf(ans, _offset(config["checkoffset"], is_advanced_offset))

    ans["data"].append(op) 
    ans["size"] = [1]
    ans["field"] = [None]
    ans["data"].append(config["checkbufferid"])
    ans["size"] = [2]
    ans["field"] = ["checkbufferid"]

  return ans

def buf_calloffset(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Call buffer with an offset")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _offset_default(ans, config, "offset", True)
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 11]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "bufferid", None]
    od = _offset(config["offset"], True)
    _merge_dsf(ans, od)
  return ans

def buf_condcalloffset(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Conditional call buffer with an offset")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "checkbufferid")
    _offset_default(ans, config, "offset", True)

    op, is_advanced_offset, is_buffer_fetch = _cond_op(ans, config)

    ans["data"] = [23, 0, 0xA0, config["bufferid"], 12]
    ans["size"] = [1, 1, 1, 2, 1, 1, 2]
    ans["field"] = [None, None, None, "bufferid", None]
    
    _offset_default(ans, config, "checkoffset", is_advanced_offset)
    _merge_dsf(ans, _offset(config["checkoffset"], is_advanced_offset))

    ans["data"].append(op) 
    ans["size"] = [1]
    ans["field"] = [None]
    ans["data"].append(config["checkbufferid"])
    ans["size"] = [2]
    ans["field"] = ["checkbufferid"]

  return ans

def buf_copyconcatblocks(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Copy blocks from multiple buffers into a single buffer")
  if "render" in config:
    _u16_default(ans, config, "targetbuffer")
    ans["data"] = [23, 0, 0xA0, config["targetbuffer"], 13]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "targetbuffer", None]
    _array_default(ans, config, "sourcebuffer")
    for n in range(len(config["sourcebuffer"])):
      _u16_default(ans, config["sourcebuffer"], n)
      ans["data"].append(config["sourcebuffer"][n])
      ans["size"].append(2)
      ans["field"].append(f'block{n}')
    ans["data"].append(65535)
    ans["size"].append(2)
    ans["field"].append(None)
  return ans

def buf_consolidate(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Consolidate blocks in a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 14]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "bufferid", None]
  return ans

def buf_split(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Split a buffer into multiple blocks")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "blocksize")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 15, config["blocksize"]]
    ans["size"] = [1, 1, 1, 2,1,2]
    ans["field"] = [None, None, None, "bufferid", None, "blocksize"]
  return ans

def buf_splitspread(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Split a buffer into multiple blocks and spread across multiple buffers")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "blocksize")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 16, config["blocksize"]]
    ans["size"] = [1, 1, 1, 2,1,2]
    ans["field"] = [None, None, None, "bufferid", None, "blocksize"]
    _array_default(ans, config, "targetbuffer")
    for n in range(len(config["targetbuffer"])):
      _u16_default(ans, config["targetbuffer"], n)
      ans["data"].append(config["targetbuffer"][n])
      ans["size"].append(2)
      ans["field"].append(f'block{n}')
    ans["data"].append(65535)
    ans["size"].append(2)
    ans["field"].append(None)
  return ans

def buf_splitspreadid(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Split a buffer and spread across blocks, starting at target buffer ID")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "blocksize")
    _u16_default(ans, config, "targetid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 17, config["blocksize"], config["targetid"]]
    ans["size"] = [1, 1, 1, 2,1,2,2]
    ans["field"] = [None, None, None, "bufferid", None, "blocksize","targetid"]
  return ans

def buf_splitwidth(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Split a buffer into blocks by width")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "width")
    _u16_default(ans, config, "blockcount")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 18, config["width"], config["blockcount"]]
    ans["size"] = [1, 1, 1, 2,1,2,2]
    ans["field"] = [None, None, None, "bufferid", None, "width","blockcount"]
  return ans

def buf_splitwidthspread(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Split by width into blocks and spread across target buffers")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "width")
    _u16_default(ans, config, "blockcount")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 19, config["width"]]
    ans["size"] = [1, 1, 1, 2,1,2]
    ans["field"] = [None, None, None, "bufferid", None, "width"]
  _array_default(ans, config, "targetbuffer")
  for n in range(len(config["targetbuffer"])):
    _u16_default(ans, config["targetbuffer"], n)
    ans["data"].append(config["targetbuffer"][n])
    ans["size"].append(2)
    ans["field"].append(f'block{n}')
  ans["data"].append(65535)
  ans["size"].append(2)
  ans["field"].append(None)
  return ans

def buf_splitspreadwidthid(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Split by width into blocks and spread across blocks starting at target buffer ID")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "width")
    _u16_default(ans, config, "blockcount")
    _u16_default(ans, config, "targetid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 20, config["width"], config["blockcount"],config["targetid"]]
    ans["size"] = [1, 1, 1, 2,1,2,2,2]
    ans["field"] = [None, None, None, "bufferid", None, "width","blockcount","targetid"]
  return ans

def buf_spread(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Spread blocks from a buffer across multiple target buffers")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 21]
    ans["size"] = [1, 1, 1, 1,2,1]
    ans["field"] = [None, None, None, "bufferid", None]
  _array_default(ans, config, "targetbuffer")
  for n in range(len(config["targetbuffer"])):
    _u16_default(ans, config["targetbuffer"], n)
    ans["data"].append(config["targetbuffer"][n])
    ans["size"].append(2)
    ans["field"].append(f'block{n}')
  ans["data"].append(65535)
  ans["size"].append(2)
  ans["field"].append(None)
  return ans

def buf_spreadid(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Spread blocks from a buffer across blocks starting at target buffer ID")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u16_default(ans, config, "targetid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 22, config["targetid"]]
    ans["size"] = [1, 1, 1, 2,1,2]
    ans["field"] = [None, None, None, "bufferid", None, "targetid"]
  return ans

def buf_reverseblocks(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Reverse the order of blocks in a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 23]
    ans["size"] = [1, 1, 1, 2,1]
    ans["field"] = [None, None, None, "bufferid", None]
  return ans

def buf_reversedata(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Reverse the order of data of blocks within a buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    opt = _flagmap(ans, config, "options", ["val16","val32","valvariable","chunksize","reverseblocks"], [0x01,0x02,0x03,0x04, 0x08])

    valsize = None
    if (opt & 0x03) == 0x03:
      valsize = "variable"
    elif (opt & 0x02) == 0x02:
      valsize = "32bit"
    elif (opt & 0x01) == 0x01:
      valsize = "16bit"
    else:
      valsize = "8bit"
    use_chunksize = (op & 0x04) == 0x04
    reverse_blocks = (op & 0x08) == 0x08 

    ans["data"] = [23, 0, 0xA0, config["bufferid"], 24, opt]
    ans["size"] = [1, 1, 1, 2,1,1]
    ans["field"] = [None, None, None, "bufferid", None, "options"]

    if valsize == "variable":
      _u16_default(ans, config, "valuesize")
      ans["data"].append(config["valuesize"])
      ans["size"].append(2)
      ans["field"].append("valuesize")
    if use_chunksize:
      _u16_default(ans, config, "chunksize")
      ans["data"].append(config["chunksize"])
      ans["size"].append(2)
      ans["field"].append("chunksize")

  return ans

def buf_copyreference(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Copy blocks from multiple buffers by reference")
  if "render" in config:
    _u16_default(ans, config, "targetbuffer")
    ans["data"] = [23, 0, 0xA0, config["targetbuffer"], 25]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "targetbuffer", None]
    _array_default(ans, config, "sourcebuffer")
    for n in range(len(config["sourcebuffer"])):
      _u16_default(ans, config["sourcebuffer"], n)
      ans["data"].append(config["sourcebuffer"][n])
      ans["size"].append(2)
      ans["field"].append(f'block{n}')
    ans["data"].append(65535)
    ans["size"].append(2)
    ans["field"].append(None)
  return ans

def buf_copyconsolidate(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Copy blocks from multiple buffers and consolidate")
  if "render" in config:
    _u16_default(ans, config, "targetbuffer")
    ans["data"] = [23, 0, 0xA0, config["targetbuffer"], 26]
    ans["size"] = [1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, "targetbuffer", None]
    _array_default(ans, config, "sourcebuffer")
    for n in range(len(config["sourcebuffer"])):
      _u16_default(ans, config["sourcebuffer"], n)
      ans["data"].append(config["sourcebuffer"][n])
      ans["size"].append(2)
      ans["field"].append(f'block{n}')
    ans["data"].append(65535)
    ans["size"].append(2)
    ans["field"].append(None)
  return ans

def buf_compress(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Compress a buffer")
  if "render" in config:
    _u16_default(ans, config, "targetid")
    _u16_default(ans, config, "sourceid")
    ans["data"] = [23, 0, 0xA0, config["targetid"], 64, config["sourceid"]]
    ans["size"] = [1, 1, 1, 2,1,2]
    ans["field"] = [None, None, None, "targetid", None, "sourceid"]
  return ans

def buf_decompress(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Decompress a buffer")
  if "render" in config:
    _u16_default(ans, config, "targetid")
    _u16_default(ans, config, "sourceid")
    ans["data"] = [23, 0, 0xA0, config["targetid"], 65, config["sourceid"]]
    ans["size"] = [1, 1, 1, 2,1,2]
    ans["field"] = [None, None, None, "targetid", None, "sourceid"]
  return ans

def buf_expandbitmap(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Expand a bitmap")
  if "render" in config:
    _u16_default(ans, config, "targetid")
    _bits_default(ans, config, "bits", 1, 8)

    bitlut = (None,1,2,3,4,5,6,7,0) # this call defines the bit pattern so that no bits set = 8 bits
    maplen = (None,2,4,8,16,32,64,128,256) # this is how many values are needed in the map for that bit width
    opt = bitlut[config["bits"]]
    if "width" in config:
      opt = opt | 0x03
    if "buffermap" in config:
      opt = opt | 0x04

    _u16_default(ans, config, "sourceid")

    ans["data"] = [23, 0, 0xA0, config["targetid"], 72, opt, config["sourceid"]]
    ans["size"] = [1, 1, 1, 2,1,2]
    ans["field"] = [None, None, None, "targetid", None, "sourceid"]

    if "width" in config["options"]:
      _u16_default(ans, config, "width")
      ans["data"].append(config["width"])
      ans["size"].append(2)
      ans["field"].append("width")
    if "buffermap" in config["options"]:
      _u16_default(ans, config, "buffermap")
      ans["data"].append(config["buffermap"])
      ans["size"].append(2)
      ans["field"].append("buffermap")
    elif len(config["map"]) == maplen[config["bits"]]:
      for n in range(maplen[config["bits"]]):
        ans["data"].append(config["bits"][n])
        ans["size"].append(1)
        ans["field"].append("map"+str(n))
    else:
      ans["log"].append(f'couldn\'t find a map or buffermap, filling in the map with an ascending sequence.')
      for n in range(maplen[config["bits"]]):
        ans["data"].append(n % 256)
        ans["size"].append(1)
        ans["field"].append("map"+str(n))

  return ans

def buf_debug(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Debug info command")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0xA0, config["bufferid"], 128]
    ans["size"] = [1, 1, 1, 2,1]
    ans["field"] = [None, None, None, "bufferid", None]
  return ans

# TODO: command 32, 33, 34, 40, 41 (experimental)

def bmp_select8(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Select bitmap n (8-bit)")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 27, 0, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def bmp_load8(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Load colour bitmap data into current bitmap (8-bit id, RGBA8888)")
  if "render" in config:
    _u8_default(ans, config, "w")
    _u8_default(ans, config, "h")
    _array_default(ans, config, "data")
    ans["data"] = [23, 27, 1, config["w"], config["h"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "w", "h"]
    if "data" in config:
      xlength = config["w"] * config["h"]
      if len(config["data"]) == xlength:
        count = 0
        for n in config["data"]:
          ans["data"].append(n)
          ans["size"].append(1)
          ans["field"].append("n"+str(count))
          count += 1
      else:
        ans["log"].append(f'length of bitmap data{len(config["data"])} is a mismatch for given size {config["w"]} x {config["h"]} = {xlength}. Appending ascending values instead.')
    else:
      pass

  return ans

def bmp_capture8(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Capture screen data into bitmap n (8-bit)")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 27, 1, config["n"], 0, 0]
    ans["size"] = [1, 1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "n", None, None]
  return ans

def bmp_makerect(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Create a solid colour rectangular bitmap")
  if "render" in config:
    _u16_default(ans, config, "w")
    _u16_default(ans, config, "h")
    _u32_default(ans, config, "col")
    ans["data"] = [23, 27, 2, config["w"], config["h"], config["col"]]
    ans["size"] = [1, 1, 1, 2, 2, 4]
    ans["field"] = [None, None, None, "w", "h", "col"]
  return ans

def bmp_draw(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Draw current bitmap on screen at pixel position x, y")
  if "render" in config:
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [23, 27, 3, config["x"], config["y"]]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "x", "y"]
  return ans

def bmp_select16(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Select bitmap n (16-bit)")
  if "render" in config:
    _u16_default(ans, config, "n")
    ans["data"] = [23, 27, 0x20, config["n"]]
    ans["size"] = [1, 1, 1, 2]
    ans["field"] = [None, None, None, "n"]
  return ans

def bmp_makefrombuffer(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Create bitmap from selected buffer")
  if "render" in config:
    _u16_default(ans, config, "w")
    _u16_default(ans, config, "h")
    bformat = _selectmap(ans, config, "format", ["rgba8888", "rgba2222", "monomask", "_reserved"])
    ans["data"] = [23, 27, 0x21, config["w"], config["h"], bformat]
    ans["size"] = [1, 1, 1, 2, 2, 1]
    ans["field"] = [None, None, None, "w", "h", "format"]
  return ans

def bmp_capture16(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Capture screen data into bitmap n (16-bit)")
  if "render" in config:
    _u16_default(ans, config, "n")
    ans["data"] = [23, 27, 0x21, config["n"], 0]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "n", None]
  return ans

def spr_select(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Select sprite n")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 27, 4, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def spr_clear(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Clear frames in current sprite")
  if "render" in config:
    ans["data"] = [23, 27, 5]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def spr_append8(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Add bitmap n as a frame to current sprite (where bitmap's buffer ID is 64000+n)")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 27, 6, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def spr_activate(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Activate n sprites")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 27, 7, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def spr_next(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Select next frame of current sprite")
  if "render" in config:
    ans["data"] = [23, 27, 8]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def spr_prev(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Select previous frame of current sprite")
  if "render" in config:
    ans["data"] = [23, 27, 9]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def spr_frame(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Select the nth frame of current sprite")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 27, 10, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def spr_show(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Show current sprite")
  if "render" in config:
    ans["data"] = [23, 27, 11]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def spr_hide(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Hide current sprite")
  if "render" in config:
    ans["data"] = [23, 27, 12]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def spr_absmove(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Move current sprite to pixel position x, y")
  if "render" in config:
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [23, 27, 13, config["x"], config["y"]]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "x", "y"]
  return ans

def spr_relmove(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Move current sprite by x, y pixels")
  if "render" in config:
    _u16_default(ans, config, "x")
    _u16_default(ans, config, "y")
    ans["data"] = [23, 27, 14, config["x"], config["y"]]
    ans["size"] = [1, 1, 1, 2, 2]
    ans["field"] = [None, None, None, "x", "y"]
  return ans

def spr_update(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Update the sprites in the GPU")
  if "render" in config:
    ans["data"] = [23, 27, 15]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def spr_resetall(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Reset bitmaps and sprites and clear all data")
  if "render" in config:
    ans["data"] = [23, 27, 16]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def spr_resetspr(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Reset sprites (only) and clear all data")
  if "render" in config:
    ans["data"] = [23, 27, 17]
    ans["size"] = [1, 1, 1]
    ans["field"] = [None, None, None]
  return ans

def spr_gcol(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Set the current sprite GCOL paint mode to n")
  if "render" in config:
    _u8_default(ans, config, "n")
    ans["data"] = [23, 27, 18, config["n"]]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, "n"]
  return ans

def spr_append16(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Add bitmap n as a frame to current sprite using a 16-bit buffer ID")
  if "render" in config:
    _u16_default(ans, config, "n")
    ans["data"] = [23, 27, 0x26, config["n"]]
    ans["size"] = [1, 1, 1, 2]
    ans["field"] = [None, None, None, "n"]
  return ans

def spr_cursor(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Setup a mouse cursor")
  if "render" in config:
    _u8_default(ans, config, "hotx")
    _u8_default(ans, config, "hoty")
    ans["data"] = [23, 27, 0x40, config["hotx"], config["hoty"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, "hotx", "hoty"]
  return ans

def ctx_select(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Select context stack")
  if "render" in config:
    _u8_default(ans, config, "contextid")
    ans["data"] = [23, 0, 0xC8, 0, config["contextid"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, None, "contextid"]
  return ans

def ctx_delete(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Delete context stack")
  if "render" in config:
    _u8_default(ans, config, "contextid")
    ans["data"] = [23, 0, 0xC8, 1, config["contextid"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, None, "contextid"]
  return ans

def ctx_reset(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Reset")
  if "render" in config:
    ans["data"] = [23, 0, 0xC8, 2]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def ctx_save(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Save context")
  if "render" in config:
    ans["data"] = [23, 0, 0xC8, 3]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def ctx_restore(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Restore context")
  if "render" in config:
    ans["data"] = [23, 0, 0xC8, 4]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def ctx_saveselect(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Save and select a copy of a context")
  if "render" in config:
    _u8_default(ans, config, "contextid")
    ans["data"] = [23, 0, 0xC8, 5, config["contextid"]]
    ans["size"] = [1, 1, 1, 1, 1]
    ans["field"] = [None, None, None, None, "contextid"]
  return ans

def ctx_restoreall(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Restore all")
  if "render" in config:
    ans["data"] = [23, 0, 0xC8, 6]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def ctx_clear(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Clear stack")
  if "render" in config:
    ans["data"] = [23, 0, 0xC8, 7]
    ans["size"] = [1, 1, 1, 1]
    ans["field"] = [None, None, None, None]
  return ans

def font_select(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Select font")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    flags = _flagmap(ans, config, "flags", 
      ["align_baseline","_reserved1","_reserved2","_reserved3","_reserved4","_reserved5","_reserved6","_reserved7"],
      [1,2,4,8,16,32,64,128])
    ans["data"] = [23, 0, 0x95, 0, config["bufferid"], flags]
    ans["size"] = [1, 1, 1, 1, 2, 1]
    ans["field"] = [None, None, None, None, "bufferid", "flags"]
  return ans

def font_create(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Create font from buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    _u8_default(ans, config, "width")
    _u8_default(ans, config, "height")
    _u8_default(ans, config, "ascent")
    _u8_default(ans, config, "flags")
    ans["data"] = [23, 0, 0x95, 1, config["bufferid"], config["width"], config["height"], config["ascent"], config["flags"]]
    ans["size"] = [1, 1, 1, 1, 2, 1, 1, 1, 1]
    ans["field"] = [None, None, None, None, "bufferid", "width", "height", "ascent", "flags"]
  return ans

def font_property(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Set or adjust font property")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    field = _selectmap(ans, config, "field", ["width", "height", "ascent", "flags", "_bufferchar", "_pointsize", "_inleading", "_exleading", "_weight", "_charset", "_codepage"])
    _u16_default(ans, config, "value")
    ans["data"] = [23, 0, 0x95, 2, config["bufferid"], field, config["value"]]
    ans["size"] = [1, 1, 1, 1, 2, 1, 2]
    ans["field"] = [None, None, None, None, "bufferid", "field", "value"]
  return ans

def font_clear(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Clear/Delete font")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0x95, 4, config["bufferid"]]
    ans["size"] = [1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, None, "bufferid"]
  return ans

def font_copysystem(config):
  ans = {"log":[],"doc":[]}
  if "doc" in config:
    ans["doc"].append("Copy system font to buffer")
  if "render" in config:
    _u16_default(ans, config, "bufferid")
    ans["data"] = [23, 0, 0x95, 5, config["bufferid"]]
    ans["size"] = [1, 1, 1, 1, 2]
    ans["field"] = [None, None, None, None, "bufferid"]
  return ans

def render_offsets(ans):
  offset = 0
  ans["offset"] = []
  for n in ans["size"]:
    ans["offset"].append(offset)
    offset += n
  return ans

def render_bytes(ans):
  ans["bytes"] = []
  if len(ans["data"])!=len(ans["size"]):
    ans["log"].append(f'Mismatched length of data({len(ans["data"])}) vs size({len(ans["size"])}). Will not render bytes.')
    ans["bytes"] = b''
  else:
    for n in range(len(ans["data"])):
      size = ans["size"][n]
      rawd = ans["data"][n]
      if (rawd < 0): # negative value handling...perhaps there is a better way of dealing with this
        if size==1:
          rawd += 32768
        elif size==2:
          rawd += 65536
        elif size==3:
          rawd += 16777216
        elif size==4:
          rawd += 4294967296
        else:
          print(ans["data"])
          raise Exception("I don't know how to deal with a negative value ("+str(rawd)+") of size "+str(size))
      ans["bytes"].append(rawd.to_bytes(size, byteorder='little'))
    ans["bytes"] = b''.join(ans["bytes"])
  return ans

def process(configs):
  optable = {
    "vdu_null":vdu_null,
    "vdu_printernext":vdu_printernext,
    "vdu_printerenable":vdu_printerenable,
    "vdu_printerdisable":vdu_printerdisable,
    "vdu_writetext":vdu_writetext,
    "vdu_writegraphics":vdu_writegraphics,
    "vdu_enablescreen":vdu_enablescreen,
    "vdu_beep":vdu_beep,
    "vdu_back":vdu_back,
    "vdu_forward":vdu_forward,
    "vdu_down":vdu_down,
    "vdu_up":vdu_up,
    "vdu_cls":vdu_cls,
    "vdu_cr":vdu_cr,
    "vdu_pageon":vdu_pageon,
    "vdu_pageoff":vdu_pageoff,
    "vdu_clg":vdu_clg,
    "vdu_colour":vdu_colour,
    "vdu_colourmode":vdu_colourmode,
    "vdu_colourlogical":vdu_colourlogical,
    "vdu_colourreset":vdu_colourreset,
    "vdu_screendisable":vdu_screendisable,
    "vdu_screenmode":vdu_screenmode,
    "vdu_charredefine":vdu_charredefine,
    "vdu_cursorcontrol":vdu_cursorcontrol,
    "vdu_dottedlineredefine":vdu_dottedlineredefine,
    "vdu_scroll":vdu_scroll,
    "vdu_cursormovementredefine":vdu_cursormovementredefine,
    "vdu_linethickness":vdu_linethickness,
    "vdu_hexload":vdu_hexload,
    "vdu_graphicsviewport":vdu_graphicsviewport,
    "vdu_plot":vdu_plot,
    "vdu_resetviewports":vdu_resetviewports,
    "vdu_charoutput":vdu_charoutput,
    "vdu_textviewport":vdu_textviewport,
    "vdu_graphicsorigin":vdu_graphicsorigin,
    "vdu_home":vdu_home,
    "vdu_cursormove":vdu_cursormove,
    "vdu_backspace":vdu_backspace,
    "aud_playnote":aud_playnote,
    "aud_status":aud_status,
    "aud_set_volume":aud_set_volume,
    "aud_set_frequency":aud_set_frequency,
    "aud_set_waveform":aud_set_waveform,
    "aud_loadsample":aud_loadsample,
    "aud_clearsample":aud_clearsample,
    "aud_samplefrombuffer":aud_samplefrombuffer,
    "aud_set_samplebasefrequency":aud_set_samplebasefrequency,
    "aud_set_samplebufferbasefrequency":aud_set_samplebufferbasefrequency,
    "aud_set_samplerepeatstart":aud_set_samplerepeatstart,
    "aud_set_samplebufferrepeatstart":aud_set_samplebufferrepeatstart,
    "aud_set_samplerepeatlength":aud_set_samplerepeatlength,
    "aud_set_samplebufferrepeatlength":aud_set_samplebufferrepeatlength,
    "aud_disable_envelope":aud_disable_envelope,
    "aud_adsr":aud_adsr,
    "aud_multiphase_adsr":aud_multiphase_adsr,
    "aud_freqenv_off":aud_freqenv_off,
    "aud_freqenv_stepped":aud_freqenv_stepped,
    "aud_enable_channel":aud_enable_channel,
    "aud_disable_channel":aud_disable_channel,
    "aud_reset_channel":aud_reset_channel,
    "aud_seek":aud_seek,
    "aud_set_duration":aud_set_duration,
    "aud_set_samplerate":aud_set_samplerate,
    "aud_set_waveform_parameter":aud_set_waveform_parameter,
    "buf_write_block":buf_write_block,
    "buf_call":buf_call,
    "buf_clear":buf_clear,
    "buf_create_writeable":buf_create_writeable,
    "buf_set_output_stream":buf_set_output_stream,
    "buf_adjust_contents":buf_adjust_contents,
    "buf_condcall":buf_condcall,
    "buf_jump":buf_jump,
    "buf_condjump":buf_condjump,
    "buf_jumpoffset":buf_jumpoffset,
    "buf_condjumpoffset":buf_condjumpoffset,
    "buf_condcall":buf_condcall,
    "buf_condcalloffset":buf_condcalloffset,
    "buf_copyconcatblocks":buf_copyconcatblocks,
    "buf_consolidate":buf_consolidate,
    "buf_split":buf_split,
    "buf_splitspread":buf_splitspread,
    "buf_splitspreadid":buf_splitspreadid,
    "buf_splitwidth":buf_splitwidth,
    "buf_splitwidthspread":buf_splitwidthspread,
    "buf_splitspreadwidthid":buf_splitspreadwidthid,
    "buf_spread":buf_spread,
    "buf_spreadid":buf_spreadid,
    "buf_reverseblocks":buf_reverseblocks,
    "buf_reversedata":buf_reversedata,
    "buf_copyreference":buf_copyreference,
    "buf_copyconsolidate":buf_copyconsolidate,
    "buf_compress":buf_compress,
    "buf_decompress":buf_decompress,
    "buf_expandbitmap":buf_expandbitmap,
    "buf_debug":buf_debug,
    "sys_terminal":sys_terminal,
    "sys_consolemode":sys_consolemode,
    "sys_testflagclear":sys_testflagclear,
    "sys_testflag":sys_testflag,
    "sys_dotdashlength":sys_dotdashlength,
    "sys_logicalscaling":sys_logicalscaling,
    "sys_updatevdp":sys_updatevdp,
    "sys_graphicsoriginviewfromcursor":sys_graphicsoriginviewfromcursor,
    "sys_graphicsoriginfromplot":sys_graphicsoriginfromplot,
    "sys_graphicsviewportfromplot":sys_graphicsviewportfromplot,
    "sys_textviewportfromplot":sys_textviewportfromplot,
    "sys_printbuffer":sys_printbuffer,
    "sys_controlkeystoggle":sys_controlkeystoggle,
    "sys_get_palettecolour":sys_get_palettecolour,
    "sys_get_graphicscode":sys_get_graphicscode,
    "sys_cursorrelmove":sys_cursorrelmove,
    "sys_resetsysfont":sys_resetsysfont,
    "sys_charredefine":sys_charredefine,
    "sys_charbitmap":sys_charbitmap,
    "sys_cursorendcol":sys_cursorendcol,
    "sys_cursorstartcol":sys_cursorstartcol,
    "sys_mousewheelacceleration":sys_mousewheelacceleration,
    "sys_mouseacceleration":sys_mouseacceleration,
    "sys_mousescaling":sys_mousescaling,
    "sys_mouseresolution":sys_mouseresolution,
    "sys_mousesamplerate":sys_mousesamplerate,
    "sys_mouseposition":sys_mouseposition,
    "sys_mousecursor":sys_mousecursor,
    "sys_mousereset":sys_mousereset,
    "sys_mousedisable":sys_mousedisable,
    "sys_mouseenable":sys_mouseenable,
    "sys_keyboardctl":sys_keyboardctl,
    "sys_set_rtc":sys_set_rtc,
    "sys_get_rtc":sys_get_rtc,
    "sys_get_screendimensions":sys_get_screendimensions,
    "sys_get_pixelcolour":sys_get_pixelcolour,
    "sys_get_textcode":sys_get_textcode,
    "sys_get_textpos":sys_get_textpos,
    "sys_keyboardlocale":sys_keyboardlocale,
    "sys_poll":sys_poll,
    "sys_cursorend":sys_cursorend,
    "sys_cursorstart":sys_cursorstart,
    "mode_logicalscale":mode_logicalscale,
    "mode_legacy":mode_legacy,
    "mode_swap":mode_swap,
    "mode_flush":mode_flush,
    "bmp_select8":bmp_select8,
    "bmp_load8":bmp_load8,
    "bmp_capture8":bmp_capture8,
    "bmp_makerect":bmp_makerect,
    "bmp_draw":bmp_draw,
    "bmp_select16":bmp_select16,
    "bmp_makefrombuffer":bmp_makefrombuffer,
    "spr_select":spr_select,
    "spr_clear":spr_clear,
    "spr_append8":spr_append8,
    "spr_activate":spr_activate,
    "spr_next":spr_next,
    "spr_prev":spr_prev,
    "spr_frame":spr_frame,
    "spr_show":spr_show,
    "spr_hide":spr_hide,
    "spr_absmove":spr_absmove,
    "spr_relmove":spr_relmove,
    "spr_update":spr_update,
    "spr_resetall":spr_resetall,
    "spr_resetspr":spr_resetspr,
    "spr_gcol":spr_gcol,
    "spr_append16":spr_append16,
    "spr_cursor":spr_cursor,
    "ctx_select":ctx_select,
    "ctx_delete":ctx_delete,
    "ctx_reset":ctx_reset,
    "ctx_save":ctx_save,
    "ctx_restore":ctx_restore,
    "ctx_saveselect":ctx_saveselect,
    "ctx_restoreall":ctx_restoreall,
    "ctx_clear":ctx_clear,
    "font_select":font_select,
    "font_create":font_create,
    "font_property":font_property,
    "font_clear":font_clear,
    "font_copysystem":font_copysystem,
  }
  ans = []
  for n in configs:
    na = optable[n["command"]](n)
    na["command"] = n["command"]
    if "render" in n:
      if n["render"] == "bytes":
        render_bytes(na)
      elif n["render"] == "offsets":
        render_offsets(na)
    ans.append(na)
  return ans

def bytesize_of_bformat_line(bformat, line_width):
  """Returns the size(in bytes) of the indicated line width in the indicated format. FIXME unused""" 
  if bformat == "RGBA8888":
    return line_width * 4
  elif bformat == "RGBA2222":
    return line_width
  else:
    raise Exception("unrecognized bitmap color format: "+str(bformat)) 
    return None

class PreparedBitmap(object):
  def __init__(self, img, bformat, x, y, bufferid, attach=[], blocksize=65535):
    """Takes a PIL/Pillow image, bitmapformat string(e.g. "RGBA2222"), x, y, bufferid, blocksize as input.
    This is an asset definition that helps describe more of the properties of a bitmap before it's broken down into commands.
    x and y values may be used as offsets for large/composited images.
    If x and y will be reassigned later, their values may be ignored; 
    """
    self.img = PreparedBitmap.downcolor(img)
    self.x = x
    self.y = y
    self.w = img.width
    self.h = img.height
    self.attach = attach
    self.bufferid = bufferid
    self.bformat = bformat
    self.blocksize = blocksize
  def __repr__(self):
    return f'<PreparedBitmap #{self.bufferid} {self.bformat} ({self.x} {self.y} {self.w} {self.h} {self.attach})>'
  def downcolor(img):
    img = img.convert('RGBA')
    img = img.point(lambda p: p // 85 * 85)
    return img
  def splitImage(img, bformat, start_bufferid, frame=(128,128), mode="tile", origin=None, attach_shared={}, attach_frame={}):
    """Splits one large tiled image into multiple by the indicated frame size, and assigns them unique ascending ids.
    In mode=("tile",) the exact size of the tile is preserved and the X and Y values are assigned to their location in
      the original sheet.
    In mode=("trim", originx, originy) the tiles are trimmed by the bounding box determined by alpha value. The
      X and Y values are assigned relative to the provided originx and originy, so that the tiles remain centered if drawn
      using the X and Y adjustments. If the majority of the tiles are uncropped, a warning will be logged to errlog.
    """
    import math
    x0 = 0
    y0 = 0    
    count = 0
    ans = []
    errlog = []
    trimwarning = 0
    while y0 + frame[0] <= img.height:
      x1 = min(img.width, x0 + frame[0])
      y1 = min(img.height, y0 + frame[1])
      box = (x0, y0, x1, y1)
      absxy = (x0,y0)
      if origin is None:
        relxy = (0,0)
      else:
        relxy = (-origin[0], -origin[1])
      attach = []
      for k in attach_shared.keys():
        attach.append((k,attach_shared[k]))
      if count in attach_frame:
        aframe = attach_frame[count]
        for k in aframe.keys():
          v = aframe[k]
          attach.append((k,v[0]-absxy[0]+relxy[0],v[1]-absxy[1]+relxy[1]))
      if mode == "tile":
        ans.append(PreparedBitmap(img.crop(box), bformat, 
          absxy[0]+relxy[0],absxy[1]+relxy[1], 
          start_bufferid+count, attach))
      elif mode == "trim":
        tile = img.crop(box)
        cbox = tile.getbbox()
        print(tile,cbox)
        absw, absh = (cbox[2]-cbox[0], cbox[3]-cbox[1])
        if absw == tile.width and absh == tile.height:
          trimwarning += 1
        ans.append(PreparedBitmap(tile.crop(cbox), bformat,
          cbox[0]+relxy[0],cbox[1]+relxy[1], 
          start_bufferid+count, attach))
      x0 = x0 + frame[0]
      if x0 >= img.width:
        x0 = 0
        y0 = y0 + frame[1]
      count += 1
    if trimwarning > count // 2:
      errlog.append(f'WARNING: {trimwarning}/{count} images in this trimmed sheet are square. The source image may have an incorrect alpha channel.')
    return ans, errlog

def rgba8888_to_rgba2222(img):
  """Reduce a PIL/Pillow RGBA8888 image to a list of packed RGBA2222 bytes."""
  ans = [] 
  for r,g,b,a in (img.getdata()):
    packed = ((a >> 6) << 6) + ((b >> 6) << 4) + ((g >> 6) << 2) + (r >> 6)
    ans.append(packed)
  return ans

"""The cmd_ functions are preset functions for generating common sequences of commands."""

def cmd_upload_blocks(bytebuffer, bufferid, blocksize=65535, then_consolidate=True):
  """Generate commands to write blocks from a byte buffer, automatically clearing the buffer and 
  splitting the blocks at the indicated size."""
  if blocksize > 65535 or blocksize < 1:
    raise Exception(f'Block size {blocksize} is out of range, expected between 1 and 65535')
  idx = 0
  ans = []
  ans.append({"command":"buf_clear","bufferid":bufferid,"render":"bytes"})
  while idx < len(bytebuffer):
    byteslice = bytebuffer[idx:idx+blocksize]
    ans.append({"command":"buf_write_block","bufferid":bufferid,"buffer":byteslice,"render":"bytes"})
    idx += blocksize
  if len(ans)>1 and then_consolidate:
    ans.append({"command":"buf_consolidate","bufferid":bufferid,"render":"bytes"})
  return ans

def cmd_upload_blocks2(blockbuffer, bufferid, then_consolidate=False):
  """Generate commands to write blocks of premade size to a buffer id."""
  idx = 0
  ans = []
  ans.append({"command":"buf_clear","bufferid":bufferid,"render":"bytes"})
  while idx < len(blockbuffer):
    bk = blockbuffer[idx]
    blocksize = len(bk)
    if blocksize > 65535 or blocksize < 1:
      raise Exception(f'Block size {blocksize} is out of range, expected between 1 and 65535')
    ans.append({"command":"buf_write_block","bufferid":bufferid,"buffer":bk,"render":"bytes"})
    idx += 1
  if len(ans)>1 and then_consolidate:
    ans.append({"command":"buf_consolidate","bufferid":bufferid,"render":"bytes"})
  return ans

def cmd_testsample(channel, bufferid, base_rate, playback_rate):
  ans = []
  ans.append({"command":"aud_samplefrombuffer","format":"unsigned8","channel":channel,"bufferid":bufferid,
    "sampletuning":True,"render":"bytes"})
  ans.append({"command":"aud_set_samplebufferbasefrequency","channel":channel,"bufferid":bufferid,
    "frequency":base_rate,"render":"bytes"})
  ans.append({"command":"aud_set_waveform","channel":channel,"waveform":"sample","bufferid":bufferid,"render":"bytes"})
  ans.append({"command":"aud_playnote","channel":channel,"volume":127,"frequency":playback_rate,"duration":5000,"render":"bytes"})
  return ans

def cmd_upload_preparedbitmaps(pbitmaps):
  """Automatically upload the indicated PreparedBitmaps, and prepare them as bitmaps.
    """
  ans = []
  for n in pbitmaps:
    if n.bformat == "RGBA2222":
      ans += cmd_upload_blocks(rgba8888_to_rgba2222(n.img), n.bufferid, n.blocksize)
    else:
      raise Exception('unsupported bitmap format: '+str(n.bformat))
    ans.append({"command":"bmp_select16","n":n.bufferid,"render":"bytes"})
    ans.append({"command":"bmp_makefrombuffer","w":n.w,"h":n.h,"format":n.bformat,"render":"bytes"})
  return ans


def cmd_generate_bitmap(bitmapid, w, h, col):
  """Generate a filled rectangle bitmap with the given color(RGBA8888)."""
  ans = []
  ans.append({"command":"bmp_select16","n":bitmapid,"render":"bytes"})
  ans.append({"command":"bmp_makerect","w":w,"h":h,"col":col,"render":"bytes"})
  return ans

def cmd_display_bitmaps(pbitmaps):
  """Demonstrate display of one or more prepared bitmap assets after they've been uploaded and assigned
  using cmd_upload_preparedbitmaps()."""
  ans = []
  for n in pbitmaps:
    ans.append({"command":"bmp_select16","n":n.bufferid,"render":"bytes"})
    ans.append({"command":"bmp_draw","x":n.x,"y":n.y,"render":"bytes"})
  ans.append({"command":"mode_swap","render":"bytes"})
  return ans

def cmd_bitmaps_to_tiled_font(pbitmaps, fontbuffer, contextid):
  """Assigns a set of (previously uploaded) PreparedBitmaps to the indicated font buffer and context id. 
  It assigns all 256 characters, looping if there aren't
  enough tiles available. The first bitmap's size is used to determine the font size."""
  commands = []
  commands.append({"command":"font_copysystem","bufferid":fontbuffer,"render":"bytes"})
  commands.append({"command":"font_property","bufferid":fontbuffer,"field":"width","value":pbitmaps[0].w,"render":"bytes"})
  commands.append({"command":"font_property","bufferid":fontbuffer,"field":"height","value":pbitmaps[0].h,"render":"bytes"})
  commands.append({"command":"font_select","flags":[],"bufferid":fontbuffer,"render":"bytes"})
  commands.append({"command":"ctx_select","contextid":contextid,"render":"bytes"})
  for n in range(256):
    tb = pbitmaps[n % len(pbitmaps)]
    commands.append({"command":"sys_charbitmap","char":n,"bitmapid":tb.bufferid,"render":"bytes"})  
  return commands

def cmd_upload_font_tileset(ipath, bitmap_start_bufferid, font_bufferid, contextid, frame, iformat="RGBA2222"):
  """Open an image and generate the commands needed to upload the tiles as a font."""
  from PIL import Image
  ifile = Image.open(ipath)
  tilebmps, errlog = PreparedBitmap.splitImage(ifile, iformat, bitmap_start_bufferid, frame, mode="tile", 
  origin=None)
  commands = cmd_upload_preparedbitmaps(tilebmps) + cmd_bitmaps_to_tiled_font(tilebmps, font_bufferid, contextid)
  return {"pbmps":tilebmps, "src":ifile, "log":errlog, "commands":commands}

def cmd_hello_world(text="Hello world"):
  ans = []
  for n in range(len(text)):
    ans.append({"command":"vdu_charoutput","char":ord(text[n]), "render":"bytes"})
  return ans

class VDPBufferAllocator(object):
  def __init__(self):
    self.tab = {}
    self.cells = {}
    self.stores = {}
  def define(self, allocid, start, length=1):
    for n in range(start, start+length):
      if n in self.cells:
        raise Exception("Allocation of \""+str(allocid)+"\" overlaps with \""+str(self.cells[n])+"\"")
      else:
        self.cells[n] = allocid
        if allocid in self.tab:
          self.tab[allocid].append(n)
        else:
          self.tab[allocid] = [n]
  def store(self, allocid, searchid, value):
    if not allocid in self.tab:
      raise Exception("Storage to \""+str(allocid)+"\" needs to be define()'d first")
    else:
      for n in self.tab[allocid]:
        if not (n in self.stores):
          self.stores[n] = (searchid, value)
          return
      raise Exception("Storage to \""+str(allocid)+"\" will not fit - clear() it first")
  def clear(self, allocid):
    for n in self.tab[allocid]:
      del self.stores[n]
  def search(self, searchid):
    for k in self.stores:
      v = self.stores[k]
      if v[0] == searchid:
        return {"allocid":self.cells[k],"bufferid":k,"searchid":v[0],"value":v[1]}
    return None
  def __repr__(self):
    return f'<VDPBufferAllocator {len(self.tab)} definitions, {len(self.stores)} stored buffers>'

def init_path(path):
  import os
  try:
    os.mkdir(path)
  except:
    pass

def writevdu(path, commands):
  errlog = []
  fw = open(path,'wb')
  count = 0
  for n in process(commands):
    if len(n["log"])>0:
      errlog.append("command "+str(count+1))
      errlog.append(print(n))
    count += fw.write(n["bytes"])
  fw.close()
  return {"path":path,"log":errlog,"size":count}


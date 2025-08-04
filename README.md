# VDPTypes for Agon Computer

VDPTypes is a Python library that assists in generating VDU protocol data for the Agon computing platform's VDP (Visual Display Processor).
It supports Console8 as of version 2.12.0, minus some experimental API calls. Not all calls have yet been tested.

Contributions are appreciated, my bandwidth to work on Agon projects is limited.

## About

VDPTypes is a support library made for customized build scripts, asset conversion, and development of VDP buffer programs. It includes:

* Utility code for loading and converting assets to VDP formats
* VDP-IL, an intermediate language for VDU commands using Python data structures, giving them some syntax and automatic checking
* Code generation for several language targets on Agon

## Dependencies

* Tested on Python 3.12.10
* Optionally, Pillow ( `pip install pillow` )
* Optionally, sox_ng ( see below )

## Basic Operation

To begin, copy in vdptypes.py and add the line '''import vdptypes''' in your script.

Then create a commands list and start appending commands, e.g.

```
  commands = []
  commands.append({"command":"vdu_screenmode","mode":20,"render":"bytes"}) # switch to screen mode 20, render the command to bytes
  vdptypes.writevdu("screenmode.vdu", commands) # write the bytes to a .vdu file
```

This translates the command, written in VDP-IL's Python format, to a file containing two bytes: (22, 20).

Alternately, vdptypes.process() can be used to examine or manipulate the output as a list of dicts before writing it.
If a command has been misconfigured it will show up under the "errors" field of process()'s answer for that command.

Some commands variable quantities of data: Lists are used in this case.

Some commands contain a enumerated selection of values: These fields are supplied as string parameters.

Some commands contain enumerated flags, which may be combined together: These fields use a list of strings.

Some commands contain optional fields: If the fields are used, the command will use a different mode.

As of right now, there is no API documentation for the intermediate language: The implementation is defined per-command and is ideosyncratic, like the command set it's based around.
You'll have to look at the code, find the API that matches the one in the Console8 docs, and read it to learn what to supply for each command.

## Buffer Allocation

VDPBufferAllocator is a class that assists with managing assignments for your buffer assets:

```
alloc = VDPBufferAllocator()
buffer_base_id = 100
buffer_length = 10
alloc.define("my_buf", buffer_base_id, buffer_length) # allocates 10 spaces from buffer id 100 to 109 with the name "my_buf"
bmp1 = PreparedBitmap(...)
alloc.store("my_buf", "bmp1", bmp1) # stores the bitmap to the first available entry in "my_buf"
ans = alloc.search("bmp1") # returns a dict with all the info about our stored "bmp1"
print(ans["allocid"]) # "my_buf"
print(ans["bufferid"]) # 100
print(ans["searchid"]) # "bmp1"
print(ans["value"]) # <PreparedBitmap ...>
alloc.clear("my_buf") # keeps the definition, but removes all the stored data (e.g. data overlays, new scenes)
```

## Processing Images

VDPTypes contains some utilities for converting bitmap images into assets defined as a .vdu file.

PreparedBitmap() is a class that uses an image loaded from the Pillow library and attaches additional data to it.

cmd_upload_preparedbitmaps() will return commands to upload each of the bitmaps and prepare them for use.

## Processing Audio

VDPTypes uses sox_ng for audio conversion.

sox_ng is available from [Codeberg](https://codeberg.org/sox_ng/sox_ng).

## Executing .vdu files in AgDev C

TODO: AgDev is available from (...)

## Executing .vdu files in Agon Forth

Agon Forth is available from [Github](https://github.com/lennart-benschop/agon-forth).

examples.py contains some example usage for loading files and uploading them to the VDP.

## Executing .vdu files in BBC Basic

TODO: BBC Basic 

## Executing .vdu files in eZ80 Assembly

TODO: Assembly

## Examples

See examples.py

## Credits

By James W. Hofmann (c) 2025.

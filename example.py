#!/usr/bin/env python3

from vdptypes import *

def demo0():  
  print(aud_multiphase_adsr({"render":"bytes","release":[(10,30)]}))
  print(buf_write_block({"buffer":[1,2,3,4,0,1,2,3],"render":"bytes"}))
  print(buf_adjust_contents({"bufferid":12,"operation":"set","advanced":["offset","multitarget","multioperand"],"render":"bytes","offset":32,"operand":[3,4,5]}))
  print(buf_adjust_contents({"bufferid":12,"operation":"set","advanced":["buffetch"],"render":"bytes","offset":15,"operand":[3,2]}))
  print(buf_adjust_contents({"bufferid":12,"operation":"set","advanced":["offset","buffetch"],"render":"bytes","offset":15,"operand":[3,[2,1]]}))
  print(buf_adjust_contents({"bufferid":12,"operation":"set","advanced":["offset","buffetch","multioperand"],"render":"bytes","offset":15,"operand":[[3,[2,1]],[4,[5,6]]]}))
  print(buf_condcall({"bufferid":100,"operation":"=0","advanced":["offset","buffetch"],"render":"bytes","checkbufferid":201,"checkoffset":15}))
  print(buf_jump({"bufferid":200,"render":"bytes"}))
  print(buf_condjump({"bufferid":200,"render":"bytes","checkbufferid":100,"checkoffset":22}))
  print(buf_jumpoffset({"bufferid":200,"render":"bytes","offset":(10,20)}))
  print(buf_condjumpoffset({"bufferid":200,"render":"bytes","offset":(10,20)}))
  print(buf_condcall({"bufferid":200,"render":"bytes","checkbufferid":100,"checkoffset":22}))
  print(buf_condcalloffset({"bufferid":200,"render":"bytes","offset":(10,20)}))
  print(buf_copyconcatblocks({"targetbuffer":200,"render":"bytes","sourcebuffer":[10,20,30,40]}))
  print(buf_consolidate({"bufferid":200,"render":"bytes"}))
  print(process([{"command":"buf_split","bufferid":123,"blocksize":32,"render":"bytes"}]))
  print(process([{"command":"buf_split","bufferid":123,"blocksize":32,"render":"offsets"}]))

def demo3(inpath, outpath):
  init_path(outpath)

  from pathlib import Path
  commands = []
  commands.append({"command":"mode_swap","render":"bytes"})
  #commands.append({"command":"aud_set_waveform_parameter","channel":1,"parameter":"volume","value":16,"render":"bytes"})
  commands.append({"command":"aud_adsr","channel":1,"attack":1000,"decay":100,"sustain":64,"release":3000,"render":"bytes"})
  commands.append({"command":"aud_freqenv_stepped","channel":1,"control":["repeats"],"steplength":100,"phases":[(100,2),(-100,3)],"render":"bytes"})
  #commands.append({"command":"aud_freqenv_off","channel":1,"render":"bytes"})
  # when freqenv is off, set_frequency will not work until the note ends.
  commands.append({"command":"aud_set_waveform","channel":1,"waveform":"triangle","render":"bytes"})
  commands.append({"command":"aud_playnote","channel":1,"volume":127,"frequency":440,"duration":2000,"render":"bytes"})
  commands.append({"command":"aud_set_duration","channel":1,"duration":3000,"render":"bytes"})
  file1 = writevdu(str(outpath / Path('demo3_1.vdu')), commands)
  commands = []
  commands.append({"command":"aud_set_waveform","channel":1,"waveform":"sawtooth","render":"bytes"})
  commands.append({"command":"aud_set_frequency","channel":1,"frequency":1000,"render":"bytes"})
  commands.append({"command":"aud_set_volume","channel":1,"volume":16,"render":"bytes"})
  file2 = writevdu(str(outpath / Path('demo3_2.vdu')), commands)
  forthcode = f'{file1["size"]} value filesize1 {file2["size"]} value filesize2'
  forthcode += """
filesize1 . filesize2 .
variable vdubuf1 filesize1 allot
variable vdubuf2 filesize2 allot
vdubuf1 filesize1 bload demo3_1.vdu
vdubuf2 filesize2 bload demo3_2.vdu

: demo1 vdubuf1 filesize1 type ;
: demo2 vdubuf2 filesize2 type ;

demo1


"""
  fw = open(str(outpath / Path('michi.4th')),'w')
  fw.write(forthcode)
  fw.close()
  print("Wrote forth code")
  """To expand on demo3....
I need to add sequencing.

Sequencing means, probably, uploading a note buffer to the vdp and then triggering it at various intervals.
No. It's just unreasonable to do it this way because there's so little provision for timers.

I think the method we'll have to lean towards is time-to-next-event across n channels.
We can store the events in some buffers, but most of them are too small to bother with.
The exceptions are in setting up patch data.

So...we need a patch data format.
The patches will always use freqenv and one of the two adsrs.
They may set a waveform and pulse width
We compile out the patches to a bank .vdu file.
Then the patches are deployed by a sound engine which we'll write in Forth, I guess.
call (patch id)
Since the patches are channel-assigned if we do it statically...hmm.
Maybe we just go with "channel" per bank and "variations".
  Since we might want to alter waveform OTF we will need some kind of variation animation.
Or I can start sculpting the instrumentation right here and decide that there's a 4-poly "chord" channel,
three "solo" channels with layers, and two "sfx" channels.
Each one can have a type of patch, the patch includes playstyle/arpeggiation information,
  and we can have some sample support in the patches.
That's _probably_ within reach of the VDP.

So, what we are doing with the VDP data is setting up channels for a "player".
The player has to be software-driven, and it can be algorithmic in nature.
The player can follow some conventional music methods but the ultimate goal is to enable compositions without
being tied to linear note placement.

Rhythm pattern
Melodic pattern
Key pattern


..."""

def demo2(inpath, outpath):
  init_path(outpath)

  from pathlib import Path
  from PIL import Image
  ipath = str(inpath / Path("smiley4.png"))
  ifile = Image.open(ipath)
  sprbmps, errlog = PreparedBitmap.splitImage(ifile, "RGBA2222", 100, frame=(32,32), mode="trim", 
  origin=(16,16), attach_shared={"lefteye":(-3,-3),"righteye":(3,-3)},
  attach_frame={0:{"tl":(8,7),"br":(23,24)},
                1:{"tl":(40,6),"br":(55,25)},
                2:{"tl":(6,39),"br":(25,56)},
                3:{"tl":(36,39),"br":(59,62)},
})
  print(errlog)
  for n in sprbmps:
    print(n)
  commands = []
  commands.append({"command":"vdu_screenmode","mode":20,"render":"bytes"})
  commands.append({"command":"mode_logicalscale","setting":0,"render":"bytes"})
  commands = commands + cmd_upload_preparedbitmaps(sprbmps)
  
  file1 = writevdu(str(outpath / Path('demo2_1.vdu')), commands)

  commands = []
  bmp_pos = ((32,32),(64,32),(32,64),(512,64))
  count = 0
  for n in sprbmps:
    xy = bmp_pos[count]
    commands.append({"command":"bmp_select16","n":n.bufferid,"render":"bytes"})
    commands.append({"command":"bmp_draw","x":xy[0]+n.x,"y":xy[1]+n.y,"render":"bytes"})
    count += 1
  commands.append({"command":"mode_swap","render":"bytes"})
  file2 = writevdu(str(outpath / Path('demo2_2.vdu')), commands)

  tileset1 = cmd_upload_font_tileset(str(inpath / Path("tiles1.png")), 500, 200, 10, (16,16))
  tileset2 = cmd_upload_font_tileset(str(inpath / Path("tiles3.png")), 500+256, 300, 20, (16,16))
  print(tileset1["log"])
  print(tileset2["log"])

  commands = []
  commands = commands + tileset1["commands"]
  commands = commands + tileset2["commands"]

  commands.append({"command":"ctx_select","flags":[],"contextid":10,"render":"bytes"})
  for count in range(32):
    commands.append({"command":"vdu_charoutput","char":count,"render":"bytes"})

  commands.append({"command":"ctx_select","flags":[],"contextid":20,"render":"bytes"})
  commands.append({"command":"vdu_cr","render":"bytes"})
  commands.append({"command":"vdu_down","render":"bytes"})
  commands.append({"command":"vdu_down","render":"bytes"})
  commands.append({"command":"vdu_down","render":"bytes"})
  commands.append({"command":"vdu_down","render":"bytes"})
  for count in range(32):
    commands.append({"command":"vdu_charoutput","char":count,"render":"bytes"})
  
  file3 = writevdu(str(outpath / Path('demo2_3.vdu')), commands)
  """*assign it to a new font
*align the cursor movement
*demonstrate that the original tileset is printable
*upload a second set of tiles
*assign that to a different font
*print that
restore regular text

"""

  forthcode = f'{file1["size"]} value filesize1 {file2["size"]} value filesize2 {file3["size"]} value filesize3'
  forthcode += """
filesize1 . filesize2 . filesize3 .
variable vdubuf1 filesize1 allot
variable vdubuf2 filesize2 allot
variable vdubuf3 filesize3 allot
vdubuf1 filesize1 bload demo2_1.vdu
vdubuf2 filesize2 bload demo2_2.vdu
vdubuf3 filesize3 bload demo2_3.vdu

: demo1 vdubuf1 filesize1 type ;
: demo2 vdubuf2 filesize2 type ;
: demo3 vdubuf3 filesize3 type ;

demo1
demo3
demo2

"""
  fw = open(str(outpath / Path('michi.4th')),'w')
  fw.write(forthcode)
  fw.close()
  print("Wrote forth code")

  """

To proceed with this I need to work on making somewhat more sophisticated Forth code.
What I want to show is that I can place bitmap objects with relative positioning.
The relative position can be either on the VDP or in Forth code, but most likely it will be faster
if I move what I can to the VDP.

I could aim to use PLOT.
With this I could go down the route of saving one context per bitmap sprite.
Is that too much?
Alternately, I could apply one program call per bitmap sprite.
Hmmmmmmm.
If I intend to use hardware sprites I need to cater to that API.

Yeah, looks like I'm going with ez80 driving the offset code, because I want to play with hw sprites.

Offsets for....
...origin to sprite
...rectangle top left (origin-relative)
...rectangle bottom right (origin-relative)

I may want to automatically generate tl/br since it's the obvious choice for a default collision rect.

Starting point.

Starting point is to just draw all four sprites somewhere, anywhere, without respecting the origin stuff.
To do this I need to generate some VDP code for placing each sprite. 
This is code that is small enough that I should be able to upload once,
then, I guess, modify offsets in a second "update buffer".
That is, if I want to run 100 sprites, I just have a buffer with 100 spaces ready to go.
I don't generate that buffer at runtime, I modify its offsets and reupload.

For this, what I want to do is make a class called DrawingRoutine, I think.
DrawingRoutine contains a program, from which I extract specific offsets.
I load the raw program into a buffer, then I reprogram the offsets with Forth code.

----

Reset sprites (only) and clear all data

select sprite 0
addSpriteFrame bitmap 100
show current sprite

select sprite 1
addSpriteFrame bitmap 101
show current sprite

select sprite 2
addSpriteFrame bitmap 102
show current sprite

select sprite 3
addSpriteFrame bitmap 103
show current sprite

activate 4 sprites

----

7 bytes per move call
* 4
(update sprites in GPU)

----

Now, because I have a ton of memory on the VDP, it actually makes a lot of sense to prerender large sprite sheets.
That's less expensive to manage than something where I'm managing a lot of offsets at runtime.

So I'm thinking that what I can have if I go for the "Rayman-type" smiley characters is to have three layers - face,
hands, feet.

Each one can be a sprite. This leaves us with, if we go for 64 hardware sprites, 21 characters onscreen.
If we bake them, we can feasibly have 64 characters.
If we assign "signpost" to some, we can go up even further since those become bitmaps or tiles.

Because we will want to sort by y, we need to be able to flexibly reassign sprites.
That means that the most likely thing we'll do is to assign every possible character expression to every sprite,
or to erase and start over every frame.

----

This actually isn't looking great for a flexible MZX-alike engine.
I think I might want to instead go the route of drawing bitmaps:

Select bitmap n
Draw current bitmap on screen at pixel position x, y

I can go for single-screen scenes without scrolling and this means I can use dirty rectangles without issue.
All I'd be doing is repeatedly updating the parts of the tilemap where things are moving and then updating the sprites over that.
No need for double-buffering, really.

The top of the screen can use HW sprites for something else like HUD as a way to avoid flicker.

----

Now, if I turn my attention over towards, uh, text...
...I'm thinking here that I'll do the thing with characters-as-bitmaps, which leaves us with just 127 tiles in our tileset.
Across a 512x384 screen that means we have a 64x48 8x8 grid,
or 32x24 16x16.

Since our characters are roughly 16x16 the latter makes more sense, but 32x24 is still 768. So we are not exactly saturated with
tiles here.

Wait. But we can use the font api to swap things out. That frees up the possibility of using all 256 in a custom font.

While it's not enough to completely cover the screen, I have to remember how MZX did things and how much that allowed!
So then we have a scenario where we can do something like this: 

28x22, 256 unique 16x16 bg tiles
6*16-width(12 character) HUD ala ZZT
One row for top HUD/titles
One row for bottom HUD/messages
64 actors (dirty rect)

Now we're getting to the phase where, OK, what do we need to implement in VDPTypes to test this?
We need some things for the HUD and titles.
We need some things for the tileset.
We need some things for actors(64 is a bit wishful without HW sprites)
  Since the actors rely on SW dirty rect we'd have to implement that.
On our first pass through this we can aim for "render the whole scene every frame"

I have my actors drawing now. I should add a tilemap next.

OK, it looks like I can have any number of 256-character fonts set up.
Sky's the limit, if I want I can have them across different contexts so that the cursor is set up differently.

There is a tile layer system coming in but it's not ready yet and working with the font support might be better
for right now.
I can pretty easily scoop up some system for blasting a lot of tiles by printing.

----

25/2/17

OK, I have some tiles printing.
I need to, though:

align the cursor movement
demonstrate that the original tileset is printable
assign it to a new font
upload a second set of tiles
assign that to a different font
print that
restore regular text

if I can do all of that I am set

------

OK, I can't do this with fonts...but I can do it with contexts.
I do need to use a font to define the advance size, but my mapping is based on context + font,
and font will be pre-selected by context.

This would mean that each context would have its own cursor to reset and restore...
...apart from that, it should be pretty straightforward once I have the right API calls.
Context also means I can hide the cursor in those contexts so that there is no visible glitch from cursor advance

It's not hard to demo two contexts, just mash down a few times to put the cursor in a different spot.

------

I have completed the demo with contexts.
Now, I can still demo drawing an actual baked-in tilemap as a buffer...
...or I can move on to other kinds of assets.

In some sense I've demonstrated font support even if I didn't use the entire API.
The next major category to work on would be audio.

Well, I hit a natural ceiling with audio on the same evening.
It works, I can play noises, set envelopes. But I will need to adopt a model of software command for most of the sequencing.

------

The next thing I should probably do is input/collision.
Debug bounding boxes and moving things with them and attaching sprites to them.
That's something that will be mostly Forth-side, not VDP-side, although the bounding boxes are important.

Regarding sprite offsets, now I'm thinking...hmmmmm, maybe I can make use of the origin data in fact.
However I am getting roped into HW sprites by ss and turbovega since they will add frame setting by bitmapid.
So, maybe I will keep that in software.

For a typical MZX type character with extremities we can use two sprites: face and hands/feet.
The animations for hands/feet will almost certainly be synced so it makes sense to combine them.

The name Megagon comes to mind for that project.

25/2/21

After a break during the week...
I think I want to focus on audio sequencing this weekend.

The goal will be to create some kind of mapping between, hmm, MIDI, I guess?
Or is that going too far in the direction of conventional tools?

Yeah, what I should do is really more, just, "trigger things from Forth".
Build out a little more infrastructure for demos there.

I might want to freshen up my build processes a little.

25/2/22

I got hooked on the problem of fast streaming loads of the .vdu files.
After hours of effort, I succeeded in getting it loading a 160k file with a 1k buffer, and using my fast
MOSTYPE word so that there is a minimum of Forth overhead.

Now... the idea of moddability after doing this seems distant. While it's possible to stream in editable 
image files, there's no point. I'm going towards a process dictated by the vdptypes build system, fully offline.
This is not so bad, in the end.

To test music, here's the demo I should set up:

1. Initialize a simple patch
2. Start an event loop that plays a repeating note trigger
3. Exit when a key is pressed.

If I do that, the upgrade is from "repeating note" to "note sequence".

I have made this demo. But now I probably need to return to VDP buffer construction.
In particular, three things I should really do:

*1. Create Python allocators for VDP buffers - named locations and arenas.
*2. A build process that just copies all the .vdu files I've made in an output directory.
3. Generate Forth code for manipulating VDP buffers - a "base and overlay" system.
  since I have named offsets available for all VDU sequences, it should be possible to expose them
  in the context of - first put this byte sequence in this buffer, then add words to assign to them.

  This should probably be accomplished "manually" first - taking my demo3_1 example - 
  and trying to turn it into a sequence of EMIT statements.
  Then rewriting it to "load a buffer and adjust memory locations inside of it".
    Since I know the sizes I can also generate the correct size of assignment.

25/2/23

I only did the allocators yesterday, but spent a while refining the existing Forth code...
...the file stat now properly reads 32-bit values (I think, not that I've tested it outside a 
synthetic example) and generally everything has been bashed down into library-code shape.

Continue with the build and codegen stuff now. That's fine for the weekend's work.

Sequencing, though. I want to get on sequencing.

1. I need to actually demonstrate USING the allocators since all I did was make them
and do a trivial test.
2. I didn't do any Forth codegen.


"""

def demo_wavetable(inpath, wavpath, outpath):
  init_path(outpath)

  from pathlib import Path

  wavs = []
  for n in range(1,7):
    wavs.append("AKWF_blended_000"+str(n))
  print(wavs)
  alloc = VDPBufferAllocator()
  alloc.define("1cycle", 100, 10)
  alloc.define("wavetable", 200, 10)
  
  for wavbase in wavs:
    sox_infile = wavpath / Path(wavbase+".wav")
    sox_outfile = wavpath / Path(wavbase+".u1")
    do_sox = True
    if do_sox:
      import subprocess
      import os
      print(os.getcwd(), sox_infile)
      sp_measure = subprocess.run(["sox_ng","--info","-s",sox_infile], capture_output=True)
      if len(sp_measure.stdout) > 0:
        print(int(sp_measure.stdout))
        rate0 = int(sp_measure.stdout)
        rate1 = 256
        spout = subprocess.run(["sox_ng","--rate",str(rate0),sox_infile,
          "--type","u1","--endian","little","--channels","1","--rate",str(rate1),
          sox_outfile], capture_output=True)
        print(spout)
      else:
        print("couldn't get sample count, bailing")
        exit(0)

    def read_bytes(fname):
      fh = open(fname, 'rb')
      ans = fh.read()
      fh.close()
      return ans
    
    alloc.store("1cycle", wavbase, read_bytes(sox_outfile))
  
  commands = []
  print(alloc.stores)
  for wavbase in wavs:
    sbuf = alloc.search(wavbase)
    print(wavbase, sbuf)
    commands += cmd_upload_blocks(sbuf["value"], sbuf["bufferid"])
  alloc.store("wavetable", "mywave", 0)
  scans = []
  for n in wavs:
    buf = alloc.search(n)["bufferid"]
    for i in range(64):
      scans.append(buf)
  scans_rev = scans.copy()
  scans_rev.reverse()
  scans = scans + scans_rev
  commands.append({"command":"buf_copyreference","targetbuffer":alloc.search("mywave")["bufferid"],"sourcebuffer":scans, "render":"bytes"})
  commands += cmd_testsample(1, alloc.search("mywave")["bufferid"], (16384*2)//256, 440)
  writevdu(outpath / Path('demo_wt.vdu'), commands)

  # TODO 25-3-2: It plays. I need to write some Forth source, I think.
  # I'm not totally clear on why I need the 16k*2 value. Is it trying to be stereo? Or does the waveform have a dbl cycle?  
  # 25-3-5: It's not a double cycle. I think the value is just stereo-ized.
  # I really, really need to iterate on the demo code because I've let it get pretty sloppy.
  # 1. The forth library should probably live in its own function.
  # 2. My application of source and output for the vdu files is shaky. 
  #   Do I use refs? Do I shove it underneath the vdptypes module?
  # 3. I don't make use of alloc everywhere.
  # 4. The build system can probably be cleaner - more configured by a dict instead of by functions.
  # 5. My use of sox_ng is a bit casual...I don't mind throwing around the windows binary but the path should probably
  # be passed into the demo.

  # 25-3-16
  # I have demonstrated that I can, in fact, do wavetable synthesis by building a large copy-pasted buffer.
  # I have partially cleaned up path usages; this should be expanded upon by just cleaning up example.py, in general,
  # and adding some of my build system stuff to vdptypes.py so that it's more of a one-stop library.

def demo1(inpath, outpath):

  init_path(outpath)

  do_alloc = False

  if do_alloc:
    alloc = VDPBufferAllocator()
    alloc.define("patch", 100, 1)
    alloc.define("image", 200, 10)
    alloc.store("patch", "patch1",1)
    alloc.store("image", "image1",2)
    alloc.store("image", "image2",3)
    alloc.store("image", "image3",4)
    alloc.store("image", "image4",5)
    alloc.clear("patch")
    alloc.store("patch", "patch2",6)
    print(alloc.stores)
    print(alloc.search("patch1"))
    print(alloc.search("patch2"))
    print(alloc.search("image3"))
    exit(0)

  from pathlib import Path
  from PIL import Image

  ipath = str(inpath / Path("michi512.png"))
  ifile = Image.open(ipath)
  print(f'opened {ipath}')
  #pbmps = PreparedBitmap.splitImage(ifile, "RGBA2222", 100)
  pbmps = [PreparedBitmap(ifile, "RGBA2222", 0, 0, 100)]
  commands = []
  commands.append({"command":"vdu_screenmode","mode":20,"render":"bytes"})
  commands = commands + cmd_upload_preparedbitmaps(pbmps)
  commands = commands + cmd_display_bitmaps(pbmps)
  """
  commands = commands + cmd_generate_bitmap(100, 64, 64, 0x1177FFFF)
  commands = commands + cmd_generate_bitmap(101, 64, 64, 0xFF77FF11)
  commands = commands + cmd_generate_bitmap(102, 64, 64, 0x11FFFFFF)
  commands = commands + cmd_generate_bitmap(103, 64, 64, 0x117700FF)
  commands = commands + cmd_display_bitmaps([
    PreparedBitmap(ifile, "RGBA8888", 0, 0, 64, 64, 100),
    PreparedBitmap(ifile, "RGBA8888", 0, 64, 64, 64, 101),
    PreparedBitmap(ifile, "RGBA8888", 0, 128, 64, 64, 102),
    PreparedBitmap(ifile, "RGBA8888", 0, 192, 64, 64, 103)])
"""
  # display the result
  print(len(commands), "commands")
  for n in commands:
    print(n["command"])
  fw = open(str(outpath / Path('michi.vdu')),'wb')
  count = 0
  for n in process(commands):
    if len(n["log"])>0:
      print("--------")
      print(n)
    count += fw.write(n["bytes"])
  fw.close()
  print(f'Wrote {count} bytes')
  forthcode = """

CODE MOSTYPE ( c-addr1 u ---)
\G Use MOS v1.03 RST 18h to rapidly print the string at c-addr1 and length u.
    LD C, E
    LD B, D
    POP DE
    EX DE, HL
    LD A, 0 \ required to trigger length mode
    RST .LIS $18
    POP DE
    NEXT
END-CODE

: d32@ ( a-addr --- d )
\G fetch 32-bit number at a-addr as double.
  dup @ swap 3 + c@
;
: d32! ( d a-addr --- )
\G write double as 32-bit number at a-addr.
  >r swap r@ ! r> 3 + c!
;

variable filinfo
\G buffer for FILINFO
4 2 + 2 + 1 + 13 + 256 + allot 

: filinfo-fsize ( --- d )
\G fetch fsize, a double number containing the file size in FILINFO.
filinfo d32@ ;

: ffs-stat ( --- )
\G loads the info from FATFS "stat" call to FILINFO.  
  filinfo curfilename 0 $96 oscall drop ;

: bload-curfile ( buf-addr --- ) 
\G BLOADs the data file set by OPEN f FFS-STAT to buf-addr
\G Example: 
\G  open myfile.vdu ffs-stat \ load filinfo
\G  variable vdubuf filinfo-fsize drop allot \ buf matches filinfo-fsize
\G  vdubuf bload-curfile \ load bytes to buf
\G  vdubuf filinfo-fsize drop mostype \ type buf
curfilename swap filinfo-fsize drop 1 OSCALL -38 ?THROW ;


1024 create vdu-streambuf allot
\G buffer for VDU streaming
0 value vdu-stream-fd
\G file handle for VDU streaming
: vdu-stream-curfile ( --- )
\G Streams the VDU data file set by OPEN
\G Example:
\G  open myfile.vdu vdu-stream-curfile \ streams in the entire file in 1k chunks
  curfilename asciiz> r/o open-file 
  drop to vdu-stream-fd
  begin
    vdu-streambuf 1024 vdu-stream-fd read-file drop dup
    0>
  while
    vdu-streambuf swap mostype
  repeat
  vdu-stream-fd close-file drop drop
;


\ this revision with read-file now works!
\ the last step is to read in chunks, using the 
\ ans of read-file to determine EOF instead of
\ relying on stat

\ basically we'll end up with bload-curfile and 
\ vdu-stream-curfile.

\ Excellent. We're done for the evening.
\ We use a 1k streaming buffer and it's...
\ great. 

\ Tomorrow's task is to clean up how we do builds, taking into account that we can now
\ mix and match our vdu files pretty easily.
\ Then we can work on audio things...

0 value note-timer
60 value note-interval
: play-notes
  note-timer 0= IF
    7 emit \ to start playing music we replace with something that triggers some patches
    note-interval to note-timer
  THEN
  note-timer 1- to note-timer
;

: start
  BEGIN ?TERMINAL INVERT WHILE play-notes 
  23 emit 0 emit $C3 emit REPEAT
;

"""
  fw = open(str(outpath / Path('michi.4th')),'w')
  fw.write(forthcode)
  fw.close()
  print("Wrote forth code")
  """ 


It now works! Michiru looks like she should.

I can keep around the slicing code since that's very useful for sprite/tile sheets.

Now, something I can do is introduce a load streaming mechanism, for example, calling an animation subroutine
in between blocks.

Something else I could do is crib the Turbovega compresson from Nihirash and use that to shrink down our images,
making the upload faster.

Flesh things out so that we have some sprites and such, maybe a cursor or a font.

We have tile slicing code so we can use that to quickly demonstrate a tilemap of some kind, maybe one using character-based 
tiles.

I've put together trimmed slicing, origin calculation, and attachment points calculation(shared across all of a sheet as well as local).
These calculations could use some more testing to ensure that they really are spot-on, but for right now I'll take it for granted that they are
about right.

The next step would be to put together code in demo2 that shows that I can move around these bitmaps relative to an origin point,
and maybe draw the attachments too.



Then proceed towards audio.

"""
  print("OK")

if __name__=="__main__":
  demo0()

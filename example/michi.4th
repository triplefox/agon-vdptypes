

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


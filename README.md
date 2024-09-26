# gba-song-assembler
A rewrite of [Sappy2006's assembler](https://github.com/Touched/Sappy/blob/master/source/frmAssembler.frm) into Python. Assembles MP2K song s files into binary and injects them into a GBA game.

To download, please click the green "code" button, then click "Download ZIP".

**Please make a backup of your GBA rom file before modifying it with this program.**

On Windows, I recommend running this with [WinPython](https://winpython.github.io/) Command Prompt.

To make MP2K song s files, I recommend using [Midi2AGB](https://github.com/ipatix/midi2agb) to convert midi files to s files.    
To edit a song in a GBA game, I recommend using [my fork of GBA_Mus_Ripper](https://github.com/Thysbelon/gba-mus-ripper) with the arguments `-xg -sb -rc -raw` to convert the song to midi, edit the midi using your favorite midi editor and sf2 synthesizer, convert it to an s file using Midi2AGB, then inject it back into the game using gba-song-assembler.py.    
[My blog post on this GBA MP2K song editing workflow](https://thysbelon.github.io/Blog/2024-9-24/My-Attempts-to-Improve-GBA-Music-Romhacking-and-SiIva-Style-Ripping).

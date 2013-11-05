Video2Poster - Create a poster from a video file
================================================

##Overview

Video2Poster takes a single video file and creates a printable poster using a frame every one second from the poster.
Its based off an old reddit post I saw (not movie barcode) but I can't find right now. 

##Example
Note: This example image is much smaller than the actual images it can produce. The script will autoscale the images to whatever dimensions and DPI you give it, so if you create a large enough poster you'll be able to clearly see every frame created.

##Notes

Video2Poster is a proof-of-concept. It has only been tested on windows with python 2.7 and has several required dependencies.

##Requirements

Video2Poster uses ffmpeg to generate the frames. It also uses ffprobe to pre-determine the size of frames needed.

Pre-built ffmpeg binaries can be found here:
- [ffmpeg Windows Binaries](http://ffmpeg.zeranoe.com/builds/)
- [ffmpeg Mac Binaries](http://ffmpegmac.net/)

Other requirements:
- A truetype font (of your choice).
- [Python Image Library (PIL)](http://www.pythonware.com/products/pil/)

##Installation and Notes

Quick example using windows:

- Place video2poster.py, ffmpeg.exe, ffprob.exe, a .ttf file, and a video file in a common directory.
- Edit video2poster.py: V2P_FONT = "arialbd.ttf", replace "arialbd.ttf" with your font file.
- Run the command:
'''
video2poster.py videofile.avi "Some Title" 10 20
'''

This will create a Poster 10in x 20in using videofile.avi

# Video2Poster - Create a poster from a video file

## Overview

Video2Poster takes a single video file and creates a printable poster using frames at a set interval from the video.

It has only been tested on windows with python 3.8

## Example

Note: This example image is much smaller than the actual images it can produce. The script will autoscale the images to whatever dimensions and DPI you give it, so if you create a large enough poster you'll be able to clearly see every frame created.

![v2p example](https://raw.github.com/giveitupforjoel/video2poster/master/examples/h_o_small.png?raw=true)

## Dependencies

Video2Poster uses ffmpeg and ffprobe, thus they need to be in your path, e.g:

```bash
set Path=%PATH%;H:\devel\bin\ffmpeg\ffmpeg-20200126-5e62100-win64-static\bin
```

It's only python dependency is PIL (pillow).

## Links

Pre-built ffmpeg binaries can be found here:
- [ffmpeg Windows Binaries](http://ffmpeg.zeranoe.com/builds/)
- [ffmpeg Mac Binaries](http://ffmpegmac.net/)

Other requirements:
- Access to a truetype font of your choice.

## Example

```bash
python v2p_cli.py ..\MyMovie.mp4 "MSM" 12 18
# This will create a poster 12in wide X 18 in tall.
```

See v2p_cli.py for python example.

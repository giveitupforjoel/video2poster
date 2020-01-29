#!/usr/bin/env python
import argparse
import video2poster

if __name__ == '__main__':
    """
    Video2Poster cli
    """
    parser = argparse.ArgumentParser(
        usage='%(prog)s [options] filename title width height',
        description='Creates a poster from a movie file.'
        )

    # required positional arguments
    parser.add_argument( "filename", help="Path to video file." )
    parser.add_argument( "title", help="Title of the poster." )
    parser.add_argument( "width", help="Width of poster (inches)." )
    parser.add_argument( "height", help="Height of poster (inches)." )

    # optional
    parser.add_argument( "-time", help="Timer interval of each frame. (Default 1 sec)." )
    parser.add_argument( "-wm", help="Width margine. (Default 1 in)" )
    parser.add_argument( "-hm", help="Height margine. (Default 1 in)" )
    parser.add_argument( "-dpi", help="DPI. (Default 300 dpi)" )

    args = parser.parse_args()

    v2p = video2poster.Video2Poster(args.filename, args.width, args.height, args.title)
    v2p.GeneratePoster(temp_dir='temp_directory')
    v2p.SavePoster('poster.png')

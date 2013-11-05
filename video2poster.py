#!/usr/bin/env python
#
# The MIT License (MIT)
#
# Copyright (c) 2013 Joel House 
#
# This file is part of Video2Poster.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

import sys
import os
import errno
import math
import argparse
import subprocess
import json

import Image
import ImageFont
import ImageDraw


def make_dir( path ):
    try:
        os.makedirs( path )
    except OSError as exception:
        if ( exception.errno != errno.EEXIST ):
            raise

V2P_FONT = "arialbd.ttf"


class VideoToPoster:
    """ Video to Poster Class
    """

    def __init__( self, filename, width, height, title, dpi = 300, margins = ( 1.0, 1.0 ), t_int = 1, verbose = 0 ):

        # required parameters
        self.movie_filename = filename
        self.poster_xy_in   = [ float( width ), float( height ) ]
        self.title          = title

        # defaults
        self.dpi          = dpi
        self.xy_margin_in = [ margins[ 0 ], margins[ 1 ] ]
        self.t_interval   = t_int

        self.font_size_px = 250
        self.font_mar_px = 400

        # uninitialize vars
        self.temp_frm_dir = ".\\temp_frms"
        self.verbose = verbose

        self.frm_list = []
        self.frame_ct = 0

        # must call this last
        self._updt_vars()


    def _updt_vars( self ):
        """ Update calculated parameters when something has changed
        """
        #clear list
        self.frm_list = []

        self._get_movie_info()

        self.xy_margin_px = [ int( self.xy_margin_in[ 0 ] * self.dpi ),
                              int( self.xy_margin_in[ 1 ] * self.dpi ) ]
        self.poster_xy_px = [ int( self.poster_xy_in[ 0 ] * self.dpi ),
                                int( self.poster_xy_in[ 1 ] * self.dpi )  ]
        self.tgt_xy_px = [ self.poster_xy_px[ 0 ] - ( self.xy_margin_px[ 0 ] * 2 ),
                           self.poster_xy_px[ 1 ] - ( self.xy_margin_px[ 1 ] * 2 ) - self.font_mar_px ]


        self.frame_ct = int( self.duration * self.t_interval )

        self._calc_optimal_res()


    def _get_movie_info( self ):
        """ Retrieve json formatted video information using ffprobe
        """
        result   = subprocess.Popen( [ "ffprobe", self.movie_filename, "-print_format", "json", "-show_streams", "-loglevel", "quiet" ],
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.STDOUT )
        rslt_str = result.stdout.read()
        info     = json.loads( rslt_str )

        self.duration     = float( info[ "streams" ][ 0 ][ "duration" ] ) #.encode( 'ascii', 'ignore' ) )
        self.xy_ratio_str = info[ "streams" ][ 0 ][ "display_aspect_ratio" ] #.encode( 'ascii', 'ignore' )
        self.xy_ratio     = float( self.xy_ratio_str.split( ':' )[ 0 ] ) / float( self.xy_ratio_str.split( ':' )[ 1 ] )


    def _calc_optimal_res( self ):
        """ Calculate the optimal resolution of each video frame
        """

        #loop from the smallest possible x size to the largest
        #increment the x resolution until it will no longer fit
        #in the defined area.

        #TODO: Determine the implicit function for this
        x_len_px = self.tgt_xy_px[ 0 ]
        y_len_px = self.tgt_xy_px[ 1 ]

        x_res = 1
        for i in range( int( self.xy_ratio ) + 1, x_len_px ):
            x_res      = i
            y_res      = int( float( x_res ) / self.xy_ratio )

            per_x_line = int( x_len_px / x_res )
            y_lines    = int( math.ceil( float( self.frame_ct ) / float( per_x_line ) ) )

            # break if the total size is too big
            if( y_lines * y_res > y_len_px ):
                break

        #return the previous resolution
        x_res = x_res - 1
        y_res = int( float( x_res ) / self.xy_ratio )

        self.pic_xy_px = [ x_res, y_res ]
        pass


    def _build_frame_list( self ):
        """ From the temp directory, build a list of each valid frame
        """
        for infile in os.listdir( self.temp_frm_dir ):
            #print "Opening:", ( indir + "\\" + infile )
            try:
                fpath = self.temp_frm_dir + "\\" + infile
                tmp_img = Image.open( fpath )
                self.frm_list.append( fpath )
                #PIL doesn't seem to have a close function
                #otherwise it would be called here
            except IOError:
                del self.frm_list[ 0:len( self.frm_list ) ]
                print "Error opening: ", infile
                break

        #ensure the frame_ct matches
        while( len( self.frm_list ) > self.frame_ct ):
            self.frm_list.pop()

        #TODO: Handle the case when not enough frames are generated... better than this
        self.frame_ct = len( self.frm_list )

        if( self.verbose > 0 ):
            print "%i images available for stitching" % ( len( self.frm_list ) )

    def _gen_frames( self ):
        """ Generate the frames using ffmpeg
        """

        if( self.verbose > 0 ):
            print "\nCreating frames...\n"

        #self.temp_frm_dir = ".\\temp"
        make_dir( self.temp_frm_dir )

        ffmpeg_cmd = [ 'ffmpeg',
                       '-i', self.movie_filename,
                       '-s', '{0:d}x{1:d}'.format( self.pic_xy_px[ 0 ], self.pic_xy_px[ 1 ] ),
                       '-f', 'image2',
                       '-vf', 'fps=fps=1',
                       self.temp_frm_dir + '\\out%06d.png' ]

        if( self.verbose > 1 ):
            print "ffmpeg cmd:"
            print ffmpeg_cmd

        result   = subprocess.Popen( ffmpeg_cmd,
                                     stdout = subprocess.PIPE,
                                     stderr = subprocess.STDOUT )
        rslt_str = result.stdout.read()
        if( self.verbose > 0 ):
            print rslt_str

    def ExportImage( self ):
        """ Build and export the final poster file
        """
        x_per_line = int( self.tgt_xy_px[ 0 ] / self.pic_xy_px[ 0 ] )


        # Determine the margins. Note: If the determined frame width doens't
        # perfectly align with end, it will need to be centered.
        x_ofs = self.xy_margin_px[ 0 ] + ( ( self.tgt_xy_px[ 0 ] % self.pic_xy_px[ 0 ] ) / 2 )
        y_ofs = self.xy_margin_px[ 1 ] + self.font_mar_px

        if( ( x_ofs != self.xy_margin_px[ 0 ] ) and self.verbose > 0 ):
            print "Adjusting x-margin from %i to %i pixels" % (self.xy_margin_px[ 0 ], x_ofs )

        oimg = Image.new( "RGB", ( self.poster_xy_px[ 0 ], self.poster_xy_px[ 1 ] ) )
        x_cnt = 0
        y_cnt = 0
        for frame in self.frm_list:

            try:
                print "Opening", frame
                tmp_img = Image.open( frame )
            except IOError:
                continue

            oimg.paste( tmp_img, ( ( self.pic_xy_px[ 0 ] * x_cnt ) + x_ofs, ( self.pic_xy_px[ 1 ] * y_cnt ) + y_ofs ) )

            #determine the next x,y coords
            if( x_cnt + 1 < x_per_line ):
                x_cnt += 1
            else:
                x_cnt = 0
                y_cnt += 1

        #print title centered
        draw = ImageDraw.Draw( oimg )
        font = ImageFont.truetype( V2P_FONT, self.font_size_px )
        ( txt_x, txt_y ) = draw.textsize( self.title, font = font )

        if( self.verbose > 0 ):
            print "The text size is %ix%i" % ( txt_x, txt_y )

        txt_x = ( self.poster_xy_px[ 0 ] / 2 ) - ( txt_x / 2 )
        draw.text( ( txt_x, self.xy_margin_px[ 1 ] ), self.title, ( 255, 255, 255 ), font = font )
        # self.font_size_px = 250
        # self.font_mar_px = 300

        #save
        oimg.save( "test.png" )

    def GenerateFrames( self ):
        """ Generate and build frames
        """

        self._gen_frames()
        self._build_frame_list()
        return True

    def PrintPosterDetails( self ):
        """ (Temp) Print movie information to the screen.
        """
        print "\nThe following poster will be created: %s\n" % ( self.movie_filename )
        print "Poster Size (in): %f in X %f in." % ( self.poster_xy_in[ 0 ], self.poster_xy_in[ 1 ] )
        print "Poster Size (px): %i x %i" % ( self.poster_xy_px[ 0 ], self.poster_xy_px[ 1 ] )
        print "DPI: %i dpi" % ( self.dpi )
        print "Movie Length (sec): %i" % ( self.duration )
        print "Movie Frame ratio: %s" % ( self.xy_ratio_str )
        print "Movie Frame dimension (px): %i x %i." % ( self.pic_xy_px[ 0 ], self.pic_xy_px[ 1 ] )
        pass


#program ran from command prompt
def main():

    args = process_cl()
    #TODO: Add optional variables
    PosterGen = VideoToPoster( args[ 'filename' ], args[ 'width' ], args[ 'height' ], args[ 'title' ], verbose = 2 )

    # Continue?
    PosterGen.PrintPosterDetails()

    yn = raw_input( "\nContinue [y/n]?" )
    if( not ( ( yn == 'y' ) or ( yn == 'Y' ) ) ):
        return

    # Generate Poster
    PosterGen.GenerateFrames()
    PosterGen.ExportImage()
    pass


#Process the command line parameters
#This will exit the program if the necessary parameters are not supplied
def process_cl():

    # parse the command line
    parser = argparse.ArgumentParser( usage='%(prog)s [options] filename title width height', description='Creates a poster from a movie file.')

    # required positional arguments
    parser.add_argument( "filename", help="Input movie file path" )
    parser.add_argument( "title", help="Tilt of the movie." )
    parser.add_argument( "width", help="Width of poster in inches." )
    parser.add_argument( "height", help="Height of poster in inches." )

    # optional
    parser.add_argument( "-time", help="Timer interval of each frame. Default 1 sec." )
    parser.add_argument( "-wm", help="Width margine. Default 1 in." )
    parser.add_argument( "-hm", help="Height margine. Default 1 in." )
    parser.add_argument( "-dpi", help="DPI. Default 300 dpi." )

    return vars( parser.parse_args() )


if __name__ == '__main__':
    main()

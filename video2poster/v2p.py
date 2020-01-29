import os
import math
import json
import subprocess
from typing import List

from PIL import Image, ImageDraw, ImageFont

class Video2Poster:
    """
    Convert a video to a poster.

    Uses FFMpeg to convert video frames to images then pastes them into
    poster format.

    Note: ffprobe and ffmpeg must be in your PATH.

    Example:
    >>> import video2poster
    >>> v2p = video2poster.Video2Poster('mymovie.mp4', 12, 18, 'My Movie')
    >>> v2p.GeneratePoster('temp_directory')
    >>> v2p.SavePoster('poster.png')

    """
    def __init__(
        self,
        filename,
        width_inches,
        height_inches,
        title,
        dpi = 300,
        margins = (1.0, 1.0),
        sample_rate_sec = 1,
        ttfont = 'arialbd.ttf',
        font_size = 250,
        font_margin_px = 400
        ):

        # Required parameters
        self._video_path = filename
        self._poster_xy_in = (float(width_inches), float(height_inches))
        self._title = title

        # Defaults
        self._dpi = dpi
        self._xy_margin_in = margins
        self._sample_rate_sec   = sample_rate_sec
        self._ttfont = ttfont
        self._font_size_px = font_size
        self._font_mar_px = font_margin_px

        # Get video specs
        info = self._get_movie_info()
        self._duration = float(info['streams'][ 0 ]['duration'])
        self._coded_w = float(info['streams'][ 0 ]['coded_width'])
        self._coded_h = float(info['streams'][ 0 ]['coded_height'])
        self._ratio   = self._coded_w / self._coded_h

        # Margins
        self._xy_margin_px = (int(self._xy_margin_in[0] * self._dpi), int(self._xy_margin_in[ 1 ] * self._dpi))
        self._poster_xy_px = (int(self._poster_xy_in[0] * self._dpi), int(self._poster_xy_in[ 1 ] * self._dpi ))
        self._target_xy_px = (int(self._poster_xy_px[0] - (self._xy_margin_px[0] * 2)),
                              int(self._poster_xy_px[1] - (self._xy_margin_px[1] * 2) - self._font_mar_px))

        # Init frame list and calculate frame resolution
        self._frame_ct = int(self._duration *self._sample_rate_sec)
        self._frame_list = []
        self._pic_xy_px = self._calc_optimal_res()

    def GeneratePoster(self, temp_dir: str = os.path.join(os.curdir, 'temp_frames') ):
        """ Generate the frames using ffmpeg
        """
        if not os.path.isdir(temp_dir):
            os.makedirs(temp_dir)

        ffmpeg_args = ['-i', self._video_path,
                       '-s', '{0:d}x{1:d}'.format(self._pic_xy_px[ 0 ], self._pic_xy_px[ 1 ]),
                       '-f', 'image2',
                       '-vf', 'fps=fps=1',
                       os.path.join(temp_dir, 'out%06d.png')
                       ]
        ret = self._run_cmd('ffmpeg', ffmpeg_args)

        for frame in os.listdir(temp_dir):
            self._frame_list.append(os.path.join(temp_dir, frame))

        # Ensure the frame_ct matches
        while len(self._frame_list) > self._frame_ct:
            self._frame_list.pop()

    def SavePoster(self, filename: str):
        """ Build and export the final poster file
        """
        x_per_line = int(self._target_xy_px[0] / self._pic_xy_px[0])

        # Determine the margins.
        # Note: If the determined frame width doens't perfectly align with
        # the end, it will need to be centered.
        x_ofs = int(self._xy_margin_px[0] + ((self._target_xy_px[0] % self._pic_xy_px[0]) / 2))
        y_ofs = self._xy_margin_px[ 1 ] + self._font_mar_px

        # Create a blank poster
        poster = Image.new("RGB", (self._poster_xy_px[ 0 ], self._poster_xy_px[ 1 ]))

        # Paste each frame into the correct position
        x_cnt = 0
        y_cnt = 0
        for frame in self._frame_list:
            try:
                tmp_img = Image.open( frame )
            except IOError:
                print('Error opening {}'.format(frame))
                continue

            frame_box = ((self._pic_xy_px[0] * x_cnt) + x_ofs, (self._pic_xy_px[1] * y_cnt) + y_ofs)
            poster.paste(tmp_img, frame_box)

            # Determine the next x,y coords
            if x_cnt + 1 < x_per_line:
                x_cnt += 1
            else:
                x_cnt = 0
                y_cnt += 1

        # Print the text for the title centered
        draw = ImageDraw.Draw(poster)
        font = ImageFont.truetype(self._ttfont, self._font_size_px)
        txt_x, txt_y = draw.textsize(self._title, font=font)

        txt_x = ( self._poster_xy_px[ 0 ] / 2 ) - ( txt_x / 2 )
        draw.text(
            (txt_x, self._xy_margin_px[1]),
            self._title,
            (255, 255, 255),
            font=font
            )

        # Save the poster
        poster.save(filename)

    def _get_movie_info( self ):
        """
        Retrieve json formatted video information using ffprobe
        """
        ffprobe_args = [
            self._video_path,
            '-print_format', 'json',
            '-show_streams',
            '-loglevel', 'quiet'
            ]
        result = self._run_cmd('ffprobe', ffprobe_args)
        return json.loads(result)

    def _run_cmd(self, cmd: str, args: List[str] = []) -> str:
        cmd_to_run = [cmd] + args
        result = subprocess.run(
            cmd_to_run,
            stdout = subprocess.PIPE,
            stderr = subprocess.STDOUT,
            text = True
            )
        return result.stdout

    def _calc_optimal_res( self ):
        """
        Calculate the optimal resolution of each video frame
        """

        # loop from the smallest possible x size to the largest
        # increment the x resolution until it will no longer fit
        # in the defined area.

        # TODO: Determine the implicit function for this
        x_len_px = self._target_xy_px[0]
        y_len_px = self._target_xy_px[1]

        x_res = 1
        for i in range(int(self._ratio) + 1, x_len_px):
            x_res = i
            y_res = int(float(x_res) / self._ratio)

            per_x_line = int(x_len_px / x_res)
            y_lines = int(math.ceil(float(self._frame_ct) / float(per_x_line)))

            # break if the total size is too big
            if y_lines * y_res > y_len_px:
                break

        #return the previous resolution
        x_res = x_res - 1
        y_res = int( float( x_res ) / self._ratio )
        return (x_res, y_res)

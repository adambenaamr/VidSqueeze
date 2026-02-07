from .ffmpeg import FFMPEG
import argparse
from pathlib import Path

class VidSqueeze:
  def __init__(self) -> None:
    pass

  def run(self) -> None:
    parser = argparse.ArgumentParser(prog='vs', description='Simple video compression tool using FFMPEG that gets periodically updated')

    parser.add_argument('path', nargs='?', default='.', help='Input directory (default = current directory)')
    parser.add_argument('--apple', action='store_true', help='Generate Apple-compatible videos (H.264)')
    parser.add_argument('--delete-originals', action='store_true', help='Delete source files after successful conversion')

    args = parser.parse_args()
    input_directory = Path(args.path).expanduser().resolve()
    output_directory = Path(args.path)

    ffmpeg = FFMPEG()

    ffmpeg.main(input_directory=input_directory, apple=args.apple, output_directory=output_directory)

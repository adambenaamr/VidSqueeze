import subprocess
from pathlib import Path
from tqdm import tqdm
import threading
import sys

def high_compression(input_file, output_file):
  """
  This is the FFmpeg compression used for general archiving as it uses the best known (to my knowledge)
  compression algorithm and bit set, however this format cannot be natively rendered by MacOS.

  :param input_file: Literally the input file
  :param output_file: Litterally no difference in input or output file as it will have the same
  file name in the end just a different file extension

  :return command: The CLI-based command used for FFMPEG to start it's compress process
  """
  command = [
    'ffmpeg',
    '-i', input_file,
    '-c:v', 'libx265',
    '-c:a', 'copy',
    '-crf', '28',
    output_file
  ]

  return command

def regular_compression(input_file, output_file):
  """
  This is the FFmpeg compression used for decent archiving this format can be natively rendered
  by MacOS but it is generally not the best as file sizes can still remain large and compression
  can be inefficient at times.

  :param input_file: Literally the input file
  :param output_file: Litterally no difference in input or output file as it will have the same
  file name in the end just a different file extension

  :return command: The CLI-based command used for FFMPEG to start it's compress process
  """
  command = [
    'ffmpeg',
    '-i', input_file,
    '-c:v', 'libx264',
    '-c:a', 'copy',
    '-crf', '28',
    output_file
  ]

  return command

def prompt_input_directory(prompt_text: str, max_attempt: int = 3) -> Path:
  """
  Prompt the user to enter a valid existing directory path.

  The user is prompted up to `max_attempt` times to provide a directory path.
  The input is expanded (e.g., `~`) and resolved to an absolute path.
  If a valid directory is provided, the corresponding Path object is returned
  After exceeding the maximum number of failed attempts, the program exits.

  :param prompt_text: The prompt displayed to the user.
  :type  prompt_text: str

  :param max_attempt: Maximum number of input attempts before existing (default = 3).
  :type max_attempt: int

  :return Path: A resolved Path object pointing to an existing directory.
  :rtype Path: Path

  :raise SystemExit: If the user fails to provide a valid directory within the allowed number of attempts.
  """
  attempts: int = 0

  while attempts < max_attempt:
    user_input: str = input(prompt_text)

    if isinstance(user_input, str):
      user_input: str = user_input.strip()
      path: Path = Path(user_input).expanduser().resolve()

      if path.exists() and path.is_dir():
        return path
      else:
        print(f'{user_input} is not a valid directory path.')
    else:
      print('Input must be in string format')
    
    attempts += 1
  
  print('Too many invalid attempts... Exiting...')
  sys.exit(1)

def prompt_output_directory(prompt_text: str, max_attempt: int = 3) -> Path:
  """
  Prompt the user to enter an output directory path.

  The user is prompted up to `max_attempt` times to provide a directory path.
  If the directory already exists, it is returned as a resolved Path.
  If it does not exist, the directory is created (including parent directories)
  and then returned. The program exists after too many invalid attempts.
  
  :param prompt_text: The prompt displayed to the user.
  :type prompt_text: str

  :param max_attempt: Maximum number of input attempts before exiting (default = 3)
  :type max_attempt: int
  
  :return Path: A resolved Path object pointing to the existing or newly created directory.
  :rtype: Path

  :raise SystemExit: If the user fails to provide a valid path within the allowed number of attempts.
  """
  attempts: int = 0

  while attempts < max_attempt:
    user_input: str = input(prompt_text)

    try:
      user_input: str = user_input.strip()
      path: Path = Path(user_input).expanduser().resolve()

      if path.exists() and path.is_dir():
        return path
    except Exception as e:
      print(e)
    
    else:
      # Create the output directory if it doesn't already exist
      path.mkdir(parents=True, exist_ok=True)

      print(f'Created output directory: {path}')

      return path

    attempts += 1
  
  print('Too many invalid attempts... Exiting...')
  sys.exit(1)

# Stream a subprocess pipe line-by-line and write output via `tqdm`
# so progress bars remain intact, then close the pipe when down
def stream_output(pipe):
  for line in iter(pipe.readline, b''):
    tqdm.write(line.decode('utf-8').strip())
  
  pipe.close()

def start_compression_process(video_file_list: list[Path], user_defined_output_directory: Path, user_compression_type: str = '') -> None:
  """
  This function iterates over a list of video files, applies the selected
  compression strategy (high-efficiency or Apple-compatible), and writes the
  compressed output to the speecified directory. A progress bar is displayed
  during processing, and original files are deleted upon successful
  compression.

  Compression behavior:
    - 'highest' -> Uses H.265 (libx265) for maximum compression efficiency
    - Any other value -> Uses H.264 (libx264) for broader compatibility
  
  :param video_file_list: A list of paths to video files that will be compressed.
  :type video_file_list: list[Path]
  
  :param user_defined_output_directory: The directory where compressed video files will be written.
  :type user_defined_output_directory: Path
  
  :param user_compression_type: Determines the compression method to use. Set to 'highest' for
  high-efficiency H.265 compression; any other value defaults to Apple-compatible H.264 compression.
  :type user_compression_type: str, optional

  :return None: This function does not return a value. Compression is performed as a 
  side effect on the filesystem.
  """
  with tqdm(total=len(video_file_list), desc='Processing Videos', unit='file') as progress_bar:

    # Iterate through files within the given directory
    for file in video_file_list:
      output_file: Path = user_defined_output_directory / file.with_suffix('.mp4').name

      if user_compression_type == 'highest':
        cmd = high_compression(file, output_file)
      else:
        cmd = regular_compression(file, output_file)

      # Start FFMPEG process
      process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

      # Stread FFMPEG stderr (where the progress information goes)
      stderr_thread = threading.Thread(target=stream_output, args=(process.stderr,))

      stderr_thread.start()
      process.wait()
      stderr_thread.join()

      if process.returncode == 0:
        progress_bar.set_postfix_str(f'{file.name}')

        # Attempt to delete the original file once the compression is completed
        # If compression fails, then the original file is untouched and an error
        # message is displayed
        try:
          file.unlink()
        except Exception as e:
          tqdm.write(f'Failed to delete {file.name}: {e}')
      else:
        progress_bar.set_postfix_str(f'Error: {file.name}')
      
      # Progress bar will update after the video file compression process has
      # been fully completed
      progress_bar.update(1)

def main():
  # Prompt the user for input and output directories
  input_directory: Path = prompt_input_directory('Enter input directory path (e.g., ./videos): ')
  output_directory: Path = prompt_output_directory('Enter output directory path (e.g., ./videos_converted): ')
  apple_compatible: str = input('Do you want your file(s) to be apple compatible? (y/N): ')
  video_extensions: set[str] = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}
  video_files: list[Path] = [f for f in input_directory.iterdir() if f.is_file() and f.suffix.lower() in video_extensions]

  # If there are no files with valid video extensions, then exit the process
  if not video_files:
    print('No video files found...')
    sys.exit(0)
  
  # Uses the low compression algorithm if the user selects yes and the high
  # compression alogirthm if the user selects no (with reverse logic on this if-else statement)
  if apple_compatible.lower() not in ['y', 'yes']:
    start_compression_process(video_files, output_directory, 'highest')
  else:
    start_compression_process(video_files, output_directory)

if __name__ == '__main__':
  main()

import subprocess
from pathlib import Path
from tqdm import tqdm
import threading
import sys
import json

# Function to prompt the user to enter a valid directory
# Will exit itself after 3 failed attempts
def prompt_directory(prompt_text: str, max_attempt: int = 2) -> Path:
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

# Get file duration in ms using ffprobe
def get_duration_ms(input_file: Path) -> int:
  result = subprocess.run(
    [
      'ffprobe',
      '-v', 'quiet',
      '-print_format', 'json',
      '-show_format',
      str(input_file)
    ],
    capture_output=True,
    text=True
  )

  try:
    data = json.loads(result.stdout)
    duration_sec = float(data['format']['duration'])

    return int(duration_sec * 1000)
  
  # If duration can't be read, progress bar will fallback
  except Exception:
    return None # type: ignore

def build_ffmpeg_command(input_file: Path, output_file: Path, apple: bool):
  codec = 'libx264' if apple else 'libx265'

  return [
    'ffmpeg',
    '-i', str(input_file),
    '-c:v', codec,
    '-c:a', 'copy',
    '-crf', '28',
    '-progress', '-',
    '-nostats',
    str(output_file)
  ]

def stream_output(pipe):
  for line in iter(pipe.readline, b''):
    tqdm.write(line.decode('utf-8').strip())
  
  pipe.close()

def run_ffmpeg_with_progress(command, duration_ms, file_name):
  with tqdm(total=duration_ms or 100, desc=file_name, unit='ms', leave=False) as file_bar:
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=False)

    # Stread FFMPEG stderr (where the progress information goes)
    stderr_thread = threading.Thread(target=stream_output, args=(process.stderr,))

    # TODO: This code below currently shows the progress bar, however, it does not update on every frame.
    # Rather it updates once the video has finished compressing which defeats the whole purpose of having the
    # second progress bar.
    stderr_thread.start()
    stderr_thread.join()
    process.wait()

    # for line in process.stdout: # type: ignore
    #   line = line.strip()

      # Extract ms progress
      # if line.startswith('out_time_ms='):
      #   value = line.split('=')[1]

      #   # Skip invalid values
      #   if value.isdigit():
      #     current = int(value)
      #     file_bar.n = current
      #     file_bar.refresh()
      #   else:
      #     continue
      # elif line == 'progress=end':
      #   file_bar.n = file_bar.total
      #   file_bar.refresh()
    
    # process.wait()
    
    return process.returncode
  
def main():
  # Prompt the user for input and output directories
  input_directory: Path = prompt_directory('Enter input directory path (e.g., ./videos): ')
  output_directory: Path = prompt_directory('Enter output directory path (e.g., ./videos_converted): ')
  video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.webm'}

  # Ensure output folder exists
  output_directory.mkdir(parents=True, exist_ok=True)

  # Find video files
  video_files = [f for f in input_directory.iterdir() if f.is_file() and f.suffix.lower() in video_extensions]

  if not video_files:
    print('No video files in the input directory.')
    sys.exit(0)
  
  apple = input('Do you want your file(s) to be apple compatible? (y/N): ').lower in ['y', 'yes']

  # Main progress bar
  with tqdm(total=len(video_files), desc='Processing Videos', unit='file') as main_bar:
    for file in video_files:
      output_file: Path = output_directory / file.with_suffix('.mp4').name

      # Get file duration
      duration_ms = get_duration_ms(file)

      # Build FFmpeg command
      command = build_ffmpeg_command(file, output_file, apple)

      # Run FFmpeg command
      returncode = run_ffmpeg_with_progress(command, duration_ms, file.name)

      # Update top-level/main bar
      if returncode == 0:
        main_bar.set_postfix_str(f'Finished: {file.name}')

        # Delete the original file safely
        try:
          file.unlink()
        except Exception as e:
          tqdm.write(f'Could not delete {file.name}: {e}')
      else:
        main_bar.set_postfix_str(f'Error: {file.name}')
      
      main_bar.update(1)

if __name__ == '__main__':
  main()

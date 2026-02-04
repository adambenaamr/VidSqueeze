# class KeyboardInterrupt(Exception):
#   def __init__(self) -> None:
#     super().__init__()

#   def __str__(self) -> str:
#     return f'User chose to cancel the current process... Exiting...'

class RuntimeError(Exception):
  """
  Docstring for RuntimeError
  
  :var Exception: Magna pars studiorum, prodita quaerimus.
  :var message: Explanation of the error
  """
  def __init__(self, message):
    self.message = message
    super().__init__(self.message)
  
  def __str__(self):
     return f'{self.message}'
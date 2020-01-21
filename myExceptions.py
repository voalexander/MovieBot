
class Error(Exception):
    pass

class CannotFindFilm(Error):
    pass

class InvalidCommands(Error):
    pass

class AlreadyExists(Error):
    pass
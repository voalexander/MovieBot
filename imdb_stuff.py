import imdb
from imdb import IMDb
import imdbExceptions

class IMDB(object):
    def __init__(self):
        self.errors = []
        self.ia = imdb.IMDb()

    def getFilmData(self, title):
        try:
            filmData = self.ia.get_movie(self.ia.search_movie(title)[0].movieID)
            data = []
            data.append(filmData.get("title"))
            data.append(str(filmData.get("rating")))
            data.append(filmData.get("plot")[0].split("::")[0]) # Split to remove imdb author
        except Exception:
            raise imdbExceptions.CannotFindFilm
        return data

    def alreadyExists(self, film, existingEntries):
        for entry in existingEntries:
            if film == entry:
                return True
        return False
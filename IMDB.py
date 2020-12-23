import imdb
from imdb import IMDb
import traceback

class IMDB(object):
    def __init__(self):
        self.ia = imdb.IMDb()

    def getCover(self, id):
        return self.ia.get_movie(id).get("cover url")

    def getTop3(self, title):
        data = []
        print("Searching IMDb for {}".format(title))
        try:
            top3 = self.ia.search_movie(title)
            print("Found {} results".format(len(top3)))
            print(top3[0])
            for i in range(0, len(top3) if len(top3) < 3 else 3):
                filmData = self.ia.get_movie(top3[i].movieID)
                title = filmData.get("title").replace('\'', '')
                rating = str(filmData.get("rating"))
                plot = filmData.get("plot")
                link = self.ia.get_imdbURL(filmData)
                image = filmData.get("cover url")
                if plot is not None:
                    plot = plot[0].split("::")[0].replace('\'', '')
                else:
                    plot = "No plot found"
                data.append([title, rating, plot, top3[i].movieID, link, image])
        except Exception as e:
            traceback.print_exc()
            return data
        return data


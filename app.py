from flask import Flask, render_template, request,jsonify
from flask_cors import CORS,cross_origin
import requests
from bs4 import BeautifulSoup as bs
from urllib.request import urlopen as uReq
import logging
import pymongo
logging.basicConfig(filename="scrapper.log" , level=logging.INFO)

app = Flask(__name__)

@app.route("/", methods = ['GET'])
def homepage():
    return render_template("index.html")

@app.route("/review" , methods = ['POST' , 'GET'])
def index():
    if request.method == 'POST':
        try:
            searchString = request.form['content'].replace(" ","")
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")

            bigboxes = flipkart_html.findAll("div", {"class": "cPHDOP col-12-12"})
            del bigboxes[0:3]
            if not bigboxes:
                return "Flipkart page layout has changed. No products found."

            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink)
            prodRes.encoding='utf-8'
            prod_html = bs(prodRes.text, "html.parser")
            commentboxes = prod_html.find_all('div', {'class': "RcXBOT"})
            filename = searchString + ".csv"
            fw = open(filename, "w")
            headers = "Product, Customer Name, Rating, Heading, Comment \n"
            fw.write(headers)
            reviews = []

            for commentbox in commentboxes:
                try:
                    name = commentbox.div.div.find_all('p', {'class': '_2NsDsF AwS1CA'})[0].text
                except:
                    name = 'No Name'
                    logging.info("name")

                try:
                    rating = commentbox.div.div.div.div.text
                except:
                    rating = 'No Rating'
                    logging.info("rating")

                try:
                    commentHead = commentbox.div.div.div.p.text
                except:
                    commentHead = 'No Comment Heading'
                    logging.info(commentHead)

                try:
                    comtag = commentbox.div.div.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except Exception as e:
                    custComment = 'No Comment'
                    logging.info(e)

                mydict = {
                    "Product": searchString,
                    "Name": name,
                    "Rating": rating,
                    "CommentHead": commentHead,
                    "Comment": custComment
                }
                reviews.append(mydict)

            logging.info("log my final result {}".format(reviews))
            client = pymongo.MongoClient("mongodb://devshah0408:Dev1234Shah@ac-spsojno-shard-00-00.fhwfzdr.mongodb.net:27017,ac-spsojno-shard-00-01.fhwfzdr.mongodb.net:27017,ac-spsojno-shard-00-02.fhwfzdr.mongodb.net:27017/?replicaSet=atlas-xsyp0u-shard-0&ssl=true&authSource=admin&retryWrites=true&w=majority&appName=Cluster0")
            db = client['review_scrap']
            review_col = db['review_scrap_data']
            review_col.insert_many(reviews)
            
            return render_template('result.html', reviews=reviews)
        except Exception as e:
            logging.info(e)
            return f'Something is wrong: {e}'
    else:
        return render_template('index.html')



if __name__=="__main__":
    app.run(host="0.0.0.0")
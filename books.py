
from flask import Flask, request, jsonify, make_response
from pymongo import MongoClient
from bson import ObjectId
import datetime
import bcrypt
from flask_cors import CORS

app = Flask(__name__)
CORS(app)


client = MongoClient("mongodb://127.0.0.1:27017")
database = client.books # Using the "books" database
books = database.best_books # Using the "best_books" collection



#################################################
# GET requests
#################################################

# Get all book records
@app.route("/api/v1.0/books", methods=["GET"])
def get_all_book_records():
    page_number, page_size = 1, 15
    if request.args.get('pn'):
        page_number = int(request.args.get('pn'))
    if request.args.get('ps'):
        page_size = int(request.args.get('ps'))
    page_start = (page_size * (page_number - 1))
 
    book_data = []
    for book in books.find() \
                    .skip(page_start).limit(page_size):
        book['_id'] = str(book['_id'])
        for reader_review in book['reader_reviews']:
            reader_review['_id'] = str(reader_review['_id'])
        book_data.append(book)
    return make_response( jsonify(book_data), 200 )


 # Retrieve a specific book record
@app.route("/api/v1.0/books/<string:bookId>", \
            methods=["GET"])
def show_one_book_record(bookId):
    book = books.find_one({'_id':ObjectId(bookId)})
    if book is not None:
        book['_id'] = str(book['_id'])
        for reader_review in book['reader_reviews']:
            reader_review['_id'] = str(reader_review['_id'])
        return make_response( jsonify( book ), 200 )
    else:
        return make_response( jsonify( \
        {"error" : "Book ID is invalid, please enter a valid ID"} ), 404 )



#Get the title of the book after specifying the ID
@app.route("/api/v1.0/books/<string:bookId>/title", \
            methods=["GET"])
def get_book_title(bookId):
    book = books.find_one({'_id':ObjectId(bookId)}, {'title': 1 , '_id': 0})
    if book is not None:
        return make_response( jsonify( book ), 200 )
    else:
        return make_response( jsonify( \
        {"error" : "Book ID is invalid, please enter a valid ID"} ), 404 )




#Get the book's author after specifying the ID
@app.route("/api/v1.0/books/<string:bookId>/author", \
            methods=["GET"])
def get_author_of_book(bookId):
    book = books.find_one({'_id':ObjectId(bookId)}, {'author': 1 , '_id': 0})
    if book is not None:
        return make_response( jsonify( book ), 200 )
    else:
        return make_response( jsonify( \
        {"error" : "Book ID is invalid, please enter a valid ID"} ), 404 )



#Get the year that the book was published
@app.route("/api/v1.0/books/<string:bookId>/year", \
            methods=["GET"])
def get_published_year(bookId):
    book = books.find_one({'_id':ObjectId(bookId)}, {'year': 1 , '_id': 0})
    if book is not None:
        return make_response( jsonify( book ), 200 )
    else:
        return make_response( jsonify( \
        {"error" : "Book ID is invalid, please enter a valid ID"} ), 404 )





# Get all review(s) of a book record
@app.route("/api/v1.0/books/<string:bookId>/reader_reviews", \
           methods=["GET"])
def retrieve_reviews(bookId):
    list_of_reviews = []
    book = books.find_one( { "_id" : ObjectId(bookId) }, \
          { "reader_reviews" : 1, "_id" : 0 } )
    for bookreview in book["reader_reviews"]:
        bookreview["_id"] = str(bookreview["_id"])
        list_of_reviews.append(bookreview)
    return make_response( jsonify( list_of_reviews ), 200 )




# Get a specific book review by specifying the ID
@app.route("/api/v1.0/books/<bookId>/reader_reviews/<revId>", \
           methods=["GET"])
def retrive_one_review(bookId, revId):
    book = books.find_one( { "reader_reviews._id" : ObjectId(revId) }, \
                  { "_id" : 0, "reader_reviews.$" : 1 } )
    if book is None:
        return make_response( \
        jsonify(
        {"error":"The book review ID is invalid, please enter a valid ID"}), 404)
    book['reader_reviews'][0]['_id'] = \
                       str(book['reader_reviews'][0]['_id'])

    return make_response( jsonify( book['reader_reviews'][0]), 200)
    




#################################################
# POST requests
#################################################

# # Add a new book record to the collection
@app.route("/api/v1.0/books", methods=["POST"])
def add_new_book():
    if "author" in request.form and \
       "title" in request.form and \
       "country" in request.form and \
       "language" in request.form and \
       "cover_image" in request.form and \
       "pages" in request.form and \
       "year" in request.form:
        new_book = {
            "author" : request.form["author"],
            "title" : request.form["title"],
            "country" : request.form["country"],
            "language" : request.form["language"],
            "cover_image" : request.form["cover_image"],
            "pages" : request.form["pages"],
            "year" : request.form["year"],
            "reader_reviews" : []
        }
        new_book_id = books.insert_one( \
                                           new_book)
        new_book_link = "http://localhost:5000/api/v1.0/books/" \
            +  str(new_book_id.inserted_id)
        return make_response( jsonify(
                    {"url": new_book_link} ), 201)
    else:
        return make_response( jsonify(
                    {"error":"Data is missing. Please try again"} ), 404)




# Add a new review to a book
@app.route("/api/v1.0/books/<string:bookId>/reader_reviews", \
           methods=["POST"])
def add_new_book_review(bookId):
    new_review = {
        "_id" : ObjectId(),
        "name" : request.form["name"],
        "comments" : request.form["comments"],
        "book_rating" : request.form["book_rating"]
    }
    books.update_one( { "_id" : ObjectId(bookId) }, \
                { "$push": { "reader_reviews" : new_review } } )
    new_review_url = "http://localhost:5000/api/v1.0/books/" \
    + bookId  + "/reader_reviews/" + str(new_review['_id'])
    return make_response( jsonify( \
                { "url" : new_review_url } ), 201 )






#################################################
# PUT requests
#################################################

# Edit the details of a book
@app.route("/api/v1.0/books/<string:bookId>", \
           methods=["PUT"])           
def edit_book_details(bookId):
    if "author" in request.form and \
       "title" in request.form and \
       "country" in request.form and \
       "language" in request.form and \
       "cover_image" in request.form and \
       "pages" in request.form and \
       "year" in request.form:
        result = books.update_one( \
          { "_id" : ObjectId(bookId) }, {
            "$set" : { "author" : request.form["author"],
                       "title" : request.form["title"],
                       "country" : request.form["country"],
                       "language" : request.form["language"],
                       "cover_image" : request.form["cover_image"],
                       "pages" : request.form["pages"],
                       "year" : request.form["year"]

                    }
          }  )
        if result.matched_count == 1:
           updated_book_details = \
           "http://localhost:5000/api/v1.0/books/" + bookId
           return make_response( jsonify(
              { "url":updated_book_details } ), 200)
        else:
            return make_response( jsonify(
               { "error":"Enter a valid book ID" } ), 404)
    else:
        return make_response( jsonify(
           { "error" : "Data is missing. Please try again" } ), 404)




# Edit a book review
@app.route("/api/v1.0/books/<bookId>/reader_reviews/<revId>", \
           methods=["PUT"])
def alter_book_review(bookId, revId):
    altered_review = {
        "reader_reviews.$.name" : request.form["name"],
        "reader_reviews.$.comments" : request.form["comments"],
        "reader_reviews.$.book_rating" : request.form['book_rating']
    }
    books.update_one( \
          { "reader_reviews._id" : ObjectId(revId) }, \
          { "$set" : altered_review } )
    altered_review_url = "http://localhost:5000/api/v1.0/books/" + \
    bookId + "/reader_reviews/" + revId
    return make_response( jsonify( \
                  {"url":altered_review_url} ), 200)




#################################################
# DELETE requests
#################################################

# Delete a book record from the collection
@app.route("/api/v1.0/books/<string:bookId>", \
           methods=["DELETE"])
def delete_book(bookId):
    result = books.delete_one( \
                 { "_id" : ObjectId(bookId) } )
    if result.deleted_count == 1:
        return make_response( jsonify( {} ), 204)
    else:
        return make_response( jsonify( \
        { "error" : "This book record has already been deleted" } ), 404)



# Delete a review for a book
@app.route("/api/v1.0/books/<bookId>/reader_reviews/<revId>", \
           methods=["DELETE"])
def remove_book_review(bookId, revId):
    books.update_one( \
        { "_id" : ObjectId(bookId) }, \
        { "$pull" : { "reader_reviews" : \
        { "_id" : ObjectId(revId) } } } )
    return make_response( jsonify( {} ), 204)



if __name__ == "__main__":
    app.run(debug=True)
# -*- coding: utf-8 -*-
"""
Created on Sun May  5 15:28:40 2024

@author: nours
"""

import tkinter as tk
from tkinter import messagebox
from scipy import spatial
import mysql.connector
import numpy
from nltk.corpus import stopwords
import nltk
from nltk.stem.snowball import FrenchStemmer
from sklearn.feature_extraction.text import TfidfTransformer

def SimilariteCosinus(a, b, matricebinaire):
    return (1 - spatial.distance.cosine(matricebinaire[a], matricebinaire[b]))

ListTotaliteMots = set()
dictProduits = {}
StopList = list(stopwords.words('french'))
StopList.extend(['.', '-', ':', '?', '!', '#'])
print(StopList)

conn = mysql.connector.connect(host="localhost", user="root", password="", database="systemerecommendation")
cursor = conn.cursor()

cursor.execute("SELECT * FROM produit")
produits = cursor.fetchall()

for p in produits:
    idPdt = int(p[0])
    description = p[2]
    Mots = nltk.word_tokenize(description)
    stemmer = FrenchStemmer()
    MotsStems = [stemmer.stem(m) for m in Mots]
    ListFinalMots = [m for m in MotsStems if m not in StopList]
    for m in ListFinalMots:
        ListTotaliteMots.add(m)
    dictProduits[idPdt] = ListFinalMots

nbmot = len(ListTotaliteMots)
nbproduit = len(produits)
ListTotaliteMots = list(ListTotaliteMots)
matricebinaire = numpy.zeros((nbproduit, nbmot))

for i in range(nbproduit):
    j = 0
    for m in ListTotaliteMots:
        if m in dictProduits[(i + 1)]:
            matricebinaire[i][j] = 1
        j += 1

matriceSimilarite = numpy.zeros((nbproduit, nbproduit))
for i in range(nbproduit):
    for j in range(nbproduit):
        matriceSimilarite[i][j] = SimilariteCosinus(i, j, matricebinaire)

def calculate_similarity(product_id):
    # Connect to the database
    conn = mysql.connector.connect(host="localhost", user="root", password="", database="systemerecommendation")
    cursor = conn.cursor()

    # Get the similarity scores for the given product_id
    similarities = list(matriceSimilarite[product_id])

    # Exclude the product itself from the list
    similarities[product_id] = 0.0

    # Sort the similarities by score in descending order
    similarities.sort(reverse=True)

    # Keep track of seen product IDs to avoid duplicates
    seen_ids = set()
    similar_products = []
    for sim in similarities:
        where_result = numpy.where(matriceSimilarite[product_id] == sim)[0]
        if where_result.size > 0:
            similar_product_id = where_result[0]
            if similar_product_id not in seen_ids:
                seen_ids.add(similar_product_id)
                cursor.execute(f"SELECT name FROM produit WHERE id = {similar_product_id + 1}")
                similar_product_name = cursor.fetchone()[0]
                similar_products.append((similar_product_name, sim))
                print(f"Found similar product: {similar_product_name} (Similarity: {sim})")

            # Break if we found 3 unique similar products
            if len(similar_products) == 3:
                break

    # Display the results in a message box
    result_text = f"Top 3 highest similarity rates for '{produits[product_id][1]}':\n"
    for i, (similar_product_name, similarity) in enumerate(similar_products, start=1):
        result_text += f"{i}. {similar_product_name} (Similarity Rate: {similarity})\n"

    messagebox.showinfo("Similar Products", result_text)

    # Close the database connection
    conn.close()
def compute_tfidf_matrix(binary_matrix):
    transformer = TfidfTransformer()
    tfidf_matrix = transformer.fit_transform(binary_matrix)
    return tfidf_matrix.toarray()

# Compute the TF-IDF matrix
tfidf_matrix = compute_tfidf_matrix(matricebinaire)

# Use the TF-IDF matrix for further processing
matriceSimilarite_tfidf = numpy.zeros((nbproduit, nbproduit))
for i in range(nbproduit):
    for j in range(nbproduit):
        matriceSimilarite_tfidf[i][j] = SimilariteCosinus(i, j, tfidf_matrix)
print(matriceSimilarite_tfidf)

# Fermer la connexion à la base de données
# conn.close()
def SimilariteJaccard(a, b, matricebinaire):
    intersection = sum((matricebinaire[a] == 1) & (matricebinaire[b] == 1))
    union = sum((matricebinaire[a] == 1) | (matricebinaire[b] == 1))
    return intersection / union

def SimilariteEuclidienne(a, b, matricebinaire):
    return 1 / (1 + spatial.distance.euclidean(matricebinaire[a], matricebinaire[b]))

def SimilariteCorrelation(a, b, matricebinaire):
    return 1 - spatial.distance.correlation(matricebinaire[a], matricebinaire[b])

matriceSimilarite_jaccard = numpy.zeros((nbproduit, nbproduit))
for i in range(nbproduit):
    for j in range(nbproduit):
        matriceSimilarite_jaccard[i][j] = SimilariteJaccard(i, j, matricebinaire)
print(matriceSimilarite_jaccard)

matriceSimilarite_euclidienne = numpy.zeros((nbproduit, nbproduit))
for i in range(nbproduit):
    for j in range(nbproduit):
        matriceSimilarite_euclidienne[i][j] = SimilariteEuclidienne(i, j, matricebinaire)
print(matriceSimilarite_euclidienne)

matriceSimilarite_correlation = numpy.zeros((nbproduit, nbproduit))
for i in range(nbproduit):
    for j in range(nbproduit):
        matriceSimilarite_correlation[i][j] = SimilariteCorrelation(i, j, matricebinaire)
print(matriceSimilarite_correlation)

print(matriceSimilarite)
for i in range (nbproduit):
    for j in range (nbproduit):
        if (i!=j):
            cursor.execute("""INSERT INTO simbc(idpdt1,idpdt2,sim)values(""" +str(i+1)+""",""" + str(j+1) +""","""+str(matriceSimilarite[i][j])+""")""")
conn.commit()
print("successful")
# Function to handle button click
def on_button_click():
    try:
        # Get the product ID from the entry widget
        product_id = int(entry.get())

        # Calculate the similarity for the given product ID
        calculate_similarity(product_id - 1)

    except ValueError:
        messagebox.showerror("Error", "Please enter a valid product ID.")

# Create the main window
root = tk.Tk()
root.title("Product Similarity Calculator")

# Add a label
label = tk.Label(root, text="Enter Product ID:")
label.pack()

# Add an entry field
entry = tk.Entry(root)
entry.pack()

# Add a button to calculate similarity
button = tk.Button(root, text="Calculate Similarity", command=on_button_click)
button.pack()

# Start the Tkinter event loop
root.mainloop()

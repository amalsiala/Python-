# -*- coding: utf-8 -*-
"""
Created on Sun May  5 16:24:33 2024

@author: nours
"""

import tkinter as tk
from tkinter import messagebox
import numpy as np
import mysql.connector


def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def generate_recommendations():
    try:
        conn = mysql.connector.connect(host="localhost", user="root", password="", database="systemerecommendation")
        cursor = conn.cursor()

        
        cursor.execute("SELECT COUNT(*) FROM user")
        nbUser = int(cursor.fetchone()[0])

        cursor.execute("SELECT COUNT(*) FROM produit")
        nbItems = int(cursor.fetchone()[0])

        
        matriceUserItems = np.zeros((nbUser, nbItems))

        cursor.execute("SELECT * FROM user")
        users = cursor.fetchall()

        
        for user in users:
            cursor.execute("SELECT * FROM note WHERE id_user = %s", (int(user[0]),))
            user_notes = cursor.fetchall()
            for note in user_notes:
                matriceUserItems[int(user[0])-1][note[1] - 1] = note[2]  

      
        matriceUserUser = np.zeros((nbUser, nbUser))

        for i in range(nbUser):
            for j in range(nbUser):
                matriceUserUser[i][j] = cosine_similarity(matriceUserItems[i], matriceUserItems[j])

        
        neighborhood_size = 5
        user_neighborhoods = {}
        for i in range(nbUser):
            most_similar_users = np.argsort(matriceUserUser[i])[-neighborhood_size-1:-1][::-1]
            user_neighborhoods[i] = most_similar_users

        
        user_recommendations = {}
        for id_user in range(nbUser):
            rated_items = np.nonzero(matriceUserItems[id_user])[0]
            recommended_items = set()
            for neighbor_id in user_neighborhoods[id_user]:
                neighbor_rated_items = np.nonzero(matriceUserItems[neighbor_id])[0]
                for item_id in neighbor_rated_items:
                    if item_id not in rated_items:
                        recommended_items.add(item_id)
            user_recommendations[id_user] = recommended_items

      
        result_text = ""
        for id_user, recommended_items in user_recommendations.items():
            cursor.execute("SELECT nom FROM user WHERE id_user = %s", (int(id_user) + 1,))
            user_name = cursor.fetchone()[0]
            result_text += f"{user_name} recommendations: {recommended_items}\n"

        result_text += "\n"

        for user_id, neighbors in user_neighborhoods.items():
            cursor.execute("SELECT nom FROM user WHERE id_user = %s", (int(user_id) + 1,))
            user_name = cursor.fetchone()[0]
            neighbor_names = []
            for neighbor_id in neighbors:
                cursor.execute("SELECT nom FROM user WHERE id_user = %s", (int(neighbor_id) + 1,))
                neighbor_name = cursor.fetchone()[0]
                neighbor_names.append(neighbor_name)
            result_text += f"{user_name} is similar to: {', '.join(neighbor_names)}\n"

        messagebox.showinfo("Recommendations and Similarities", result_text)

        result_text = ""
        for id_user, recommended_items in user_recommendations.items():
            cursor.execute("SELECT nom FROM user WHERE id_user = %s", (int(id_user) + 1,))
            user_name = cursor.fetchone()[0]
            result_text += f"{user_name} bought the following products:\n"
            for item_id, note in enumerate(matriceUserItems[id_user]):
                if note > 0:
                    cursor.execute("SELECT id, name FROM produit WHERE id = %s", (item_id + 1,))
                    item_data = cursor.fetchone()
                    result_text += f"({item_data[0]}, {item_data[1]}), "
            result_text += "\n\n"

        messagebox.showinfo("Products Bought by Users", result_text)

        conn.close()

    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")


root = tk.Tk()
root.title("Product Recommendation System")


button = tk.Button(root, text="Generate Recommendations", command=generate_recommendations)
button.pack(pady=20)

root.mainloop()

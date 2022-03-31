import numpy as np
import pandas as pd
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

documents = []
for file in os.listdir("temp"):
    text_file = open(os.path.join("temp", file))
    data = text_file.read()
    text_file.close()
    documents.append(data)

vectorizer = TfidfVectorizer()
vectors = vectorizer.fit_transform(["what is my ip", "my ip has been provided"])
feature_names = vectorizer.get_feature_names()
dense = vectors.todense()
denselist = dense.tolist()
df = pd.DataFrame(denselist, columns=feature_names)

print(cosine_similarity(dense[0], dense[1]))
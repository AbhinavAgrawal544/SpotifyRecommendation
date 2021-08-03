# -*- coding: utf-8 -*-
"""Spotify_rec.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1aWvWxgu8iG-QOzKtADp7xo5i_hopKE55
"""

!pip install -U yellowbrick
!pip install scikit-learn-extra
!pip install spotipy==2.16.1
!pip install plotly --upgrade

# Commented out IPython magic to ensure Python compatibility.
import os 
import numpy as np
import pandas as pd
import time
from sklearn.metrics import euclidean_distances

import matplotlib.pyplot as plt                                         
# %matplotlib inline                                      
import seaborn as sns                                                   
from yellowbrick.target import FeatureCorrelation
import plotly.express as px                                              
from plotly.offline import plot                                         
from sklearn.manifold import TSNE                                       
from sklearn.decomposition import PCA                                   

from sklearn.cluster import KMeans
from sklearn_extra.cluster import KMedoids
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from collections import defaultdict


from scipy.spatial.distance import cdist
import difflib

import warnings

data = pd.read_csv("/content/sample_data/data.csv")
genre_data = pd.read_csv('/content/sample_data/data_by_genres.csv')
year_data = pd.read_csv('/content/sample_data/data_by_year.csv')

data.info()

genre_data.info()

year_data.info()

feature_names = ['acousticness', 'danceability', 'energy', 'instrumentalness',
       'liveness', 'loudness', 'speechiness', 'tempo', 'valence','duration_ms','explicit','key','mode','year']

X, y = data[feature_names], data['popularity']

# Create a list of the feature names
features = np.array(feature_names)

visualizer = FeatureCorrelation(labels=features)

plt.rcParams['figure.figsize']=(10,10)
visualizer.fit(X, y)

#Music Over Time
def get_decade(year):
    period_start = int(year/10) * 10
    decade = '{}s'.format(period_start)
    return decade

data['decade'] = data['year'].apply(get_decade)

sns.set(rc={'figure.figsize':(11 ,6)})
sns.countplot(data['decade'])

#Characteristics of Different Genres
top10_genres = genre_data.nlargest(10, 'popularity')

fig = px.bar(top10_genres, x='genres', y=['valence', 'energy', 'danceability', 'acousticness'], barmode='group')
fig.show()

### Clustering Genres with K-Means ###

start = time.time()

cluster_pipeline = Pipeline([('scaler', StandardScaler()), ('kmeans', KMeans(n_clusters=10))])
X = genre_data.select_dtypes(np.number)
cluster_pipeline.fit(X)
genre_data['cluster'] = cluster_pipeline.predict(X)
print(genre_data['cluster'])

end = time.time()
print ("\nTime elapsed:", end - start)

### Visualizing the Clusters with t-SNE ###

tsne_pipeline = Pipeline([('scaler', StandardScaler()), ('tsne', TSNE(n_components=2, verbose=2))])
genre_embedding = tsne_pipeline.fit_transform(X)
projection = pd.DataFrame(columns=['x', 'y'], data=genre_embedding)
projection['genres'] = genre_data['genres']
projection['cluster'] = genre_data['cluster']

fig = px.scatter( projection, x='x', y='y', color='cluster', hover_data=['x', 'y', 'genres'])
fig.show()

### Clustering Genres with K-Medoids ###

start = time.time()

cluster_pipeline = Pipeline([('scaler', StandardScaler()), ('kmedoids', KMedoids(n_clusters=10))])
X = genre_data.select_dtypes(np.number)
cluster_pipeline.fit(X)
genre_data['cluster'] = cluster_pipeline.predict(X)
print(genre_data['cluster'])
end = time.time()

print ("\nTime elapsed:", end - start)

### Visualizing the Clusters with t-SNE ###

tsne_pipeline2 = Pipeline([('scaler', StandardScaler()), ('tsne', TSNE(n_components=2, verbose=2))])
genre_embedding2 = tsne_pipeline2.fit_transform(X)
projection2 = pd.DataFrame(columns=['x', 'y'], data=genre_embedding)
projection2['genres'] = genre_data['genres']
projection2['cluster'] = genre_data['cluster']

fig = px.scatter(
    projection2, x='x', y='y', color='cluster', hover_data=['x', 'y', 'genres'])
fig.show()

### Clustering Songs with K-Means ###

start = time.time()

song_cluster_pipeline = Pipeline([('scaler', StandardScaler()), 
                                  ('kmeans', KMeans(n_clusters=20, 
                                    verbose=2, n_jobs=4))],verbose=True)

X = data.select_dtypes(np.number)
number_cols = list(X.columns)
song_cluster_pipeline.fit(X)
song_cluster_labels = song_cluster_pipeline.predict(X)
data['cluster_label'] = song_cluster_labels
print(data['cluster_label'])

end = time.time()
print ("\nTime elapsed:", end - start)

### Visualizing the Clusters with PCA ###

from sklearn.decomposition import PCA

pca_pipeline = Pipeline([('scaler', StandardScaler()), ('PCA', PCA(n_components=2))])
song_embedding = pca_pipeline.fit_transform(X)
projection = pd.DataFrame(columns=['x', 'y'], data=song_embedding)
projection['title'] = data['name']
projection['cluster'] = data['cluster_label']

fig = px.scatter(
    projection, x='x', y='y', color='cluster', hover_data=['x', 'y', 'title'])
fig.show()

### Clustering Songs with K-Medoids ###

#start = time.time()
#cluster_pipeline2 = Pipeline([('scaler', StandardScaler()), ('kmedoids', KMedoids(n_clusters=20, init='k-medoids++'))])

#X2 = data.select_dtypes(np.number)
#cluster_pipeline2.fit(X2)
#cluster_labels2 = cluster_pipeline2.predict(X2)
#data['cluster_label2'] = cluster_labels2
#print(data['cluster_label2'])

#end = time.time()
#print ("\nTime elapsed:", end - start)

#Establishing connection with Spotify Web API
cid = 'b6f3c9a684c94bf6a2b16e86d04efc0e'
secret = '2f82a05e1e83413cb635061b36178a12'
#client_credentials_manager = SpotifyClientCredentials(client_id=cid, client_secret=secret)
sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(client_id = cid, client_secret = secret))

#Building the recommendation system
number_cols = ['valence', 'year', 'acousticness', 'danceability', 'duration_ms', 'energy', 'explicit',
 'instrumentalness', 'key', 'liveness', 'loudness', 'mode', 'popularity', 'speechiness', 'tempo']

def find_song(name, year):
    song_data = defaultdict()
    results = sp.search(q= 'track: {} year: {}'.format(name,year), limit=1)
    if results['tracks']['items'] == []:
        return None

    results = results['tracks']['items'][0]
    track_id = results['id']
    audio_features = sp.audio_features(track_id)[0]

    song_data['name'] = [name]
    song_data['year'] = [year]
    song_data['explicit'] = [int(results['explicit'])]
    song_data['duration_ms'] = [results['duration_ms']]
    song_data['popularity'] = [results['popularity']]

    for key, value in audio_features.items():
        song_data[key] = value

    return pd.DataFrame(song_data)

def get_song_data(song, spotify_data):
    
    try:
        song_data = spotify_data[(spotify_data['name'] == song['name']) & (spotify_data['year'] == song['year'])].iloc[0]
        return song_data
    
    except IndexError:
        return find_song(song['name'], song['year'])
        

def get_mean_vector(song_list, spotify_data):
    
    song_vectors = []
    
    for song in song_list:
        song_data = get_song_data(song, spotify_data)
        if song_data is None:
            print('Warning: {} does not exist in Spotify or in database'.format(song['name']))
            continue
        song_vector = song_data[number_cols].values
        song_vectors.append(song_vector)  
    
    song_matrix = np.array(list(song_vectors))
    return np.mean(song_matrix, axis=0)


def flatten_dict_list(dict_list):
    
    flattened_dict = defaultdict()
    for key in dict_list[0].keys():
        flattened_dict[key] = []
    
    for dictionary in dict_list:
        for key, value in dictionary.items():
            flattened_dict[key].append(value)
            
    return flattened_dict


def recommend_songs( song_list, spotify_data, n_songs=10):
    
    metadata_cols = ['name', 'year', 'artists']
    song_dict = flatten_dict_list(song_list)
    
    song_center = get_mean_vector(song_list, spotify_data)
    scaler = song_cluster_pipeline.steps[0][1]
    scaled_data = scaler.transform(spotify_data[number_cols])
    scaled_song_center = scaler.transform(song_center.reshape(1, -1))
    distances = cdist(scaled_song_center, scaled_data, 'cosine')
    index = list(np.argsort(distances)[:, :n_songs][0])
    
    rec_songs = spotify_data.iloc[index]
    rec_songs = rec_songs[~rec_songs['name'].isin(song_dict['name'])]
    return rec_songs[metadata_cols].to_dict(orient='records')

#Song recommendation example
recommend_songs([{'name': 'Dynamite', 'year':2020}],  data)

#Song recommendation example
recommend_songs([{'name': 'Smack that', 'year':2006}],  data)

#Song recommendation example
recommend_songs([{'name':'Agar Tum Na Milte', 'year': 1947}],  data, 4)

#Song recommendation example
recommend_songs([{'name': 'Come As You Are', 'year':1991},
                {'name': 'Smells Like Teen Spirit', 'year': 1991},
                {'name': 'Lithium', 'year': 1992},
                {'name': 'All Apologies', 'year': 1993},
                {'name': 'Stay Away', 'year': 1993}],  data)

#Song recommendation example
recommend_songs([{'name': 'Ocean Waves for Sleep', 'year':2010}],  data, 2)
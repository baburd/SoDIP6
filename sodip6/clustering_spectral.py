import numpy as np
import pandas as pd
float_formatter = lambda x: "%.3f" % x
np.set_printoptions(formatter={'float_kind':float_formatter})
from sklearn.cluster import SpectralClustering, KMeans
from matplotlib import pyplot as plt
import scipy.cluster.vq as vq
import networkx as nx
import csv
from tkinter import messagebox
from tkinter import filedialog
import seaborn as sns
sns.set()

file_open = filedialog.askopenfilename(initialdir='D:\PhD-Study\Experimental\SoDIP6', title='Select file', \
                    filetypes=(('GML files', '*.gml'),('CSV files', '*.csv'), ('All files', '*.*')))
if file_open.endswith('.gml'):
    try:
        G = nx.read_gml(file_open)
        if nx.get_edge_attributes(G, name='weight') is None:
            nx.set_edge_attributes(G,10.0,name='weight')
    except FileNotFoundError:
        print('File not found')
elif file_open.endswith('.csv'):
    G = nx.Graph()
    try:
        with open(file_open) as graph_file:
            read_file = csv.DictReader(graph_file)
            for row in read_file:
                G.add_edge(row['node_from'], row['node_to'], weight=float(row['bandwidth']))
    except FileNotFoundError:
        print('File or node error')
else:
    messagebox.showerror('SoDIP6','Could Not Load file')

with open('../dataset/generate_csv.csv', 'w', newline='') as write_csv:
    writer = csv.writer(write_csv)
    writer.writerow(['id', 'Name', 'Latitude', 'Longitude'])
    id = 0
    for node, attrs in list(G.nodes(data=True)):
        writer.writerow([id, str(node), attrs['Latitude'], attrs['Longitude']])
        id += 1
write_csv.close()

#find number of suitable clusters in the graph G
df = pd.read_csv('../dataset/generate_csv.csv')
#df.head(10)
#df.dropna(axis=0,how='any',subset=['latitude','longitude'],inplace=True)
X=df.reindex(['id','Latitude','Longitude'])
#X.head(10)

K_clusters = range(1,10)
kmeans = [KMeans(n_clusters=i) for i in K_clusters]
Y_axis = df[['Latitude']]
X_axis = df[['Longitude']]
score = [kmeans[i].fit(Y_axis).score(Y_axis) for i in range(len(kmeans))]
# Visualize
plt.plot(K_clusters, score)
plt.xlabel('Number of Clusters')
plt.ylabel('Score')
plt.title('Elbow Curve')


fig = plt.figure()
ax1 = fig.add_subplot(111, aspect="equal")
ax1.axis("off")
pos = nx.spring_layout(G)
nx.draw_networkx_nodes(G, pos)
nx.draw_networkx_labels(G, pos)
nx.draw_networkx_edges(G, pos, width=1.0, alpha=0.5)

W = nx.adjacency_matrix(G)
print(W.todense())

sc = SpectralClustering(3, affinity='precomputed', n_init=100)
sc.fit(W)
print('spectral clustering')
print(sc.labels_)

print('just for better-visualization: invert clusters (permutation)')
print(np.abs(sc.labels_ - 1))

# degree matrix
D = np.diag(np.sum(np.array(W.todense()), axis=1))
print('printing degree matrix:')
#print(D)

# laplacian matrix
L = D - W
print('printing laplacian matrix:')
#print(L)

e, v = np.linalg.eig(L)
f = v[:,1]
labels = np.ravel(np.sign(f))
coord = nx.spring_layout(G, iterations=1000)
fig = plt.figure()
ax2 = fig.add_subplot(221, aspect="equal")
ax2.title.set_text('Two clusters')
ax2.axis("off")
nx.draw_networkx_edges(G, coord)
nx.draw_networkx_nodes(G, coord,node_size=45,node_color=labels)
#nx.draw_networkx_labels(G, pos)

k=3
means, labels = vq.kmeans2(v[:,1:k], k)
ax3 = fig.add_subplot(222, aspect="equal")
ax3.title.set_text('Three Clusters')
ax3.axis("off")
nx.draw_networkx_edges(G, coord)
nx.draw_networkx_nodes(G, coord,node_size=45,node_color=labels)
#nx.draw_networkx_labels(G, pos)

# eigenvalues
print('printing eigenvalues:')
print(e)
# eigenvectors
print('printing eigenvectors:')
#print(v)

#fig = plt.figure()
ax4 = plt.subplot(223)
#ax2.axis("off")
plt.plot(e)
ax4.title.set_text('eigenvalues')

i = np.where(e < 10e-6)[0]
ax5 = plt.subplot(224)
plt.plot(v[:, i[0]])
fig.tight_layout()
plt.show()

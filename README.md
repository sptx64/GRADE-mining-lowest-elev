# GRADE mining - lowest elev
A simple notebook to batch process multiple Surpac .str DEM to compute the lowest escavated points of your site from all your .str, .shp and .dxf.

Le suivi topographique est important dans le contexte minier pour différencier les zones remblayées du terrain naturel. Pour générer une topographie défruitée, c'est à dire une topographie montrant le point le plus bas historiquement atteint, de longues manipulations topographie par topographie sont nécessaires. Aujourd'hui il existe des solutions directement dans les logiciels Surpac, Leapfrog et QGIS pour calculer la topographie la plus basse par paire de topographie, mais pas à la volée.

Ce notebook permet de compiler une topo defruitée à partir de x fichiers .str et d'un contour .gpkg. Il s'agit d'une application open source qui s'adapte au format des fichiers .str (Attention : au format texte, non binaire) de Surpac. Mettre toutes les topos .str dans le dossier "input" et la limite désirée de l'output au format bd_topo_def.gpkg dans le dossier "input boundary". Limites rencontrées : sur certaines grandes zones avec une résolution de 1m, le fichier peut générer de +100 000 000 points de controle ce qui peut éventuellement créer un crash du noyau. Limitez intelligemment la zone d'intérêt et donc le nombre de point grâce au fichier de boundary.

Vous devrez avoir au préalable installé les librairies jupyter, geopandas, pandas, numpy et scipy dans votre environnement avec les commandes :

- pip install numpy
- pip install pandas
- pip install jupyter
- pip install scipy
- pip install geopandas

Puis lancer la commande "jupyter notebook" et ouvrir le notebook .ipynb
Script 100% python.

Trouble shooting :

- Attention à l'arborescence et au nom du fichier boundary.
- En cas d'erreur de byte non reconnu, recherchez dans la topo concernée s'il y a des caractères spéciaux é, è, à, ù, ... qui peuvent dans certains cas etre problématiques.
- Vérifier que les str soient au format str.


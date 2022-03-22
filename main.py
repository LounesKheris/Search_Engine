#!/usr/bin/python3.6 
import searchEngine as se
# debut programme

if (not se.os.path.isfile('/home/lounes98kheris/Desktop/frwiki.xml')):
	print('calcule du corpus...')
	se.getCorpus()
if (not se.os.path.isfile('graphe.npy')):
	print('calcule dict des ids et title...')
	dict_id_title= se.getIdTitleDict()
	print('calcule dict des titles et ids...')
	dict_title_id=se.getTitleIdDict(dict_id_title)
	print('construire le graphe...')
	graphe=se.getLienInterne(dict_title_id)
	print('sauvgarde le graphe,dict titre,dict id...')
	se.saveDicts(graphe,dict_id_title,dict_title_id)
print('chargement du graphe...')
graphe,dict_id_title,dict_title_id=se.loadGraphe()
print('calcule de C.L.I...')
C,L,I=se.contruire_CLI(graphe)
#print(I)


print('calcule pageRank...')
PageRank=se.PageRank(C,L,I,se.V,se.espsilon)

del graphe
del C
del L
del I
del se.V

#if not os.path.isfile('dict_of_words.npy'):
if not se.os.path.isfile('dict_of_words.npy'):
	print('contruire le dictionnaire mot page')
	dict_mot_page_freq=se.getDictWords(se.mot_plus_frequent)
print('chargement du dictionnaire mot page...')
dict_mot_page_freq=se.np.load('dict_of_words.npy',allow_pickle='TRUE').item()
dict_page_mot=se.get_page_mot(dict_mot_page_freq)
if not se.os.path.isfile('idf_du_mot.npy'):
	print('calcule des idf des mots...')
	se.idf_du_mot(dict_mot_page_freq)
print('chargement des idf des mots...')
dict_idf=se.np.load('idf_du_mot.npy',allow_pickle='TRUE').item()
if not se.os.path.isfile('vecteur_des_pages.npy'):
	print('calcule des vecteurs des pages ...')
	vecteur_des_pages=se.calcule_vecteur_page()
print('chargement des vecteur des pages ...')
vecteur_des_pages= se.np.load('vecteur_des_pages.npy',allow_pickle='TRUE').item()
print('initialisation terminer ')
Port=9000
server= se.HTTPServer(('',Port),se.requestHandler)
print('lancement du serveur sur '+str(Port))
server.serve_forever()
#!/usr/bin/python3.6 

from typing import cast
import xml.etree.ElementTree as etree
import re
from cltk.tokenize.word import WordTokenizer#
from cltk.corpus.utils.importer import CorpusImporter#
from nltk.corpus import stopwords
import nltk
from nltk.tokenize import word_tokenize
import spacy
from spacy import displacy
import fr_core_news_md
from nltk.stem import WordNetLemmatizer#
import os.path
import datetime
import numpy as np
import time
import unicodedata 
import math
from http.server import HTTPServer,BaseHTTPRequestHandler
import cgi
from spacy import displacy
nlp = spacy.load("fr_core_news_sm")

theme=['champion','penalty','ailier','adverse','arbitrage','équipe','sport','championnat','match','club','maillot','avant-centre','mi-temps','spectateur','footix','supporter','derby','division','défenseur','jouer','offensif','tournoi','mondial','foot','football','ballon','FIFA','stade','Calcio','coupe','ligue','attaquant','fédération','joueur','footballeur','entraîneur','but','buteur','sélectionneur','vainqueur','olympique','trophée','arbitre','prolongation','tactique','gardien','finale','sélectionné','éliminatoire','tacle']

lien_externe_multi= re.compile(r"\{\{(.+?)\}\}",re.DOTALL )#on supprime les {{}} sur plusieurs lignes (probleme si on fait au mm temps line et multiline)
lien_externe_line= re.compile(r"\{\{(.*?)\}\}",re.MULTILINE )#on supprimer les {{}} sur une ligne 

lien_interne=re.compile(r"\[\[([A-Za-z0-9_éè()â| ]+)\]\]", flags=re.DOTALL)

#------variable globale------
#dict_mot_page={} #dictionnaire qui contient {mot:(page_id,tf(mot))}
dict_page_mot={}#dictionaaire qui contient {page_id :[list de mots]} 
dict_id_title={}#dictionnaire contient {id_page : title_de_page}
dict_title_id={}#dictionnaire qui contient {title_de_page:id_page}
list_mots_vide=[]#la liste des mots vides de la langue francaise
dict_mot_page_freq={}#contient {mot:(page_id,tf(mot))}
mot_plus_frequent={}#dictionnaire des mots les plus utilises
dict_idf={}#contiwnt les idf des mots besoin dans la requtes
graphe={}#graphe du nos pages pour faire le cli
vecteur_des_pages={}#contient les vecteur des pages precalcule 
vecteur_de_requete={}
nombre_de_page=200000 #nombre de page total
espsilon=0.15 #epsilon de page rank
alpha=pow(10,-6) #alpha pour efectuer au score final
beta=alpha#beta pour efectuer au score final
PageRank=[]
C=[]#coefficiant non nul
L=[]# L[i] indice du debut de la ieme ligne dans C /l'idee: d'ajouter le len du tableau de change page 
I=[]# I cest la colonne de C[i]/ numuro de page de la liste
V=[1/nombre_de_page]*nombre_de_page #tableau pour calculer la pagerank
#nlp = fr_core_news_md.load()#charger la bibliotheque francaise
caractere_speciaux =[',',':','*',';','','+','=','.',',','',':']
#-----------theme----------------


def strip_tag_name(t):
    t = t
    idx = k = t.rfind("}")
    if idx != -1:
        t = t[idx + 1:]
    return t

def nombre_doccurence(page,title,theme):
    i = 0
    for x in theme:
        i=i+page.count(x)
        i = i+title.count(x)
    return i
    
def getSizeFile(file):
	size = os.path.getsize(file)
	print('Size of file is', size, 'bytes')
	return size

def mot_videList():#retourne une liste de mot_vide quon doit supprimer 
	mot_vide=stopwords.words('french')
	mot_vide+=["'",",","}","{","[","]","|","<",">",".","*","#","/",'plus','align','comme','tout','apres','the','autre','depuis','dont','aussi','celui','sans','tres','sous','etre','alors','ainsi','nbsp']
	#print(mot_vide)
	return mot_vide


#les pathes sont former de {}tag donc on veut laisser que le tag

def supprimer_lien_externe(text):
	#supprimer les liens exerne  entre {{}}
	m=lien_externe_line.finditer(text)
	if (m!=None):
		for x in m:
			text=text.replace(x.group(0),'')
	z=lien_externe_multi.finditer(text)
	if (z!=None):
		for x in z:
			text=text.replace(x.group(0),'')

	return text

#pour supprimer les [] et garder les liens interne [[]]
def supp1coll(text): 
	allpar=re.compile(r'\[.*?\]',re.DOTALL )
	m= allpar.finditer(text)
	if (m!=None):
		for x in m:
			if x.group(0)[0:2]!="[[":
				#print(x.group(0))
				text=text.replace(x.group(0),'')
	return text


def nettoyage(text):
	text = supprimer_lien_externe(text)		
	text=re.sub(r'\{(.+?)\}','',text,flags=re.DOTALL)	
	text=re.sub(r'(https|http)?:\/\/(\w|\.|\/|\?|\=|\&|\%)*\b', '', text, flags=re.MULTILINE) #supprimer les lients http et https externes
	text=text=re.sub(r"(\w|\.|\-|\/|\?|\=|\&|\%)*.(com|net|dz|fr|org|gov|edu|int|arpa|blog|au|aspx|eu|de|asp|be|ca|COM|de)/?\b",'',text,flags=re.DOTALL)
	text=re.sub(r"(\w|\.|\-|\/|\?|\=|\&|\%)*.(jpg|gif|png|bmp|JPEG|JPG|svg)",'',text,flags=re.DOTALL)
	text=re.sub(r'<.*?>','',text, flags=re.MULTILINE)#supprimer les balise inutile
	text=re.sub(r'\[\[(Image:|:Catégorie:|Fichier:|Catégorie:).*?]]','',text, flags=re.MULTILINE)#supprimer les [[]] qui ne sont pas des liens
	text=supp1coll(text)
	text=re.sub(r'(\=\=\=?).+?(\=\=\=?)','',text,flags=re.MULTILINE) #supprimer les lines qui contient === mots ===
	text=re.sub(r'\{\|.*?\s\|\}','',text,flags=re.DOTALL) #supprimer les {||} contient du code css 
	text=re.sub(r'<','',text,flags=re.DOTALL) #supprimer les {||} contient du code css 
	text=re.sub(r'>','',text,flags=re.DOTALL) #supprimer les {||} contient du code css 
	text=re.sub(r'&','',text,flags=re.DOTALL) #supprimer les {||} contient du code css 
	text=re.sub(r'\}\}','',text,flags=re.DOTALL)
	text=re.sub(r'(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:\'".,<>?«»“”‘’]))','',text,flags=re.DOTALL)
	text=re.sub(r"[\n\t]*", "", text)
	return text


#recupperer le corpus des mots choisis
def getCorpus(): 
	totalCount = 0
	idp=-1 #id de chaque page
	title = ''#titre de page
	page=0#nombre de page
	corps=None#partie text du fichier
	nbocc=15#nombre d#
	nboccTrouver=0
	dictPage=[]
	i=1
	openf=False
	df=0
	file1='wikiSelected1.xml'
	file2='wikiSelected2.xml'
	file3='wikiSelected3.xml'
	file4='wikiSelected4.xml'


	while(i<5):
		print("[nouveau] Fichier")
		df=open('wikiSelected'+str(i)+'.xml','w')
		df.write('<?xml version="1.0" encoding="utf-8"?> \n')
		df.close()
		i+=1
	i=0
	for event, elem in etree.iterparse('frwiki-latest-pages-articles.xml', events=('start', 'end')):
		tname = strip_tag_name(elem.tag)
		#print(tname)

		if event == 'start':
			#pour chaque nouvelle page initialiser les variablle
			if tname == 'page':
				title = ''
				idp = -1
				inrevision = False #pour eviter le probleme de recuperer id + dautre info
			elif tname == 'revision':
				inrevision = True
			elif tname == 'title': #recuuperer le titre de la page 
				title = elem.text
				
				#print(title)
			elif tname=='text':
				
				corps=elem.text
				#print(corps)
		else:
			if tname == 'page':#pour compter nombre de page du fichier 
				totalCount += 1
			if tname=='text': # a la fin de la balise <text> quon peut recuperer le text sinon none
				#recuperer le corps de la page
				if(corps==None):
					corps=elem.text
					try:
						text=corps+' '+title
					except TypeError:
						corps=''
						title = ''
						continue
				
				if (title!=None and corps!=None):
					if ('Wikipédia' in title or 'Projet:' in title or 'Modèle:' in title or 'Portail:' in title):
						#print('********************************* '+title)
						corps=''
						title = ''
						continue
					nboccTrouver= nombre_doccurence(corps,title,theme)
					if(nboccTrouver>=nbocc):
						text2=nettoyage(text)
						#print(title)
						#print(title)
						title=re.sub(r'&','',title,flags=re.DOTALL) #supprimer les {||} contient du code css 
						if (str(page)!=None and str(page)!='None' and title!=None and title!='None' and title!='' and title not in dictPage  and page<200000 ):
							#print(str(page),title)
							dictPage.append(title)
							if (int(page/50000)==i and openf==False ):#chaque fichier contient 50k page
								x='wikiSelected'+str(i+1)+'.xml'

								df=open(x,'a')
								openf=True

							df.write('	<page>\n')
							df.write('		<id>'+str(page)+'</id>\n')
							df.write('		<title>'+title+'</title>\n')
							df.write('		<text>' +text2 +'</text>\n')
							df.write('	</page>\n')
							page+=1
							print(page)
							print(i)
							if (page==50000 or page==100000 or page==150000 or page ==200000):
								print("[Fermeture] du fichier x")
								df.write('</mediawiki>\n')
								df.close()
								i+=1
								openf=False
								if page ==200000:
									break
						nboccTrouver=0
										#print(corps)
				
		elem.clear()
	return page

def getIdTitleDict():
	d={}
	i=1
	while(i<5):
		filename='wikiSelected'+str(i)+'.xml'
		print('debut de calcule fichier: '+str(i))
		i+=1
		tree=etree.parse(filename)
		root=tree.getroot()
		for page in root.findall("./page"):
			d[int(page.find('id').text)]=page.find('title').text
		tree=None
		root=None
	return d
	
def getTitleIdDict(diction):
	title_id={}
	title_id={v: k for k, v in diction.items()}
	return title_id

def mot_plus_frequent():
	list_stop=mot_videList()
	tokenizer = nltk.RegexpTokenizer(r"\w+")
	print('calculer le mot_plus_frequent... ')
	idp=-1
	corps=''
	title=''
	dict_of_words={}#dictionnaire globale des mots -> (page,tf)
	i=1
	while(i<5):
		filename='wikiSelected'+str(i)+'.xml'
		print('debut de fichier: '+str(i))
		i+=1
		tree=etree.parse(filename)
		root=tree.getroot()
		for page in root.findall("./page"):
			new_list=[]
			new_list2=[]
			newText=''
			newtext=''
			idp=int(page.find('id').text)
			print("--------id:"+str(idp))
			corps=page.find('text').text
			title=page.find('title').text
			text=corps+" "+title
			new_list= tokenizer.tokenize(str(text))
			for x in new_list:
				if x.lower() not in list_stop and  (x.isdigit()!=True) and (len(x)>2):
					new_list2.append(x.lower())
			lis2=' '.join(x for x in new_list2)
			doc2=nlp(lis2)
			new_list=[]
			for token in doc2:
				new_list.append(token.lemma_)
			new_list2=[]
			for x in new_list:
				if x.lower() not in list_stop and  (x.isdigit()!=True) and (len(x)>2):
					new_list2.append(x.lower())

			newText = ' '.join(x for x in new_list2)
			newtext= ''.join((c for c in unicodedata.normalize('NFD', newText) if unicodedata.category(c) != 'Mn')) #enlever les accents
			listn=newtext.split()
			for x in listn:
				if x in dict_of_words:
					dict_of_words[x]=dict_of_words[x]+1
				else:
					dict_of_words[x]=1
			#print(dic0tionnaire)
			if (len(dict_of_words)>=20000):
				new_dict=sorted(dict_of_words.items(), key=lambda x: x[1], reverse=True)
				tree=None
				root=None
				itere=0
				f=open('most_word_used','w')
				for mot in new_dict:
					if(itere<10000):
						f.write(mot[0])
						f.write(';')
					itere+=1
					if (itere>10000):
						f.close()
						print('fichier des mots les plus utiliser est creer')
						return
				
def getLienInterne(dict_title_id):
	print('calcule le graphe des pages.....')
	i=1
	idp=-1
	listeOfPages=[]
	ListofId=[]
	graphe={}
	while(i<5):
		filename='wikiSelected'+str(i)+'.xml'
		i+=1
		tree=etree.parse(filename)
		root=tree.getroot()
		for page in root.findall("./page"):
			idp=int(page.find('id').text)
			corps=page.find('text').text
			listeOfPages=[]
			m=lien_interne.finditer(corps)
			if(m!=None):
				for x in m:
					l=str(x.group(0)).split('|')
					link=l[0].replace('[','')
					link=link.replace(']','')
					if (link not in listeOfPages):#pour ne pas compter la meme page 2 fois 
						listeOfPages.append(link)
				l=[]
				link=''
				listeOfPages.sort()
				for x in listeOfPages:
					if x in dict_title_id:
						ListofId.append(dict_title_id[x])
			graphe[idp]=ListofId
			ListofId=[]
		tree=None
		root=None
	return graphe#pour calculer le pagerank

def saveDicts(graphe,dict_id_title,dict_title_id):
	np.save('graphe.npy', graphe)
	np.save('dict_id_title.npy', dict_id_title)
	np.save('dict_title_id.npy', dict_title_id)

def loadGraphe():
	graphe = np.load('graphe.npy',allow_pickle='TRUE').item()
	dict_id_title=np.load('dict_id_title.npy',allow_pickle='TRUE').item()
	dict_title_id=np.load('dict_title_id.npy',allow_pickle='TRUE').item()
	return graphe,dict_id_title,dict_title_id

def contruire_CLI(graphe):
	C=[]
	L=[]
	I=[]
	ligne=0
	colonne=-1
	for k in graphe:
		list_de_page=graphe[k]
		#print(k, list_de_page)
		for pageLie in list_de_page:
			#print("C", 1/len(list_de_page))
			C.append(1/len(list_de_page))
			#print("I", pageLie)
			#print(pageLie)
			I.append(pageLie)
		ligne=ligne+len(list_de_page)
		L.append(ligne)
		#print("L---------------------------------------------------------------", ligne)
		list_de_page=[]
	
	return C,L,I

def listTodict(diction,liste,idp):#ajouter au dictionnaire globale les mots avec leurs id de page et leurs occurences , le return de la fonction liste_depuis_text 
	#{mot:(id,tf(mot =1+log10(occ)))}
	
	DdeList = {x:liste.count(x) for x in liste}
	for item in liste:
		if item not in diction:
			diction[item]=[(idp,1+math.log10(DdeList[item]))]
		else:
			l= [x[0] for x in  diction[item]]
			if idp not in l:#verifier quand na pas deja ajouter le mots dans la page eviter les doublants 
				diction[item].append((idp,1+math.log10(DdeList[item])))
	liste=[]
	return diction

def liste_depuis_text(text,title,list_mot_vide,dict_mot_plus_freq):
	tokenizer = nltk.RegexpTokenizer(r"\w+")
	mots_du_text = tokenizer.tokenize(text+" "+title)
	new_mots_du_text = []

	for x in mots_du_text:
		if x.lower() not in list_mot_vide:
			if x.isdigit()!=True:
				#if x in dict_mot_plus_freq:
				new_mots_du_text.append(x.lower())
	new_text = ' '.join(x for x in new_mots_du_text)
	new_mots_du_text=[]
	#print(new_text)
	doc2 = nlp(new_text)
	for token in doc2:
		new_mots_du_text.append(token.lemma_)#trouver la racine du mot 

	new_mots_du_text2=[]
	for x in mots_du_text:
		if x.lower() not in list_mot_vide:
			new_mots_du_text2.append(x.lower())
	newText = ' '.join(x for x in new_mots_du_text2)
	new_text= ''.join((c for c in unicodedata.normalize('NFD', newText) if unicodedata.category(c) != 'Mn')) #enlever les accents
    
	return new_text.split()
	

def getDictWords(dict_mot_plus_freq):
	print('calculer le dictionnaire des mots... ')
	list_mots_vide=mot_videList()
	idp=-1
	corps=''
	title=''
	dict_of_words={}#dictionnaire globale des mots -> (page,occurrence)
	
	i=1
	while(i<5):
		filename='wikiSelected'+str(i)+'.xml'
		print('debut de fichier: '+str(i))
		i+=1
		tree=etree.parse(filename)
		root=tree.getroot()
		for page in root.findall("./page"):
			#if (len(dict_of_words)>=30000):
			#	break
			idp=int(page.find('id').text)
			print(str(idp))
			corps=page.find('text').text
			title=page.find('title').text
			#print(title)
			dict_of_words=(listTodict(dict_of_words,liste_depuis_text(corps,title,list_mots_vide,dict_mot_plus_freq),idp))
			#print("length  ------>    ",len(dict_of_words))
			#print(dict_of_words)
		if (len(dict_of_words)>=30000):
			if (idp >= 5000):
				#print(dict_of_words)
				np.save('dict_of_words', dict_of_words)
				return dict_of_words
				tree=None
				root=None
	

def PageRank(C,L,I,V,espsilon): #calculer le page rank des page
	k=50 # nombre d'iteration
	n=200000 #taille du corpus
	
	for it in range(0,k):
		P=[0.0]*n
		s=0
		#print('je suis dans iteAVERr :'+str(it))
		for i in range(0,n-1):
			print(L[i], L[i+1])
			if (L[i]==L[i+1]):
				s+=V[i]
			for j in range(L[i],L[i+1]):
				P[I[j]]+=C[j]*V[i]
		s=s/n
		#print(s)
		for i in range(0,n):
			P[i]=(1-espsilon)*(P[i]+s)+(espsilon/n)
		for i in range (0,n):
			V[i]=P[i]
		V=P
	return P
def get_page_mot(dict_mot_page_freq):
	dict_page_mot={}
	for mot in dict_mot_page_freq:
		for idp,tf in dict_mot_page_freq[mot]:
			if idp in dict_page_mot:
				dict_page_mot[idp].append((mot,tf))
			else:
				dict_page_mot[idp]=[(mot,tf)]
	return dict_page_mot
def idf_du_mot(dict_mot_page_freq):#calculer le idf des mots de notre dictionnaire
	#nombre_de_page : cest le nombre de page total
	dict_idf={}
	for mot in dict_mot_page_freq:
		# idf = math.log10(nombre_de_page/len(dict_mot_page_freq[mot]))
		#	if id == 0 : 
		#		break
		#	else :
		dict_idf[mot] = math.log10(nombre_de_page/len(dict_mot_page_freq[mot]))
	np.save('idf_du_mot', dict_idf)
	return dict_idf

def calcule_vecteur_page():#calculer le vecteur normaliser des page et le stocker
	norme=[0]*nombre_de_page
	vecteur_des_pages={}
	for mot in dict_mot_page_freq:
		#pour chaque mot on recupere une liste de uple
		list_de_uple = dict_mot_page_freq[mot] # list_de_uple = {mot : (id_page, tf(mot))}
		for uple in list_de_uple:
			idpage=uple[0] # mot 
			tf_mot=uple[1] # tf(mot)
			norme[idpage]+= pow(tf_mot,2) # tf*2
	for case in norme:
		case=math.sqrt(case)
	for mot in dict_mot_page_freq: #dict_mot_page_freq = {mot : (id_page, tf(mot))}
		list_de_uple=dict_mot_page_freq[mot] # list_de_uple = {mot : (id_page, tf(mot))}
		for uple in list_de_uple:
			idpage=uple[0]   # mot
			tf_mot=uple[1]   # {mot : tf(mot)
			if (idpage in vecteur_des_pages):
				vecteur_des_pages[idpage].append([(mot,tf_mot/norme[idpage])])#sauvgarder chaque page les mots quelle contient et son tf
			else:
				vecteur_des_pages[idpage]=[(mot,tf_mot/norme[idpage])]#sauvgarder chaque page les mots quelle contient et son tf

	np.save('vecteur_des_pages', vecteur_des_pages)
	return vecteur_des_pages


def calculer_vecteur_requete(list_req):#calculer le vecteur normaliser de la requete a partir des idf des mots dans le dictionnaire 
	#dict_idf le return de la fonction idf_du_mot()
	norme_requete=0
	vect_requete={}
	for mot in list_req:
		if mot in dict_idf:
			#print(mot,dict_idf[mot])
			vect_requete [mot]=dict_idf[mot] #attribuer un idf a chaque mot de requete 
			norme_requete+= pow(dict_idf[mot],2) #on adition pour avoir la norme 
		else:
			vect_requete [mot]=0
	norme_requete=math.sqrt(norme_requete)
	if norme_requete!=0:
		for mot in vect_requete:
			vect_requete[mot]=vect_requete[mot]/norme_requete #on divise le idf de chaque mot de requete sur la norme 
	return vect_requete

def get_pages_mots(requete):#on lui donnant une liste de mots de la requte elle retourne une liste de listes de page de chaque mot on la donne en argument a page_commun
	listrenvoyer=[]
	for mot in requete:
		list_page=[]
		if mot in dict_mot_page_freq:
			for idp,tf in dict_mot_page_freq[mot]:
				list_page.append(idp)
			listrenvoyer.append(list_page)
	#print(listrenvoyer)
	return listrenvoyer

#list_m retourner par la fonction get_pages_mots()
def page_commun(list_m):#pour trouver les pages communes entre les mots , o lui donne une liste de liste
	s=set()
	if (list_m!=[]):
		s=set(list_m[0])
		for i in range(1,len(list_m)):
			s=s & set(list_m[i])
	return s



def calcule_du_score(list_page_en_communs,vecteur_de_requete):
	score_requete_page={}
	score=0
	res=[]
	#print('dans calcule_du_score')
	print(list_page_en_communs)
	for id_page in list_page_en_communs:
		score=0
		#print(id_page)
		for mot,tf_norm in dict_page_mot[id_page]:
			if mot in vecteur_de_requete:
				score+= vecteur_de_requete[mot]*tf_norm
		score_requete_page[id_page]= (alpha * score) + (beta * PageRank[id_page])
	sortedL=sorted(score_requete_page.items(), key=lambda x: x[1], reverse=True)
	for idpage,score in sortedL:
		res.append(dict_id_title[idpage])
	return res


requests =[]
resulat=[]
temps_execution=0

class requestHandler(BaseHTTPRequestHandler):
	def do_GET(self):
		if self.path.endswith('/'):
			self.send_response(200)
			self.send_header('content-type','text/html')
			self.end_headers()
			output= '<html>'
			output+='<body>'
			output+='<script src="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js" integrity="sha384-MrcW6ZMFYlzcLA8Nl+NtUVF0sA7MsXsP1UyJoMp4YLEuNSfAP+JcXn/tWtIaxVXM" crossorigin="anonymous"></script>'
			output+='<h1>search engine</h1>'
			output+='<form method="POST" enctype="multipart/form-data" action="/resultat">'
			output+='<input name="requete" type="text" placeholder="mettez votre requete">'
			output+='<input type="submit" value="search">'
			output+='</form>'
			output+='</body></html>'
			self.wfile.write(output.encode())
		if self.path.endswith('/resultat'):
			self.send_response(200)
			self.send_header('content-type','text/html')
			self.end_headers()
			output= ''
			output+='<html>'
			output+="""
				  <head>
					<!-- Required meta tags -->
					<meta charset="utf-8">
					<meta name="viewport" content="width=device-width, initial-scale=1">

					<!-- Bootstrap CSS -->
					<link href="https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-EVSTQN3/azprG1Anm3QDgpJLIm9Nao0Yz1ztcQTwFspd3yD65VohhpuuCOmLASjC" crossorigin="anonymous">

    				<title>My Search Engine!</title>
  				</head>
				"""

			output+='<body>'
			output+= '<h1>resulat de votre recherche </h1>'
			output+= '<h4>temps de reponse: '+ str(temps_execution)+'</h4>'
			global resulat

			new_list=resulat
			
			resulat=[]
			if new_list != []:
				output+=' <div class="panel panel-default">'
				for mot in new_list:
					print(mot)
					output+='<div class="panel-heading" class="panel-body"><a href="'+'https://fr.wikipedia.org/wiki/'+mot.replace(' ','_')+'"">'+str(mot)+'</a></div>'
					output+='</br>'
				output+='</div>'

			else:
				output+='<h4> desole pas de resultat pour votre recherche</h4>'
				output+='</br>'
			output+='</body></html>'
			self.wfile.write(output.encode())
			
	def do_POST(self):
		if self.path.endswith('/resultat'):
			ctype,pdict = cgi.parse_header(self.headers.get('content-type'))
			pdict['boundary']=bytes(pdict['boundary'],'utf-8')
			content_len=int(self.headers.get('Content-length'))
			pdict['CONTENT-LENGTH']=content_len
			if ctype=='multipart/form-data':
				fields=cgi.parse_multipart(self.rfile,pdict)
				list_requete=fields.get("requete")
				print(list_requete)
				requete=''.join(x for x in list_requete).lower().split(' ')
				print(requete)
				global resulat
				global temps_execution
				debut = datetime.datetime.now()
				vecteur_de_requete= calculer_vecteur_requete (requete)
				res = calcule_du_score(page_commun(get_pages_mots(requete)),vecteur_de_requete)
				fin=datetime.datetime.now()
				temps_execution = fin-debut
				print(temps_execution)
				resulat=res
			self.send_response(301)
			self.send_header('content-type','text/html')
			self.send_header('Location','/resultat')
			self.end_headers()




if (not os.path.isfile('/home/lounes98kheris/Desktop/frwiki.xml')):
	print('calcule du corpus...')
	getCorpus()
if (not os.path.isfile('graphe.npy')):
	print('calcule dict des ids et title...')
	dict_id_title=getIdTitleDict()
	print('calcule dict des titles et ids...')
	dict_title_id=getTitleIdDict(dict_id_title)
	print('construire le graphe...')
	graphe=getLienInterne(dict_title_id)
	print('sauvgarde le graphe,dict titre,dict id...')
	saveDicts(graphe,dict_id_title,dict_title_id)
print('chargement du graphe...')
graphe,dict_id_title,dict_title_id=loadGraphe()
print('calcule de C.L.I...')
C,L,I=contruire_CLI(graphe)
#print(I)


print('calcule pageRank...')
PageRank=PageRank(C,L,I,V,espsilon)

del graphe
del C
del L
del I
del V

#if not os.path.isfile('dict_of_words.npy'):
if not os.path.isfile('dict_of_words.npy'):
	print('contruire le dictionnaire mot page')
	dict_mot_page_freq=getDictWords(mot_plus_frequent)
print('chargement du dictionnaire mot page...')
dict_mot_page_freq=np.load('dict_of_words.npy',allow_pickle='TRUE').item()
dict_page_mot=get_page_mot(dict_mot_page_freq)
if not os.path.isfile('idf_du_mot.npy'):
	print('calcule des idf des mots...')
	idf_du_mot(dict_mot_page_freq)
print('chargement des idf des mots...')
dict_idf=np.load('idf_du_mot.npy',allow_pickle='TRUE').item()
if not os.path.isfile('vecteur_des_pages.npy'):
	print('calcule des vecteurs des pages ...')
	vecteur_des_pages=calcule_vecteur_page()
print('chargement des vecteur des pages ...')
vecteur_des_pages= np.load('vecteur_des_pages.npy',allow_pickle='TRUE').item()
print('initialisation terminer ')
Port=9000
server= HTTPServer(('',Port),requestHandler)
print('lancement du serveur sur '+str(Port))
server.serve_forever()

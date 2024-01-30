import time
import threading 
from multiprocessing import Value,Process,Lock,Manager,Array
import queue
import random
import socket
import signal
import os

class Carte :
    def __init__(self, valeur, couleur):
        self.valeur = valeur
        self.couleur = couleur

    def __str__(self):
        return f"{self.valeur} {self.couleur}"
    
    def __repr__(self):
        return f"{self.valeur} {self.couleur}"

def mise_en_place(nb_joueurs):

    couleurs_disponibles=["red","green","blue","yellow","white"]
    couleurs=[]
    pile=[]
    liste_joueur=[]

    for i in range(0,nb_joueurs):
        couleurs.append(couleurs_disponibles[i])
        pile.append(0)
        liste_joueur.append(i+1)
    
    deck=[]
    for couleur in couleurs : 
        i=1
        for i in range (10) :
            if i<3 :
                carte=Carte(1,couleur)
            elif i<5 :
                carte=Carte(2,couleur)
            elif i<7 :
                carte=Carte(3,couleur)
            elif i<9 :
                carte=Carte(4,couleur)
            else :
                carte=Carte(5,couleur)
            deck.append(carte)
            i+=1

    random.shuffle(deck)
    
    hands = {}

    for i in range(nb_joueurs):
        hands[i+1] = []
        for j in range (5):
            hands[i+1].append(piocher(deck))
    
    return deck,hands,couleurs,pile,liste_joueur

def piocher(deck):
    carte_pioche=deck.pop()
    return carte_pioche

def handle_client(client_socket,num_joueur):
    
    h=dict(hands)

    with client_socket:
        while True : 

            data = client_socket.recv(1024).decode()

            if data == "-information_token":
                information_token.value-=1
            elif data[:-2] == "-fuse_token":
                a_enlever=data[-2:]
                nouvelle_carte=piocher(deck)
                h[num_joueur][int(a_enlever)-1]=nouvelle_carte
                hands.update(h)
                fuse_token.value-=1
            else:
                a_enlever=data[2]
                nouvelle_carte=piocher(deck)
                h[num_joueur][int(a_enlever)-1]=nouvelle_carte
                hands.update(h)
                pile[int(data[0])]+=1
                if data[4]==5:
                    information_token.value+=1
            mutex_handle.release()

        

def game() : 

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(server_address)
    server_socket.listen(nb_joueurs)
    socket_processes=[]
    client_sockets=[]

    for i in range (nb_joueurs) :
        client_socket, addr = server_socket.accept()

        # Créé un child pour chaque client
        socket_process = Process(target=handle_client, args=(client_socket,i+1))
        socket_process.start()

        socket_processes.append(socket_process)
        client_sockets.append(client_socket)

        
    Fin_de_jeu=False
    Victoire=False
    player_playing = 1
    


    while not Fin_de_jeu:
        
        if(player_playing == nb_joueurs+1):
            player_playing=1

        mutex = mutexes[player_playing - 1]

        afficherjeu(nb_joueurs,couleurs,pile,information_token,fuse_token,deck,hands,player_playing)

        mutex.release() 

        if (fuse_token.value == 0):
            Fin_de_jeu=True

        test_victoire_pile=0
        for test_pile in range(0,len(pile)):
            if(pile[test_pile]==5):
                test_victoire_pile+=1

        if (test_victoire_pile == len(pile)):
            Fin_de_jeu=True
            Victoire=True

        mutex_handle.acquire()

        player_playing+=1

    if Victoire==False:
        print("T'as perdu hahahah sale merde")        
    if Victoire==True:
        print("bien joué bg")

    kill_sockets(socket_processes,client_sockets)
    os.kill(os.getppid(), signal.SIGUSR1)

def afficherjeu(nb_joueurs,couleurs,pile,information_token,fuse_token,deck,hands,joueur):
    print("\033c")
    print(f"                                            Indice:{information_token.value},    Fuse:{fuse_token.value}       ")
    print("Piles:   ")
    for color in range(0,nb_joueurs):
        print(couleurs[color], end=' ')
    
    print()
    print()
    print("Valeurs: ")
    for value in range(0,nb_joueurs):
        print(pile[value], end='     ')
    print()
    print(f"                                            Cartes restantes: {len(deck)}\n")
    print(f"C'est au joueur {joueur} de jouer !\n")

    for nom,cartes in hands.items():
        if(nom!=joueur):
            print(f"Main du joueur {nom}: {cartes}")
    print("----------------------------------------------------------------")

def player(n, mutex):

    player_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    connexion=False

    while not connexion: 
        try : 
            player_socket.connect(server_address)
            connexion=True
        except : 
            time.sleep(1)

    while True : 
        mutex.acquire()

        if not message_queue.empty ():
            for m in range (0,nb_joueurs):
                indice_personnel=message_queue.get()
                if indice_personnel[0]==n:
                    print("Voici les indices de votre main: ",end="")
                    for p in range(1,6):
                        print(f"{indice_personnel[p]}, ",end="")
                    message_queue.put(indice_personnel)   
                    break
                message_queue.put(indice_personnel)
        choix = None
        print()
        while choix not in [1, 2]:
            try:
                choix = int(input("Joueur {}, veux-tu jouer une carte (1) ou donner une information (2) ?".format(n)))
            except ValueError:
                print("Veuillez entrer un chiffre valide (1 ou 2).")
        
        if choix==2 and information_token.value==0:
            print("Vous n'avez plus d'information token.")
            
            test,carte_choisie=play(n)
            if not message_queue.empty():
                for m in range (0,nb_joueurs):
                    message_temporaire=message_queue.get()
                    if message_temporaire[0]==n:
                        for a in range (1,6):
                            if a == carte_choisie:
                                message_temporaire[a]=" . " 
                        message_queue.put(message_temporaire)
                        break
                    message_queue.put(message_temporaire)  
        elif choix == 1:
            test,carte_choisie=play(n)
            if not message_queue.empty():
                for m in range (0,nb_joueurs):
                    message_temporaire=message_queue.get()
                    if message_temporaire[0]==n:
                        for a in range (1,6):
                            if a == carte_choisie:
                                message_temporaire[a]=" . " 
                        message_queue.put(message_temporaire)
                        break
                    message_queue.put(message_temporaire)                                   
        elif choix == 2 and information_token.value!=0:
            test,indice,joueur_choisi=info(n)
            if not message_queue.empty():
                Message_existant=False
                for m in range (0,nb_joueurs):
                    message_temporaire=message_queue.get()
                    if message_temporaire[0]==joueur_choisi:
                        ancien_indice = message_temporaire
                        for c in range (1,6):
                            if type(ancien_indice[c])==str and ancien_indice[c][0] in ["1","2","3","4","5"] :
                                indice[c]=ancien_indice[c]   
                            elif type(ancien_indice[c])==int and type(indice[c])==str:
                                if "." not in indice[c]:
                                    indice[c]=str(ancien_indice[c])+indice[c]
                                else:
                                    indice[c]=ancien_indice[c]
                                        
                            elif type(ancien_indice[c])==str and type(indice[c]==int):
                                if "." not in ancien_indice[c]:
                                    indice[c]=str(indice[c])+ancien_indice[c]    
                        message_queue.put(indice)
                        Message_existant=True
                        break              
                    else:
                        message_queue.put(message_temporaire)
                if Message_existant==False:
                    message_queue.put(indice)     
            else:
                message_queue.put(indice)             
            
        message=test

        tour="N"
        while tour != "Y":
            tour=input("Passez au joueur suivant ? (Y/N)")
            
            if tour=="end":
                signal_queue.put("SIGUSR1")

        time.sleep(2)
        player_socket.sendall(message.encode())
        

def info(n):

    infor = None
    quel_joueur=None
    while ((quel_joueur not in liste_joueur) or (quel_joueur == n)):
            try:
                quel_joueur = int (input(f"Joueur {n}, de quel joueur veux-tu réveler la carte ? \n"))
            except ValueError:
                print("Veuillez entrer un joueur valide") 
    indice_donné=[quel_joueur]            
    while infor not in [1,2]:
        try:
            infor = int (input(f"Joueur {n}, veux-tu révéler une couleur (1) ou une valeur (2) ? \n"))
        except ValueError:
            print("Veuillez entrer un chiffre valide (1 ou 2).")
    if infor == 1:
        couleur = None
        while couleur not in ["red","green","blue","yellow","white"]:
            try:
                couleur = str (input("Choisissez la couleur que vous souhaitez révéler parmis les couleurs disponibles:"))
            except ValueError:
                print("Veuillez entrer une couleur valide (""red"",""green"", etc).")
        for nom,hand in hands.items():
            if (nom==quel_joueur):
                for cartes in hand:
                    if(cartes==None):
                        indice_donné.append("vide")
                    elif(cartes.couleur==couleur):
                        indice_donné.append(cartes.couleur)
                    else:
                        indice_donné.append(" . ")
                        
    
    if infor == 2:
        valeur = None
        while valeur not in [1,2,3,4,5]:
            try:
                valeur = int (input("Choisissez la valeur que vous souhaitez révéler parmis les valeurs disponibles:"))
            except ValueError:
                print("Veuillez entrer une valeur valide (1, 2, 3, 4, 5).")
        for nom, hand in hands.items():
            if(nom==quel_joueur):
                for cartes in hand:
                    if cartes==None:
                        indice_donné.append(0)
                    elif (cartes.valeur==valeur):
                        indice_donné.append(cartes.valeur)
                    else:
                        indice_donné.append(" . ")
    return "-information_token",indice_donné,quel_joueur

def play(n):
        h=dict(hands)
        playy = None
        while playy not in [1,2,3,4,5]:
            try:
                playy = int (input(f"Joueur {n}, quelle carte souhaites-tu jouer ? \n"))
            except ValueError:
                print("Veuillez entrer un chiffre valide (1, 2, 3, 4 ou 5).")

        erreur = True
        for i in range(0,nb_joueurs):
            if(h[n][playy-1].couleur == couleurs[i] and h[n][playy-1].valeur == pile[i]+1):
                erreur = False
                return f"{i}+{playy}+{h[n][playy-1].valeur}",playy
        
        if(erreur):
            return f"-fuse_token+{playy}",playy  
        

        
def kill_processes(sig, frame):

    if sig == signal.SIGUSR1 or sig == "SIGUSR1":

        os.kill(game_process.pid, signal.SIGTERM)
        print("Game is done")
        os.kill(os.getppid(), signal.SIGTERM)
        print("Main is done")

def kill_sockets(socket_processes,client_sockets):

    for client_socket in client_sockets :
        client_socket.shutdown(socket.SHUT_RDWR)
        print("socket close")

    for socket_process in socket_processes : 

        os.kill(socket_process.pid, signal.SIGTERM)
        print("Process socket kill")



if __name__ == "__main__":

    nb_joueurs=0

    while nb_joueurs not in [1,2,3,4,5]:
        try:
            nb_joueurs = int(input("Combien de joueurs ? (5 max)"))
        except ValueError:
            print("Veuillez entrer un chiffre valide (1, 2, 3, 4 ou 5).")
    
    deck_init,mains,couleurs,pile_init,liste_joueur = mise_en_place(nb_joueurs)
    
    information_token = Value('i',nb_joueurs+3)
    fuse_token = Value('i',3)
    message_queue=queue.Queue()
    
    pile = Array('i', pile_init)
    
    deck = Manager().list(deck_init)
    hands = Manager().dict(mains)

    mutex_handle=Lock()
    mutex_handle.acquire(block=False)

    mutexes = [Lock() for _ in range(nb_joueurs)]

    for mutex in mutexes :
        mutex.acquire(block=False)

    signal_queue = queue.Queue()
    signal.signal(signal.SIGUSR1, kill_processes)

    random_port = random.randint(1024, 65535)
    server_address = ('localhost', random_port)
  
    game_process = Process(target=game, args=())
    game_process.start()
    
    player_threads = [threading.Thread(target=player, args=(i+1, mutexes[i])) for i in range(nb_joueurs)]
    for thread in player_threads:
        thread.start()
    
    sig = signal_queue.get()
    kill_processes(sig, None)

    game_process.join()

    for thread in player_threads:
        thread.join()

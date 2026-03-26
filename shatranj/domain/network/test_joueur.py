from shatranj.domain.network.game_client import GameClient

nom = input("Quel est ton nom ? ")

def dessiner_plateau(code_plateau):
    propre = code_plateau.replace(",", "").replace(".", "-").replace("/", "")
    
    print("\n    a b c d e f g h")
    print("  +-----------------+")
    
    for i in range(8):
        ligne_num = 8 - i
        debut = i * 8
        fin = debut + 8
        morceau = propre[debut:fin]
        
        if len(morceau) < 8:
            morceau = morceau.ljust(8, "-")
            
        lettres = " ".join(morceau)
        print(f"{ligne_num} | {lettres} | {ligne_num}")
        
    print("  +-----------------+")
    print("    a b c d e f g h\n")

def afficher_message(msg):
    # NOUVEAU : Si le serveur dit NON, on l'affiche en gros !
    if msg.command == "INVALID":
        print(f"\n❌ LE SERVEUR REFUSE ! Raison : {msg.args[0]}")
        return

    # S'il y a un plateau, on le dessine
    a_un_plateau = False
    for info in msg.args:
        if info.startswith("board="):
            code_plateau = info.replace("board=", "")
            dessiner_plateau(code_plateau)
            a_un_plateau = True
            
    # Sinon on affiche les autres infos normales
    if not a_un_plateau:
        print(f"\n[SERVEUR] : {msg.command} {msg.args}")

client = GameClient("127.0.0.1", 12345, afficher_message)
client.connect(nom)

print("\nOrdres : ping, joueurs, inviter [ID], accepter, refuser, jouer [COUP], quitter")

while True:
    choix = input("-> ")
    
    if choix == "ping": 
        client.ping()
    elif choix == "joueurs": 
        client.get_players()
    elif choix.startswith("inviter"): 
        mots = choix.split()
        if len(mots) > 1: 
            client.invite_player(mots[1])
    elif choix == "accepter": 
        client.accept_invite()
    elif choix == "refuser": 
        client.decline_invite()
        
    elif choix.startswith("jouer"):
        mots = choix.split()
        if len(mots) > 1:
            coup = mots[1]
            # Ajoute le tiret si tu l'oublies (ex: e2e3 devient e2-e3)
            if len(coup) == 4 and "-" not in coup:
                coup = coup[:2] + "-" + coup[2:]
            client.play_move(coup)
            
    elif choix == "quitter": 
        client.disconnect()
        break
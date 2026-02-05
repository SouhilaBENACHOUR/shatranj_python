"""
Module de gestion des bitboards (représentation bas niveau du plateau).

Ce module implémente les exigences F25 et F26 du cahier des charges :
    - F25 : Module bitboard pour représenter l'état du plateau
    - F26 : Algorithmes de manipulation des bitboards

Principe des bitboards :
    Un bitboard est un entier de 64 bits où chaque bit représente une case
    de l'échiquier 8×8. Cette représentation permet des opérations ultra-rapides
    via les instructions binaires du processeur.

Structure des données :
    - 12 bitboards individuels (6 types de pièces × 2 couleurs)
    - Chaque bit = une case (0-63)
    - Bit à 1 = case occupée, bit à 0 = case vide

Numérotation des cases (cahier des charges F19) :
    8  56 57 58 59 60 61 62 63
    7  48 49 50 51 52 53 54 55
    6  40 41 42 43 44 45 46 47
    5  32 33 34 35 36 37 38 39
    4  24 25 26 27 28 29 30 31
    3  16 17 18 19 20 21 22 23
    2   8  9 10 11 12 13 14 15
    1   0  1  2  3  4  5  6  7
       a  b  c  d  e  f  g  h

Fichiers du module :
    - bitboard.py : Classe Bitboard principale (12 bitboards)
        Responsabilités :
            - Contient les 12 bitboards individuels
            - Méthodes : set_bit(), clear_bit(), get_bit(), get_piece_at()
            - Propriétés calculées : white_pieces, black_pieces, all_pieces
            - Initialisation position de départ
            - Conversion case ↔ notation algébrique
    
    - operations.py : Opérations binaires bas niveau 
        Responsabilités :
            - set_bit_at(bitboard, square) : Active un bit
            - clear_bit_at(bitboard, square) : Désactive un bit
            - get_bit_at(bitboard, square) : Teste un bit
            - count_bits(bitboard) : Compte les bits actifs
            - squares_from_bitboard(bitboard) : Liste des positions
    
    - masks.py : Masques pré-calculés
        Responsabilités :
            - KNIGHT_ATTACKS[64] : Attaques de cavalier pour chaque case
            - KING_ATTACKS[64] : Attaques de shah pour chaque case
            - ALFIL_ATTACKS[64] : Attaques d'alfil pour chaque case
            - FERZ_ATTACKS[64] : Attaques de ferz pour chaque case
            - FILE_MASKS[8] : Masques de colonnes a-h
            - RANK_MASKS[8] : Masques de rangées 1-8

Notation des pièces :
    Pièce       Blanc (MAJ)  Noir (min)
    Shah        K            k
    Ferz        F            f
    Rook        R            r
    Alfil       A            a
    Knight      N            n
    Pawn        P            p

Algorithmes fournis :
    - Vérifier si un coup est valide
    - Calculer les coups possibles pour un joueur
    - Appliquer un coup sur l'état du jeu
    - Calculer les scores des joueurs
    - Déterminer la fin de la partie

"""

# TODO: Importer les classes et fonctions lors de l'implémentation
# from shatranj.data.bitboards.bitboard import Bitboard
# from shatranj.data.bitboards.operations import (
#     set_bit_at,
#     clear_bit_at,
#     get_bit_at,
#     toggle_bit_at,
#     count_bits,
#     get_lsb,
#     pop_lsb,
#     squares_from_bitboard,
#     print_bitboard
# )
# from shatranj.data.bitboards.masks import (
#     KNIGHT_ATTACKS,
#     KING_ATTACKS,
#     ALFIL_ATTACKS,
#     FERZ_ATTACKS,
#     FILE_MASKS,
#     RANK_MASKS,
#     DIAGONAL_MASKS,
#     CENTER_MASK,
#     EDGE_MASK
# )
# from shatranj.data.bitboards.manager import BitboardManager

__all__ = [
    # Classe principale 
    # "Bitboard",
    # "BitboardManager",
    # Opérations binaires 
    # "set_bit_at",
    # "clear_bit_at",
    # "get_bit_at",
    # "toggle_bit_at",
    # "count_bits",
    # "get_lsb",
    # "pop_lsb",
    # "squares_from_bitboard",
    # "print_bitboard",
    # Masques pré-calculés
    # "KNIGHT_ATTACKS",
    # "KING_ATTACKS",
    # "ALFIL_ATTACKS",
    # "FERZ_ATTACKS",
    # "FILE_MASKS",
    # "RANK_MASKS",
    # "DIAGONAL_MASKS",
    # "CENTER_MASK",
    # "EDGE_MASK",
]
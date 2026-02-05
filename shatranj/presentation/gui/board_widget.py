"""
Rôle : Dessin plateau + drag'n'drop 
Fonctions :
    __init__(game) : Init Gtk.DrawingArea
    do_draw(cr) : Cairo rendering 8×8 (cases + pièces)
    on_button_press(event) : Clic souris → sélection pièce
    on_motion_notify(event) : Drag pièce
    on_button_release(event) : Drop → joue coup
    _highlight_legal_moves(square) : Surligne cases possibles
    Attributs : game, selected_square, dragging_piece
"""
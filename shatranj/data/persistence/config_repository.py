"""
Rôle : Gestion fichier .shatranjrc utilisateur Fonctions :

    load_config() : Lit ~/.shatranjrc → dict options
    create_default_config() : Crée .shatranjrc si absent
    validate_config(config_dict) : Vérifie cohérence options
    merge_with_cli(config, cli_args) : CLI override config file
"""
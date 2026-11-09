# Jour Tempo pour Home Assistant

Couleur Tempo et jour EJP d'aujourd'hui et de demain dans Home Assistant, **sans compte RTE, sans clé, sans inscription**. L'intégration lit l'API gratuite de [jourtempo.fr](https://jourtempo.fr/api/) toutes les 15 minutes.

- couleur Tempo d'aujourd'hui et de demain (source : RTE) ;
- jours bleus, blancs et rouges restants dans la saison ;
- jour EJP d'aujourd'hui et de demain, et jours EJP restants (source : calendrier publié par EDF) ;
- un capteur binaire « demain rouge », prêt pour vos automatisations ;
- configuration en un clic depuis l'interface, en français ou en anglais.

## Installation

### Avec HACS

[![Ouvrir dans HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=jourtempo&repository=ha-jourtempo&category=integration)

1. Dans HACS, ouvrez le menu ⋮, **Dépôts personnalisés**, collez `https://github.com/jourtempo/ha-jourtempo` et choisissez la catégorie **Intégration**.
2. Cherchez **Jour Tempo**, téléchargez-le, puis redémarrez Home Assistant.
3. **Paramètres**, **Appareils et services**, **Ajouter une intégration**, **Jour Tempo**. Validez : c'est tout.

[![Ajouter l'intégration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=jourtempo)

### À la main

Copiez le dossier `custom_components/jourtempo` dans le dossier `custom_components` de votre configuration Home Assistant, redémarrez, puis ajoutez l'intégration comme ci-dessus.

## Entités créées

| Entité | Valeurs |
| --- | --- |
| `sensor.jourtempo_couleur_aujourdhui` | `bleu`, `blanc`, `rouge` |
| `sensor.jourtempo_couleur_demain` | `bleu`, `blanc`, `rouge` ; inconnu avant l'annonce de RTE (vers 10 h 30, dans l'API avant 13 h) |
| `sensor.jourtempo_jours_restants_bleu` | nombre de jours bleus restants dans la saison |
| `sensor.jourtempo_jours_restants_blanc` | nombre de jours blancs restants |
| `sensor.jourtempo_jours_restants_rouge` | nombre de jours rouges restants |
| `sensor.jourtempo_ejp_aujourdhui` | `ejp`, `normal`, `hors_saison` |
| `sensor.jourtempo_ejp_demain` | `ejp`, `normal`, `non_verifie` (pas encore publié par EDF), `hors_saison` |
| `sensor.jourtempo_ejp_jours_restants` | nombre de jours EJP restants (sur 22) |
| `binary_sensor.jourtempo_demain_rouge` | allumé quand demain est un jour rouge |

Chaque fichier de l'API porte une date `perime_apres`. Passé cette date (panne prolongée de la source), les capteurs passent à **inconnu** plutôt que de garder une ancienne couleur : une automatisation ne se déclenchera jamais sur une donnée fausse.

Le jour Tempo commence à 6 h : entre minuit et 6 h, « aujourd'hui » reste la couleur de la veille, comme sur la facture.

## Exemple : prévenir la veille d'un jour rouge

```yaml
alias: Tempo - demain rouge
triggers:
  - trigger: time
    at: "18:00:00"
conditions:
  - condition: state
    entity_id: binary_sensor.jourtempo_demain_rouge
    state: "on"
actions:
  - action: notify.notify
    data:
      title: Jour rouge demain
      message: >-
        Demain est un jour Tempo rouge.
        Il reste {{ states('sensor.jourtempo_jours_restants_rouge') }} jours rouges cette saison.
```

## Exemple : couper le chauffe-eau un jour rouge

```yaml
alias: Tempo - chauffe-eau coupé les jours rouges
triggers:
  - trigger: time
    at: "06:05:00"
conditions:
  - condition: state
    entity_id: sensor.jourtempo_couleur_aujourdhui
    state: rouge
actions:
  - action: switch.turn_off
    target:
      entity_id: switch.chauffe_eau
```

## Questions fréquentes

**Faut-il un compte RTE ou une clé ?** Non. L'API de [jourtempo.fr](https://jourtempo.fr/api/) est publique et gratuite ; l'intégration n'envoie aucune donnée personnelle.

**D'où viennent les données ?** Les couleurs Tempo viennent de l'API officielle de RTE, les jours EJP du calendrier publié par EDF. Jour Tempo les relève plusieurs fois par jour et les diffuse en JSON ; tous les champs sont décrits sur [jourtempo.fr/api/](https://jourtempo.fr/api/).

**Puis-je interroger l'API plus souvent ?** Inutile : la couleur ne change qu'une fois par jour. L'intégration lit les deux fichiers toutes les 15 minutes, ce qui laisse la couleur de demain arriver dans Home Assistant dans le quart d'heure qui suit sa publication.

**Ce projet est-il lié à EDF ou à RTE ?** Non. Jour Tempo est un service indépendant ; seule la facture de votre fournisseur fait foi.

## Licence

MIT. Données : RTE (couleurs Tempo) et EDF (jours EJP), diffusées par [Jour Tempo](https://jourtempo.fr/).

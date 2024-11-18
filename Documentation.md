# Documentation du Projet

Bienvenue dans la documentation détaillée de votre projet Flask. Ce document couvre l'ensemble des composants de l'application, y compris les services, contrôleurs, modèles, schémas, extensions, configurations et tests. Chaque section fournit une description approfondie des fichiers et des fonctionnalités associés.

## Table des Matières

1. [Introduction](#introduction)
2. [Structure du Projet](#structure-du-projet)
3. [Détails des Composants](#détails-des-composants)
    - [Dockerfile](#dockerfile)
    - [Fichiers de Configuration](#fichiers-de-configuration)
        - [.env](#env)
        - [config.py](#configpy)
        - [extensions.py](#extensionspy)
    - [Serveur et Initialisation](#serveur-et-initialisation)
        - [server.py](#serverpy)
        - [__init__.py](#initpy)
    - [Contrôleurs](#contrôleurs)
        - [controllers/user.py](#controllersuserpy)
            - [Résumé des Endpoints](#résumé-des-endpoints)
            - [/user/register](#userregister)
            - [/user/login](#userlogin)
            - [/user/refresh](#userrefresh)
            - [/user/logout](#userlogout)
            - [/user/request_password_reset](#userrequest_password_reset)
            - [/user/reset_password](#userreset_password)
    - [Modèles](#modèles)
        - [models/user.py](#modelsuserpy)
    - [Schémas](#schémas)
        - [schemas/user.py](#schemasuserpy)
    - [Services](#services)
        - [services/user.py](#servicesuserpy)
    - [Tests](#tests)
        - [tests/user.py](#testsuserpy)
    - [Outils Utilitaires](#outils-utilitaires)
        - [printer.py](#printerpy)
4. [Fonctionnalités](#fonctionnalités)
5. [Gestion des Erreurs](#gestion-des-erreurs)
6. [Sécurité](#sécurité)
7. [Journalisation](#journalisation)
8. [Conclusion](#conclusion)
9. [License](#license)
10. [Remerciements](#remerciements)
11. [Contact](#contact)
12. [Historique des Versions](#historique-des-versions)
13. [Avertissement](#avertissement)

---

## Introduction

Ce projet est une application web construite avec Flask, offrant des fonctionnalités de gestion des utilisateurs telles que l'inscription, l'authentification, la réinitialisation de mot de passe et la gestion des tokens JWT. L'application utilise MongoDB pour le stockage des données, Redis pour la gestion des tokens révoqués et intègre des services tiers tels que l'envoi d'emails via SMTP.

---

## Structure du Projet

Voici la structure des fichiers et répertoires principaux du projet :

```
.
├── Dockerfile
├── printer.py
├── app
│   ├── __init__.py
│   ├── config.py
│   ├── extensions.py
│   ├── server.py
│   ├── controllers
│   │   └── user.py
│   ├── models
│   │   └── user.py
│   ├── schemas
│   │   └── user.py
│   ├── services
│   │   └── user.py
│   └── tests
│       └── user.py
└── requirements.txt
```
---

### Contrôleurs

#### user.py

1. **/user/register [POST]** : Permet à un nouvel utilisateur de s'inscrire.
2. **/user/login [POST]** : Authentifie un utilisateur et retourne des tokens JWT.
3. **/user/refresh [POST]** : Rafraîchit un token d'accès en utilisant un token de rafraîchissement.
4. **/user/logout [POST]** : Révoque le token actuel de l'utilisateur.
5. **/user/request_password_reset [POST]** : Envoie un email de réinitialisation de mot de passe.
6. **/user/reset_password [POST]** : Réinitialise le mot de passe de l'utilisateur.
7. **/user/delete [DELETE]** : Supprime le compte de l'utilisateur.
8. **/user/profile [GET]** : Récupère les informations du profil de l'utilisateur.
9. **/user/update_profile [PUT]** : Met à jour les informations du profil de l'utilisateur hors mot de passe.

#### file.py

1. **/file/upload [POST]** : Télécharge un fichier sur le serveur.
2. **/file/download [GET]** : Télécharge un fichier du serveur.
3. **/file/delete [DELETE]** : Supprime un fichier du serveur.

#### folder.py

1. **/folder/create [POST]** : Crée un nouveau dossier sur le serveur.
2. **/folder/delete [DELETE]** : Supprime un dossier du serveur.


---

### 

##### /user/register

###### Description

Permet à un nouvel utilisateur de s'inscrire en fournissant un nom d'utilisateur, un email et un mot de passe.

###### Paramètres

- **Body (JSON) :**
  - `username` (string, requis) : Nom d'utilisateur unique.
  - `email` (string, requis) : Adresse email unique.
  - `password` (string, requis) : Mot de passe sécurisé.

###### Réponses

- **Succès :**
  - **Message :** Indique que l'utilisateur a été créé avec succès.
  
- **Erreurs :**
  - **Validation des Données :** Si les données fournies ne respectent pas les règles de validation (par exemple, format incorrect de l'email, mot de passe trop faible).
  - **Conflit d'Unicité :** Si le nom d'utilisateur ou l'email est déjà utilisé par un autre utilisateur.

###### Codes de Statut

- `201 Created` : Utilisateur créé avec succès.
- `400 Bad Request` : Données invalides ou manquantes.
- `409 Conflict` : Nom d'utilisateur ou email déjà existant.

---

##### /user/login

###### Description

Authentifie un utilisateur en utilisant soit son nom d'utilisateur soit son email, et retourne des tokens JWT (accès et rafraîchissement).

###### Paramètres

- **Body (JSON) :**
  - `identifier` (string, requis) : Nom d'utilisateur ou email de l'utilisateur.
  - `password` (string, requis) : Mot de passe de l'utilisateur.

###### Réponses

- **Succès :**
  - **access_token** : Token JWT pour accéder aux ressources protégées.
  - **refresh_token** : Token JWT pour rafraîchir le `access_token`.

- **Erreurs :**
  - **Validation des Données :** Si les données fournies sont manquantes ou invalides.
  - **Identifiants Invalides :** Si le nom d'utilisateur/email ou le mot de passe est incorrect.

###### Codes de Statut

- `200 OK` : Authentification réussie.
- `400 Bad Request` : Données invalides ou manquantes.
- `401 Unauthorized` : Identifiants invalides.

---

##### /user/refresh

###### Description

Permet de rafraîchir un token d'accès en utilisant un token de rafraîchissement valide.

###### Paramètres

- **Headers :**
  - `Authorization` : Bearer token de rafraîchissement.

- **Body :** Aucun.

###### Réponses

- **Succès :**
  - **access_token** : Nouveau token JWT d'accès.

- **Erreurs :**
  - **Token Invalide ou Expiré :** Si le token de rafraîchissement est invalide ou expiré.
  - **Manque de Token :** Si aucun token n'est fourni.

###### Codes de Statut

- `200 OK` : Token rafraîchi avec succès.
- `401 Unauthorized` : Token de rafraîchissement invalide ou expiré.
- `400 Bad Request` : Token manquant.

---

##### /user/logout

###### Description

Révoque le token actuel de l'utilisateur, le rendant invalide pour les futures requêtes.

###### Paramètres

- **Headers :**
  - `Authorization` : Bearer token d'accès à révoquer.

- **Body :** Aucun.

###### Réponses

- **Succès :**
  - **Message :** Indique que la déconnexion a été réussie.

- **Erreurs :**
  - **Token Invalide ou Expiré :** Si le token est invalide ou déjà révoqué.
  - **Manque de Token :** Si aucun token n'est fourni.

###### Codes de Statut

- `200 OK` : Déconnexion réussie.
- `401 Unauthorized` : Token invalide ou expiré.
- `400 Bad Request` : Token manquant.

---

##### /user/request_password_reset

###### Description

Envoie un email de réinitialisation de mot de passe à l'utilisateur.

###### Paramètres

- **Body (JSON) :**
  - `email` (string, requis) : Adresse email de l'utilisateur demandant la réinitialisation.

###### Réponses

- **Succès :**
  - **Message :** Indique que, si un compte avec cet email existe, un email de réinitialisation a été envoyé.

- **Erreurs :**
  - **Validation des Données :** Si l'email fourni est manquant ou invalide.

###### Codes de Statut

- `200 OK` : Email de réinitialisation envoyé (ou message générique pour ne pas divulguer l'existence du compte).
- `400 Bad Request` : Email manquant ou invalide.

---

##### /user/reset_password

###### Description

Permet à l'utilisateur de réinitialiser son mot de passe en fournissant un token valide.

###### Paramètres

- **Body (JSON) :**
  - `token` (string, requis) : Token de réinitialisation reçu par email.
  - `password` (string, requis) : Nouveau mot de passe sécurisé.

###### Réponses

- **Succès :**
  - **Message :** Indique que le mot de passe a été réinitialisé avec succès.

- **Erreurs :**
  - **Token Invalide ou Expiré :** Si le token est invalide ou a expiré.
  - **Utilisateur Non Trouvé :** Si aucun utilisateur n'est associé au token.
  - **Validation des Données :** Si le nouveau mot de passe ne respecte pas les règles de validation.

###### Codes de Statut

- `200 OK` : Mot de passe réinitialisé avec succès.
- `400 Bad Request` : Token invalide/expiré, utilisateur non trouvé ou mot de passe invalide.
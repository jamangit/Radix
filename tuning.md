# Guide de réglage (tuning)

Toutes les valeurs que l'on peut ajuster pour optimiser Wordmeter / Radix, avec le fichier où elles se trouvent.
Les chemins sont relatifs à `apps/api` (backend) ou `apps/web` (frontend).

## Comment appliquer un changement

| Où est la valeur | Comment la changer | Pour que ça prenne effet |
|---|---|---|
| Variable d'environnement (section 1) | Ajouter ou modifier une ligne dans `apps/api/.env`, par exemple `WHISPER_MODEL=small` | **Redémarrer l'API** : le rechargement automatique (`--reload`) ne surveille pas `.env` |
| Constante dans le code backend (sections 2 et 3) | Modifier le fichier indiqué | Automatique si l'API tourne avec `--reload` |
| Constante dans le code frontend (section 4) | Modifier le fichier indiqué | Automatique avec `pnpm dev` |

Règle d'or : **changer une seule valeur à la fois** et noter l'effet dans le journal en bas de ce document.

Quand tu ajoutes une nouvelle variable à `.env`, ajoute aussi son nom dans `apps/api/.env.example` (avec une valeur factice) : c'est ce fichier-là qui est commité. Ne mets jamais de vrai secret dedans.

---

## 1. Réglages dans `apps/api/.env`

Chaque variable a sa valeur par défaut dans `src/wordmeter_api/config.py`.

### Transcription

| Variable | Défaut | Effet |
|---|---|---|
| `WHISPER_MODEL` | `base` | Taille du modèle de transcription. `tiny` : très rapide, peu précis. `small` : nettement meilleur en français, plus lent. `medium` : probablement trop lourd pour un petit Codespace. Un nouveau modèle se télécharge au premier lancement. |
| `WHISPER_COMPUTE_TYPE` | `int8` | `int8` est le plus rapide sur processeur. `float32` est plus précis mais beaucoup plus lent. |
| `PRELOAD_MODELS` | `false` | `true` charge Whisper au démarrage de l'API : la première phrase n'attend plus, mais le démarrage est plus long. Recommandé. |
| `VAD_SILENCE_MS` | `500` | Durée de pause qui termine une phrase. Plus bas : les mots arrivent plus vite, mais les phrases risquent d'être coupées. Plus haut : phrases entières, plus d'attente. |

### Qualité du son (conseil « trop loin du micro »)

| Variable | Défaut | Effet |
|---|---|---|
| `QUALITY_MIN_LEVEL_DB` | `-45` | Volume de voix sous lequel on avertit que l'utilisateur est trop loin ou parle trop bas. Plus haut (par exemple `-40`) : le conseil arrive plus tôt. |
| `QUALITY_MIN_SNR_DB` | `12` | Écart minimum entre la voix et le bruit de fond. En dessous : conseil « trop de bruit ». |

Si tu modifies `QUALITY_MIN_LEVEL_DB`, garde la même valeur dans `FAINT_LEVEL_DB` côté frontend (section 4), qui colore la jauge de volume.

### Limites

| Variable | Défaut | Effet |
|---|---|---|
| `MAX_STREAM_SECONDS` | `1800` | Durée maximale d'un enregistrement en direct (30 minutes). À ne relever qu'après la mise en place de la sauvegarde par tranches. |
| `MAX_AUDIO_SECONDS` | `600` | Durée maximale d'un fichier audio envoyé (route `/transcribe`). |
| `MAX_AUDIO_MB` | `25` | Taille maximale de ce fichier. |
| `WS_TICKET_SECONDS` | `60` | Durée de validité du ticket qui ouvre le WebSocket. |

### Sécurité et sessions

| Variable | Défaut | Effet |
|---|---|---|
| `JWT_SECRET` | obligatoire | Secret qui signe les sessions. Long, aléatoire, différent en production, jamais commité. |
| `ACCESS_TOKEN_MINUTES` | `10080` | Durée de la session (7 jours). |
| `COOKIE_SECURE` | `false` | À mettre à `true` **en production** : le cookie de session n'est alors envoyé qu'en HTTPS. En développement, laisse `false` : avec `true` sur une adresse en simple `http`, la connexion semblerait réussir mais la session ne tiendrait pas. |
| `DATABASE_URL` | base locale | Adresse de la base PostgreSQL. |

---

## 2. Valeurs dans le code : analyse des mots

| Valeur | Fichier | Actuelle | Effet |
|---|---|---|---|
| `DEFAULT_RARE_THRESHOLD` | `src/wordmeter_api/analysis/analyzer.py` | `3.5` | **Rareté des mots.** Échelle de Zipf : 3,0 correspond à environ 1 mot sur un million, 4,0 à environ 1 sur 100 000. Plus haut : davantage de mots comptés comme rares. Les mots inconnus du dictionnaire sont toujours ignorés (noms propres, fautes). |
| `DEFAULT_TOP_N` | `src/wordmeter_api/analysis/analyzer.py` | `10` | Nombre de mots fréquents et de mots rares affichés après une analyse. |
| `TOP_WORDS_LIMIT` | `src/wordmeter_api/services/stats.py` | `10` | Longueur du classement des mots dans les récaps jour, mois et année. |
| `MISMATCH_CONFIDENCE` | `src/wordmeter_api/routers/analyze.py` | `0.85` | Confiance requise avant d'avertir qu'un texte n'est pas dans la langue choisie. |
| `max_length` du texte | `src/wordmeter_api/routers/analyze.py` | `50_000` | Taille maximale d'un texte analysé. |
| `MAX_WORD_LENGTH` | `src/wordmeter_api/services/persistence.py` | `100` | Les mots plus longs ne sont pas enregistrés. |
| `_ELISIONS` | `src/wordmeter_api/analysis/tokenizer.py` | liste | Les « l' », « d' », « qu' »… retirés avant de compter. |

---

## 3. Valeurs dans le code : la voix

### Découpage en phrases (`src/wordmeter_api/speech/segmenter.py`, classe `SegmenterConfig`)

| Valeur | Actuelle | Effet |
|---|---|---|
| `start_threshold` | `0.5` | Sensibilité du détecteur de voix. Plus bas : capte les voix faibles, mais aussi plus de bruit. |
| `end_threshold` | `0.35` | Seuil sous lequel la voix est considérée comme arrêtée. |
| `min_speech_ms` | `250` | Les bruits plus courts (toux, choc, clic) sont ignorés. |
| `pre_roll_ms` | `256` | Audio conservé avant le début de la parole, pour ne pas couper la première syllabe. |
| `trailing_ms` | `128` | Silence conservé après la parole. |
| `max_utterance_ms` | `25000` | Coupure forcée pour quelqu'un qui ne fait aucune pause. |

La pause qui termine une phrase (`min_silence_ms`) se règle par `VAD_SILENCE_MS` dans `.env`.

### Transcription (`src/wordmeter_api/speech/transcriber.py`)

| Valeur | Actuelle | Effet |
|---|---|---|
| `beam_size` (dans `transcribe_pcm`) | `1` | `5` donne une transcription plus précise mais plus lente. |
| `no_speech_prob`, `avg_logprob`, `compression_ratio` (dans `_keep`) | `0.6`, `-1.0`, `2.4` | Filtres qui rejettent les phrases que Whisper invente sur du bruit. Plus strict : moins de fausses phrases, mais risque de perdre de vraies phrases. |
| `_HALLUCINATIONS` | liste | Phrases fantômes connues (« merci d'avoir regardé cette vidéo »…). À compléter quand tu en repères de nouvelles. |

### Session en direct (`src/wordmeter_api/routers/live.py`)

| Valeur | Actuelle | Effet |
|---|---|---|
| `LOCK_CONFIDENCE` | `0.8` | En mode Auto, confiance requise pour verrouiller la langue détectée. |
| `MAX_PENDING_PHRASES` | `10` | Phrases en attente avant que le serveur signale qu'il ne suit plus. |
| `MAX_FRAME_BYTES` | `64 * 1024` | Taille maximale d'un paquet audio reçu. |

### Mesure de qualité (`src/wordmeter_api/speech/quality.py`)

| Valeur | Actuelle | Effet |
|---|---|---|
| `CLIPPING_FRACTION` | `0.005` | Part de sons saturés qui déclenche le conseil « trop fort ». |
| `CLIPPING_SAMPLE` | `32000` | Niveau à partir duquel un échantillon est considéré comme saturé. |

---

## 4. Valeurs dans le code : le site

| Valeur | Fichier | Actuelle | Effet |
|---|---|---|---|
| `WEAK_PHRASES_BEFORE_HINT` | `src/features/analysis/audio-quality.ts` | `2` | Nombre de phrases faibles de suite avant d'afficher un conseil. |
| `HINTS` | `src/features/analysis/audio-quality.ts` | textes | Les messages de conseil affichés. |
| `METER_FLOOR_DB` | `src/features/analysis/audio-quality.ts` | `-60` | Bas de la jauge de volume. |
| `FAINT_LEVEL_DB` | `src/features/analysis/components/live-recorder.tsx` | `-45` | Couleur de la jauge. À garder égal à `QUALITY_MIN_LEVEL_DB`. |
| Options du micro | `src/features/analysis/use-live-transcription.ts` | réduction de bruit activée | `autoGainControl: false` est voulu : le réglage automatique du volume masquerait l'éloignement du micro. Ne pas l'activer. |
| `CHUNK_SAMPLES` | `src/features/analysis/pcm-worklet-source.ts` | `1600` | Taille d'un paquet audio envoyé (100 ms). |
| Mot de passe minimum | `src/features/auth/schemas.ts` | `8` | À garder identique à la règle côté API (`min_length` dans `src/wordmeter_api/routers/auth.py`). |
| Durée du splash | `src/app/page.tsx` | `2600` ms | Temps d'affichage du nom Radix avant la page de connexion. |
| Couleurs et arrondis | `src/app/globals.css` (bloc `:root`) | tokens | `--primary`, `--background`, `--radius`… Tout le design en dépend. |

---

## 5. Recettes à essayer

Les effets décrits sont ceux que l'on attend, à vérifier sur ta machine.

| Objectif | Réglages à tester |
|---|---|
| Plus rapide | `WHISPER_MODEL=tiny`, `VAD_SILENCE_MS=400` |
| Plus précis en français | `WHISPER_MODEL=small`, puis `beam_size=5` dans `transcribe_pcm` |
| Phrases moins coupées | `VAD_SILENCE_MS=700` |
| Conseil « trop loin » plus tôt | `QUALITY_MIN_LEVEL_DB=-40` (et `FAINT_LEVEL_DB` à `-40` dans le frontend) |
| Plus de mots rares détectés | `DEFAULT_RARE_THRESHOLD=4.0` |

---

## 6. Pour la mise en production (V2)

- `COOKIE_SECURE=true`, avec le site servi en HTTPS.
- Un `JWT_SECRET` neuf, long et aléatoire, et une vraie `DATABASE_URL`.
- Dans `apps/web/.env.local` (à créer) : `NEXT_PUBLIC_API_WS_URL=wss://adresse-de-ton-api` et `API_URL=https://adresse-de-ton-api`. Le port 8000 public est une astuce de développement propre à Codespaces, pas une solution de production.
- À ajouter avant un vrai lancement : vérification de l'origine du WebSocket, limitation des tentatives de connexion, vérification de l'email.
- `MAX_STREAM_SECONDS` ne doit être relevé qu'après la sauvegarde par tranches et la reconnexion automatique (enregistrements de plusieurs heures).

---

## Journal d'expériences

| Date | Valeur changée | Avant → après | Résultat |
|---|---|---|---|
|  |  |  |  |

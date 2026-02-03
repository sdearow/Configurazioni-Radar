#!/usr/bin/env python3
"""
Rome street coordinates database.
Contains known coordinates for major Rome streets and intersections.
This allows geocoding without external API calls.
"""

# Known Rome streets with approximate midpoint coordinates
# Format: 'street_name_lowercase': (latitude, longitude)
ROME_STREETS = {
    # Major consular roads (Strade consolari)
    'cassia': (41.9651, 12.4589),
    'flaminia': (41.9371, 12.4732),
    'salaria': (41.9267, 12.5089),
    'nomentana': (41.9167, 12.5234),
    'tiburtina': (41.8989, 12.5456),
    'prenestina': (41.8878, 12.5567),
    'casilina': (41.8689, 12.5678),
    'tuscolana': (41.8656, 12.5234),
    'appia': (41.8534, 12.5167),
    'ardeatina': (41.8456, 12.4978),
    'laurentina': (41.8323, 12.4789),
    'ostiense': (41.8545, 12.4756),
    'portuense': (41.8634, 12.4345),
    'aurelia': (41.8989, 12.4123),
    'trionfale': (41.9178, 12.4378),
    'boccea': (41.9089, 12.4089),

    # Major streets and viales
    'corso francia': (41.9367, 12.4678),
    'viale cortina d\'ampezzo': (41.9378, 12.4589),
    'viale liegi': (41.9234, 12.4934),
    'viale parioli': (41.9256, 12.4889),
    'viale regina margherita': (41.9112, 12.5034),
    'viale castro pretorio': (41.9034, 12.5023),
    'viale manzoni': (41.8889, 12.5089),
    'viale aventino': (41.8778, 12.4845),
    'viale trastevere': (41.8823, 12.4734),
    'viale marconi': (41.8545, 12.4656),
    'viale europa': (41.8267, 12.4667),
    'viale oceania': (41.8234, 12.4589),
    'cristoforo colombo': (41.8356, 12.4778),
    'circonvallazione': (41.8734, 12.5167),

    # Pineta Sacchetti area
    'pineta sacchetti': (41.9134, 12.4234),
    'forte braschi': (41.9112, 12.4178),
    'baldo degli ubaldi': (41.9056, 12.4312),

    # Boccea / Torrevecchia area
    'torrevecchia': (41.9234, 12.4089),
    'battistini': (41.9067, 12.4045),
    'cornelia': (41.9012, 12.4178),
    'gregorio xiii': (41.9078, 12.4156),

    # Prati / Vatican area
    'gregorio vii': (41.8934, 12.4534),
    'anastasio ii': (41.8967, 12.4489),
    'pio xi': (41.8989, 12.4512),
    'villa carpegna': (41.8978, 12.4456),
    'madonna del riposo': (41.8967, 12.4423),
    'clodio': (41.9156, 12.4567),
    'milizie': (41.9123, 12.4589),
    'cola di rienzo': (41.9089, 12.4623),
    'ottaviano': (41.9045, 12.4589),
    'cipro': (41.9078, 12.4545),
    'conciliazione': (41.9012, 12.4589),

    # Trastevere area
    'trastevere': (41.8856, 12.4678),
    'lungara': (41.8934, 12.4656),
    'gianicolense': (41.8778, 12.4534),
    'jenner': (41.8756, 12.4489),

    # Testaccio / Aventino
    'marmorata': (41.8778, 12.4756),
    'piramide': (41.8745, 12.4778),
    'ostiense': (41.8656, 12.4734),
    'garbatella': (41.8567, 12.4812),
    'aventino': (41.8823, 12.4834),

    # EUR area
    'eur': (41.8289, 12.4656),
    'colombo': (41.8367, 12.4756),
    'laurentino': (41.8189, 12.4678),
    'tintoretto': (41.8278, 12.4567),
    'torrino': (41.8123, 12.4489),

    # North Rome
    'tor di quinto': (41.9456, 12.4712),
    'ponte milvio': (41.9389, 12.4678),
    'parioli': (41.9312, 12.4889),
    'somalia': (41.9289, 12.5067),
    'panama': (41.9267, 12.5089),
    'priscilla': (41.9234, 12.5056),
    'stoppani': (41.9278, 12.4912),
    'trieste': (41.9189, 12.5034),
    'coppede': (41.9167, 12.5067),
    'montesacro': (41.9456, 12.5234),
    'conca d\'oro': (41.9512, 12.5189),
    'talenti': (41.9534, 12.5356),

    # East Rome
    'tiburtina': (41.9012, 12.5323),
    'san lorenzo': (41.8978, 12.5189),
    'verano': (41.9034, 12.5145),
    'pietralata': (41.9178, 12.5456),
    'rebibbia': (41.9278, 12.5589),
    'casal bertone': (41.9089, 12.5389),
    'centocelle': (41.8767, 12.5578),
    'torpignattara': (41.8789, 12.5489),

    # South-East Rome
    'tuscolano': (41.8678, 12.5234),
    'numidio quadrato': (41.8734, 12.5289),
    'cinecittà': (41.8567, 12.5623),
    'anagnina': (41.8389, 12.5712),
    'torre spaccata': (41.8634, 12.5678),

    # Specific streets mentioned in data
    'grottarossa': (41.9612, 12.4534),
    'barellai': (41.9189, 12.4434),
    'fabbroni': (41.9589, 12.4578),
    'pareto': (41.9567, 12.4589),
    'valdagno': (41.9378, 12.4712),
    'vigna stelluti': (41.9345, 12.4623),
    'pascucci': (41.9156, 12.4278),
    'tardini': (41.9134, 12.4312),
    'giureconsulti': (41.9034, 12.4167),
    'irnerio': (41.9012, 12.4189),
    'monte del gallo': (41.8912, 12.4567),
    'savorelli': (41.8978, 12.4478),
    'angelico': (41.9112, 12.4612),

    # Centro storico
    'tritone': (41.9023, 12.4878),
    'barberini': (41.9034, 12.4889),
    'nazionale': (41.9001, 12.4945),
    'termini': (41.9001, 12.5012),
    'cavour': (41.8956, 12.4923),
    'fori imperiali': (41.8923, 12.4878),
    'colosseo': (41.8902, 12.4922),
    'esquilino': (41.8967, 12.5034),
    'manzoni': (41.8889, 12.5067),
    'conte verde': (41.8878, 12.5089),
    'merulana': (41.8912, 12.5034),
    'brancaccio': (41.8923, 12.5023),
    'indipendenza': (41.9023, 12.5001),
    'volturno': (41.9034, 12.4989),
    'goito': (41.9045, 12.4978),
    'cernaia': (41.9045, 12.4967),

    # Pigneto / Prenestino
    'pigneto': (41.8867, 12.5278),
    'prenestino': (41.8834, 12.5389),

    # Marconi / Portuense
    'marconi': (41.8534, 12.4678),
    'pincherle': (41.8512, 12.4689),
    'cardano': (41.8523, 12.4712),
    'portuense': (41.8645, 12.4389),
    'trullo': (41.8589, 12.4278),
    'casetta mattei': (41.8612, 12.4234),

    # Monteverde
    'monteverde': (41.8712, 12.4478),
    'ramazzini': (41.8734, 12.4434),
    'folchi': (41.8756, 12.4456),
    'val tellina': (41.8723, 12.4445),

    # Gianicolense / Colli Portuensi
    'colli portuensi': (41.8689, 12.4378),
    'baldelli': (41.8712, 12.4356),

    # Nuovo Salario / Prati Fiscali
    'nuovo salario': (41.9445, 12.5134),
    'prati fiscali': (41.9378, 12.5112),

    # Balduina
    'balduina': (41.9189, 12.4312),
    'medaglie d\'oro': (41.9212, 12.4289),

    # Primavalle
    'primavalle': (41.9234, 12.4034),
    'monti di primavalle': (41.9256, 12.4012),
    'ipogeo degli ottavi': (41.9278, 12.3989),
    'calasanziane': (41.9189, 12.4056),
    'fratelli gualandi': (41.9234, 12.4078),

    # Aurelio
    'bra': (41.9023, 12.4145),
    'don carlo gnocchi': (41.9056, 12.4112),
    'cardinale costantini': (41.9189, 12.4089),
    'aloisi masella': (41.9167, 12.4067),

    # Bridges (Ponti)
    'ponte garibaldi': (41.8889, 12.4734),
    'ponte mazzini': (41.8923, 12.4678),
    'ponte sublicio': (41.8812, 12.4756),
    'ponte matteotti': (41.9112, 12.4712),
    'ponte risorgimento': (41.9156, 12.4689),
    'ponte duca d\'aosta': (41.9234, 12.4723),

    # Piazze (Squares)
    'piazza mancini': (41.9267, 12.4756),
    'piazza gentile da fabriano': (41.9245, 12.4734),
    'piazzale clodio': (41.9167, 12.4556),
    'piazza cavour': (41.9078, 12.4678),
    'piazza meucci': (41.8523, 12.4734),
    'piazza umanesimo': (41.8312, 12.4612),
    'piazza ostiense': (41.8734, 12.4778),

    # Porte (Gates)
    'porta cavalleggeri': (41.8989, 12.4512),
    'porta san giovanni': (41.8856, 12.5089),
    'porta metronia': (41.8812, 12.5034),
    'porta capena': (41.8845, 12.4934),
    'porta pia': (41.9089, 12.4989),
    'porta maggiore': (41.8912, 12.5156),

    # Lungotevere
    'lungotevere sangallo': (41.8923, 12.4689),
    'lungotevere fiorentini': (41.8956, 12.4678),
    'lungotevere in sassia': (41.9012, 12.4589),
    'lungotevere cadorna': (41.9189, 12.4689),
    'lungotevere maresciallo diaz': (41.9212, 12.4712),
    'lungotevere della vittoria': (41.9134, 12.4678),
    'lungotevere tebaldi': (41.8934, 12.4667),
    'lungotevere farnesina': (41.8945, 12.4645),

    # More Lungotevere short forms
    'sangallo': (41.8923, 12.4689),
    'fiorentini': (41.8956, 12.4678),
    'sassia': (41.9012, 12.4589),
    'cadorna': (41.9189, 12.4689),
    'diaz': (41.9212, 12.4712),
    'vittoria': (41.9134, 12.4678),
    'morra di lavriano': (41.9189, 12.4701),

    # More bridges
    'ponte pasa': (41.8923, 12.4689),
    'ponte vittorio emanuele': (41.8967, 12.4667),
    'ponte v.e.': (41.8967, 12.4667),

    # Pinciano area
    'rossini': (41.9156, 12.4889),
    'paisiello': (41.9167, 12.4901),
    'pinciana': (41.9145, 12.4912),
    'puccini': (41.9134, 12.4878),
    'allegri': (41.9123, 12.4867),

    # Talenti / Monte Sacro area
    'jonio': (41.9512, 12.5289),
    'col di rezia': (41.9501, 12.5278),
    'val di cogne': (41.9489, 12.5267),
    'val di lanzo': (41.9478, 12.5256),
    'tirreno': (41.9523, 12.5312),
    'valle scrivia': (41.9534, 12.5323),

    # Tuscolano / Spezia area
    'spezia': (41.8745, 12.5178),
    'nola': (41.8756, 12.5189),
    'monza': (41.8734, 12.5167),
    'caltagirone': (41.8723, 12.5156),

    # Emanuele Filiberto / San Giovanni
    'emanuele filiberto': (41.8878, 12.5078),
    'e.filiberto': (41.8878, 12.5078),

    # Ardeatina / Sette Chiese
    'sette chiese': (41.8534, 12.4978),
    'bompiani': (41.8523, 12.4967),

    # Pisana / Gianicolense
    'pisana': (41.8623, 12.4234),
    'grimaldi': (41.8612, 12.4223),
    'don guanella': (41.8589, 12.4289),

    # Cilicia / Galeria
    'cilicia': (41.8767, 12.5012),
    'piazza galeria': (41.8756, 12.5001),

    # Greca / Bocca della Verità
    'greca': (41.8867, 12.4845),
    'bocca della verita': (41.8878, 12.4834),

    # Caracalla
    'caracalla': (41.8789, 12.4934),
    'vittime del terrorismo': (41.8801, 12.4945),

    # Maresciallo Pilsudski
    'pilsudski': (41.9278, 12.4934),
    'maresciallo pilsudski': (41.9278, 12.4934),
    's.valentino': (41.9267, 12.4923),
    'san valentino': (41.9267, 12.4923),

    # Timavo
    'timavo': (41.9145, 12.4667),

    # Angelo Emo
    'angelo emo': (41.9034, 12.4234),

    # Portonaccio
    'portonaccio': (41.8989, 12.5334),
    'silvio latino': (41.8978, 12.5323),

    # Rolli
    'rolli': (41.8689, 12.4312),
    'stradivari': (41.8678, 12.4301),
    'pascarella': (41.8667, 12.4289),
}

def find_street_coords(street_name):
    """Find coordinates for a street name."""
    name_lower = street_name.lower().strip()

    # Direct match
    if name_lower in ROME_STREETS:
        return ROME_STREETS[name_lower]

    # Partial match
    for key, coords in ROME_STREETS.items():
        if key in name_lower or name_lower in key:
            return coords

    return None

def geocode_intersection_name(name):
    """
    Geocode an intersection name using the local database.
    Returns (lat, lng) or None.
    """
    import re

    if not name:
        return None

    # Remove leading number codes (e.g., "101-", "116-")
    clean_name = re.sub(r'^\d+[-\s]*', '', name)

    # Expand abbreviations
    abbreviations = {
        r'\bP\.zza\b': 'Piazza',
        r'\bP\.le\b': 'Piazzale',
        r'\bP\.za\b': 'Piazza',
        r'\bV\.le\b': 'Viale',
        r'\bV\.lo\b': 'Vicolo',
        r'\bL\.re\b': 'Lungotevere',
        r'\bL\.go\b': 'Largo',
        r'\bLgt\b': 'Lungotevere',
        r'\bC\.so\b': 'Corso',
        r'\bS\.\b': 'San',
    }

    for abbr, full in abbreviations.items():
        clean_name = re.sub(abbr, full, clean_name, flags=re.IGNORECASE)

    # Split by "/" to get individual parts
    parts = [p.strip().lower() for p in clean_name.split('/') if p.strip()]

    coords_list = []

    for part in parts:
        # Try to find this part in our database
        coords = find_street_coords(part)
        if coords:
            coords_list.append(coords)

    if not coords_list:
        # Try full name
        coords = find_street_coords(clean_name.lower())
        if coords:
            return coords

        # Try each word
        words = clean_name.lower().split()
        for word in words:
            if len(word) > 3:  # Skip short words
                coords = find_street_coords(word)
                if coords:
                    return coords

        return None

    # If we found multiple coords (intersection), average them
    avg_lat = sum(c[0] for c in coords_list) / len(coords_list)
    avg_lng = sum(c[1] for c in coords_list) / len(coords_list)

    return (avg_lat, avg_lng)

if __name__ == "__main__":
    # Test
    test_names = [
        "101-Cassia/Grottarossa",
        "116-P.zza Villa Carpegna/Madonna del Riposo",
        "119-Boccea/Battistini",
        "Ponte Milvio/Tor di Quinto",
        "Salaria/Somalia",
    ]

    for name in test_names:
        coords = geocode_intersection_name(name)
        print(f"{name} -> {coords}")

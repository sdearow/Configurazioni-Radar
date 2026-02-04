# UNCERTAIN INTERSECTION MATCHES - NEED YOUR CONFIRMATION

Based on the analysis of all Excel files, I found **224 intersections** in the master list (LOTTI M9 file).
- **M9.1**: 123 intersections
- **M9.2**: 97 intersections

## Files Analyzed:
1. **LOTTI M9_RADAR_v1_2026.01.28.xlsx** - Main configuration file (MASTER)
2. **ELENCO_LOTTO_1_2026.01.23.xlsx** - Lotto 1 installation details
3. **ELENCO LOTTO 2_2026.01.23.xlsx** - Lotto 2 installation details
4. **Swarco_Verifica stato - TOT_2026.01.29.xlsx** - SWARCO connection status
5. **Elenco IS RADAR_SEMAFORICA_per VERIFICA STATO AUT.xlsx** - Semaforica AUT status

---

## SECTION 1: HIGH CONFIDENCE MATCHES (Please confirm)

These Lotto 1 names match well with Master names based on keyword analysis:

| # | LOTTO 1 Name | MASTER Match | Confirm (Y/N) |
|---|-------------|--------------|---------------|
| 1 | `Emo - Bus` | `417-Angelo Emo/Capolinea Bus` | Y |
| 2 | `L.RE Diaz - Largo Mllo Diaz` | `413-L.re M.llo Diaz/Largo M.llo Diaz` | Y |
| 3 | `Via Cristoforo Colombo - Via Druso` | `209-Caracalla/Colombo/Druso` | Y |
| 4 | `Via Cernaia - Via Goito` | `442-Cernaia/Goito` | Y |
| 5 | `Via Anastasio II - Pio XI` | `121-Pio XI/Anastasio II` | Y |
| 6 | `Piazza di porta Portese` | `252-Portuense/Porta Portese` | Y |
| 7 | `Portuense/Casetta Mattei` | `261-Casetta Mattei/Poggio Verde` | Y/N? |
| 8 | `Piazzale Ostiense` | `231-Laurentina/Acqua Acetosa Ostiense` OR `270-Ostiense/Spizzichina` | ? |

---

## SECTION 2: UNCERTAIN MATCHES - Need Your Decision

These names have some similarity but I'm not confident. Please confirm:

| # | LOTTO 1 Name | Best MASTER Match | Score | Your Decision |
|---|-------------|-------------------|-------|---------------|
| 1 | `Marconi/Pincherle` | `248-Marconi/Metro` | 0.67 | |
| 2 | `P.le Umanesimo` | `226-Laurentina/Umanesimo` | 0.65 | |
| 3 | `Ponte Matteotti/P.zza delle Cinque Giornate` | `306-Ponte Matteotti/L.re Navi` | 0.62 | |
| 4 | `Ponte Risorgimento/P.zza Monte Grappa` | `307-Ponte Risorgimento/P.le Belle Arti` (M9.2)? | 0.53 | |
| 5 | `Ponte Garibaldi/Trastevere` | `250-Trastevere/Induno`? | 0.47 | |
| 6 | `Ponte Garibaldi/Arenula` | NO CLEAR MATCH | 0.55 | |
| 7 | `Ponte Mazzini/Lungara/L.re Farnesina` | NO CLEAR MATCH | 0.51 | |
| 8 | `Ponte Mazzini/L.re Tebaldi/L.re San Gallo` | `128-L.re Sangallo/Ponte PASA`? | 0.50 | |
| 9 | `Ponte Sublicio` | NO CLEAR MATCH | 0.50 | |
| 10 | `Piazza Pia/Conciliazione` | `132-Piazza Adriana/Crescenzio`? | 0.61 | |

---

## SECTION 3: NO MATCH FOUND - Need Manual Identification

These Lotto 1 intersections don't have a good match in the Master list.
They might be:
- Spelled completely differently in the master
- Missing from the master list
- Part of M9.2 instead of M9.1

| # | LOTTO 1 Name | Notes |
|---|-------------|-------|
| 1 | `Galvani/Marmorata/Gelsomini` | No matching keywords in master |
| 2 | `Viale Camillo Sabatini` | No matching keywords |
| 3 | `Rolli/Porta` | Multiple "Porta" intersections but no "Rolli" |
| 4 | `Milizie/Angelico` | No "Milizie" or "Angelico" in master |
| 5 | `Aventino/Circo Massimo` | No "Aventino" or "Circo Massimo" in master |
| 6 | `Rolli/Pascarella` | No "Rolli" or "Pascarella" in master |
| 7 | `Rolli/Stradivari` | No "Rolli" or "Stradivari" in master |

---

## SUMMARY STATISTICS

### Lotto 1 Matching:
- Total Lotto 1 records: **147**
- Confidently matched: **~122**
- Uncertain matches: **~18**
- No match: **~7**

### Lotto 2 Matching:
- Total Lotto 2 records: **96**
- Matched by code: **96** (all matched!)
- Uncertain: **0**

### Connection Data:
- Intersections with SWARCO data: **23** (Omnia system)
- Intersections with Semaforica data: **54** (Tmacs system)

---

## YOUR ACTION REQUIRED:

1. **Review Section 1** - Confirm the high-confidence matches (should be mostly Y)
2. **Review Section 2** - Tell me the correct match for each uncertain case
3. **Review Section 3** - Tell me what these intersections should map to, or if they should be added as new

Please respond with your confirmations and I will generate the final master report.

---

## COMPLETE MASTER INTERSECTION LIST

See the Excel file: **MASTER_INTERSECTION_REPORT.xlsx** for the complete list with all data.

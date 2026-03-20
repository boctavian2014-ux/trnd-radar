# MiroFish din dashboard – pas cu pas

Cum funcționează secțiunea MiroFish din dashboard și **ce trebuie să încarci**.

---

## Ce face MiroFish

MiroFish este un motor de **simulare / predicție** pe baza documentelor și a unei cerințe în limbaj natural. Ia documente (PDF, MD, TXT), extrage din ele **entități** (persoane, organizații, concepte) și **relații**, construiește un **graf** (GraphRAG), apoi rulează o **simulare** pe platforme sociale (Twitter, Reddit) cu **agenți virtuali** care postează, comentează și reacționează. La final poți genera un **raport** de analiză.

Tot fluxul se desfășoară din **dashboard-ul nostru** (Streamlit), în română; backend-ul MiroFish trebuie pornit separat (`npm run dev` în folderul MiroFish).

---

## Ce trebuie să încarci (Pas 1)

### 1. Fișiere – cel puțin unul

- **Formate acceptate:** PDF, MD (Markdown), TXT.
- **Ce conțin:** text despre subiectul pe care vrei să îl simulezi. Exemple:
  - un articol de știri despre un eveniment;
  - un raport sau un document despre o companie / organizație;
  - un text scurt despre o persoană publică sau un topic.
- **Rol:** MiroFish extrage din aceste documente **entități** (cine/ce apare) și **relații** între ele; pe baza lor construiește mai departe graful și agenții pentru simulare.

Poți încărca **mai multe fișiere** deodată (ex. două-trei articole despre același subiect).

### 2. Cerința de simulare (obligatoriu)

- **Ce e:** un text în **limbaj natural** care spune exact **ce vrei să simulezi** sau să „prezici”.
- **Exemple:**
  - *„Dacă compania X anunță concedieri masive, cum reacționează utilizatorii pe Twitter și Reddit?”*
  - *„Cum se răspândește știrea despre evenimentul Y în primele 24 de ore?”*
  - *„Ce sentiment au utilizatorii față de măsura Z?”*
  - *„Dacă persoana A face declarația B, care sunt reacțiile pe social media?”*

Fără acest text butonul **„Generează ontologie și creează proiect”** nu va avansa (vei vedea mesajul „Încarcă cel puțin un fișier și completează cerința de simulare”).

### 3. Nume proiect (opțional)

- Un nume pentru acest proiect (ex. „Test 1”, „Simulare știri”). Poți lăsa și valoarea implicită „Proiect Dashboard”.

---

## Pașii în ordine (după ce încarci și apeși butonul din Pas 1)

| Pas | Ce faci | Ce se întâmplă |
|-----|--------|----------------|
| **1** | Încarci fișiere + scrii cerința + (opțional) nume proiect → apeși **„Generează ontologie și creează proiect”** | Se analizează documentele și cerința; se creează proiectul și se generează „ontologia” (tipuri de entități și relații). |
| **2** | Apeși **„Pornește construcția grafului”** | Se construiește graful (GraphRAG) pe baza documentelor. Poate dura câteva minute. |
| **3** | Apeși **„Creează simulare (Twitter + Reddit)”** | Se creează simularea asociată proiectului și grafului. |
| **4** | Apeși **„Pregătește simularea”** | Se generează agenții virtuali și configurația pentru Twitter și Reddit. Poate dura câteva minute. |
| **5** | Apeși **„Pornește simularea”** | Simularea rulează (agenții postează, comentează etc.). Poți seta și număr maxim de runde (opțional). |
| **6** | Apeși **„Generează raport”** | Se generează raportul de analiză pe baza rezultatelor simulării. |

Fiecare pas depinde de precedentul: nu poți construi graful fără proiect (Pas 1), nu poți crea simularea fără graf (Pas 2), etc.

---

---

## Exemplu: măsurarea viralității unei aplicații

**Da, poți încărca un fișier MD (sau PDF/TXT) care descrie app-ul tău** și să folosești MiroFish pentru a simula cât de virală ar putea deveni pe rețelele sociale.

### Ce să pui în fișierul MD (despre app)

- **Numele aplicației** și tipul (ex. social, utilitar, joc, productivitate).
- **Ce face app-ul** – funcționalități principale, public țintă.
- **Ce îl face unic** sau de ce ar putea fi partajat (meme, utilitate, trend).
- Opțional: **lanțare / evenimente** (ex. lansare, update major, campanie).

Exemplu de conținut scurt în MD:
```markdown
# NumeApp – aplicație pentru X

NumeApp este o aplicație [tip] care [funcționalitate principală].
Public țintă: [cine o folosește].
De ce ar putea deveni virală: [motiv – ex. shareability, utilitate, trend].
```

### Cerința de simulare (pentru viralitate)

În câmpul **„Cerința de simulare”** scrie, de exemplu:

- *„Cât de virală poate deveni această aplicație pe Twitter și Reddit în primele săptămâni de la lansare? Simulează reacțiile utilizatorilor, partajările și discuțiile.”*
- sau: *„Cum se răspândește vestea despre această app pe social media? Ce tipuri de postări și comentarii apar?”*

Apoi parcurgi pașii 2–6 ca de obicei; raportul final îți va da indicii despre dinamica simulării (reacții, spread, sentiment).

---

---

## Eroare: API 500 / 401 „Incorrect API key”

Dacă la Pas 1 vezi **API 500** cu mesaj **„Incorrect API key provided”** sau **„invalid_api_key”**, problema e la **cheia LLM** din MiroFish, nu din dashboard.

**Ce faci:**

1. Deschide fișierul **`.env`** din folderul **MiroFish**:  
   `C:\Users\octav\Desktop\MiroFish\.env`
2. Verifică **`LLM_API_KEY`**. Trebuie să fie o cheie **validă** de la furnizorul LLM:
   - **Alibaba DashScope (Qwen):** [bailian.console.aliyun.com](https://bailian.console.aliyun.com/) sau [dashscope.console.aliyun.com](https://dashscope.console.aliyun.com/) → secțiunea API-KEY → creează/copiezi cheia și o pui în `.env`.
   - **OpenAI:** [platform.openai.com](https://platform.openai.com) → API keys. În `.env` setez și `LLM_BASE_URL=https://api.openai.com/v1` și `LLM_MODEL_NAME=gpt-4o-mini` (sau alt model).
3. Salvează `.env`, **oprește** MiroFish (Ctrl+C în terminal) și pornește din nou:  
   `cd C:\Users\octav\Desktop\MiroFish` apoi `npm run dev`.
4. Încearcă din nou Pas 1 în dashboard.

**Important:** Fișierul `.env` folosit pentru LLM este cel din **MiroFish**, nu cel din proiectul „social trends”.

---

## Rezumat

- **Ce încarci:** cel puțin **un fișier** (PDF/MD/TXT) cu text despre subiect + **cerința de simulare** (ce vrei să simulezi, în limbaj natural).
- **Cum funcționează:** completezi Pas 1 și apeși butonul; apoi parcurgi pașii 2–6 în ordine, fiecare cu butonul lui. Mesajul „Încarcă cel puțin un fișier și completează cerința de simulare” dispare după ce ai încărcat fișier(e) și ai scris cerința și apeși **„Generează ontologie și creează proiect”**.

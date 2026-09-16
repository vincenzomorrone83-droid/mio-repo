# mio-repo — Toolkit: da paper a sito interattivo

Catalogo e guida pratica degli strumenti per costruire questa pipeline:

**leggere un paper → capirne la teoria e la matematica → presentarla su un sito**

> Nota tecnica: questa sessione gira in un ambiente sandboxed il cui proxy di
> rete non permette il `git clone` diretto di repository esterni (richiede
> credenziali non disponibili qui). Per questo il codice dei 15 tool non è
> stato clonato dentro il repo: qui trovi la scheda di ognuno con il comando
> di installazione/clone da lanciare **in locale**, dove funziona normalmente.

---

## 1. Leggere il paper, estrarre teoria e matematica

| Tool | Repo | A cosa serve | Installazione |
|---|---|---|---|
| **Marker** | [VikParuchuri/marker](https://github.com/VikParuchuri/marker) | Converte PDF (anche paper con formule complesse) in Markdown pulito, preservando equazioni LaTeX, tabelle e struttura. Il punto di partenza migliore per portare un paper fuori dal PDF. | `pip install marker-pdf` oppure `git clone https://github.com/VikParuchuri/marker && cd marker && pip install -e .` |
| **Nougat** | [facebookresearch/nougat](https://github.com/facebookresearch/nougat) | OCR neurale specializzato su paper accademici: legge il layout scientifico (colonne, formule, riferimenti) meglio di un OCR generico. Utile quando Marker non basta (scan di bassa qualità, paper vecchi). | `pip install nougat-ocr` oppure `git clone https://github.com/facebookresearch/nougat` |
| **paper-qa** | [whitead/paper-qa](https://github.com/whitead/paper-qa) | Q&A su un archivio di paper con citazioni puntuali (pagina/frase) alla fonte. Serve per interrogare la teoria estratta ("cosa dice il paper sulla dimostrazione X?") senza perdere la tracciabilità. | `pip install paper-qa` oppure `git clone https://github.com/whitead/paper-qa` |
| **AnythingLLM** | [Mintplex-Labs/anything-llm](https://github.com/Mintplex-Labs/anything-llm) | Applicazione completa (UI + backend) per creare uno "spazio di lavoro" locale su un set di documenti e interrogarlo in chat. Utile come front-end pronto all'uso sopra i paper già estratti. | `git clone https://github.com/Mintplex-Labs/anything-llm && cd anything-llm && yarn setup` (richiede Node.js e Yarn; vedi il loro `docker-compose.yml` per l'avvio via Docker) |
| **GROBID** | [kermitt2/grobid](https://github.com/kermitt2/grobid) | Il parser di riferimento per convertire PDF scientifici in XML/TEI strutturato (titolo, autori, sezioni, bibliografia, formule). Più rigido di Marker/Nougat ma è lo standard usato dalla comunità (es. Semantic Scholar). | `docker run -t --rm -p 8070:8070 lfoppiano/grobid:0.8.0` (via Docker, più semplice) oppure `git clone https://github.com/kermitt2/grobid && cd grobid && ./gradlew clean install` (richiede Java 11+) |

**Come si incastrano:** Marker/Nougat/GROBID fanno l'estrazione (PDF → testo/markdown/XML strutturato con formule); paper-qa e AnythingLLM interrogano quel materiale per farti capire teoria e dimostrazioni prima di scrivere i contenuti del sito.

---

## 2. Costruire il sito (estetica "artigianale", fuori dagli schemi)

| Tool | Repo | A cosa serve | Installazione |
|---|---|---|---|
| **Quartz** | [jackyzha0/quartz](https://github.com/jackyzha0/quartz) | Genera un digital garden statico partendo da file Markdown (con supporto a wikilink, grafo delle note, LaTeX). Perfetto se i contenuti estratti dal paper restano in Markdown. | `npx quartz create` |
| **Astro** | [withastro/astro](https://github.com/withastro/astro) | Framework per siti a contenuto (blog, documentazione, landing) veloce di default, con island architecture: usi React/Vue/Svelte solo dove serve interattività. Buona base per il sito "principale". | `npm create astro@latest` |
| **react-three-fiber** | [pmndrs/react-three-fiber](https://github.com/pmndrs/react-three-fiber) | Renderer React per Three.js: permette di mettere in pagina visualizzazioni 3D (es. superfici, campi vettoriali, grafici della matematica del paper) come componenti dichiarativi. | `npm install three @react-three/fiber` |
| **shadcn/ui** | [shadcn-ui/ui](https://github.com/shadcn-ui/ui) | Non è una libreria da installare come dipendenza chiusa: genera componenti UI (bottoni, card, dialog) come codice sorgente dentro il progetto, così sono completamente modificabili. | `npx shadcn@latest init` |
| **Lenis** | [studio-freight/lenis](https://github.com/studio-freight/lenis) | Smooth scroll leggero e performante: dà quella sensazione di scorrimento "fluido/organico" invece dello scroll nativo a scatti. | `npm install lenis` |
| **Scrollama** | [russellgoldenberg/scrollama](https://github.com/russellgoldenberg/scrollama) | Libreria per lo scrollytelling: triggera eventi (cambio contenuto, animazioni) mentre l'utente scrolla — ideale per spiegare passo-passo una dimostrazione matematica o un esperimento del paper. | `npm install scrollama` |
| **neo-brutalism-ui** | [ekmas/neo-brutalism-ui](https://github.com/ekmas/neo-brutalism-ui) | Componenti React in stile neo-brutalista: bordi spessi, ombre nette, alto contrasto, look volutamente "grezzo" invece che patinato. | `npm install neo-brutalism-ui` |
| **Barba.js** | [barbajs/barba](https://github.com/barbajs/barba) | Gestisce transizioni fluide tra pagine (evita il "flash" del reload), utile per dare al sito un feeling cinematografico quando si passa da una sezione all'altra del paper. | `npm install @barba/core` |
| **p5.js** | [processing/p5.js](https://github.com/processing/p5.js) | Creative coding: permette di disegnare a codice elementi grafici/matematici (es. animare una formula, una simulazione, un grafico generativo) direttamente nel browser. | `npm install p5` (oppure via `<script>` da CDN per uso rapido) |
| **Locomotive Scroll** | [locomotivemtl/locomotive-scroll](https://github.com/locomotivemtl/locomotive-scroll) | Scroll library con supporto a parallasse ed elementi posizionati liberamente (non solo verticale/lineare) — utile per layout asimmetrici e più "editoriali". | `npm install locomotive-scroll` |

**Come si incastrano:** Astro o Quartz come base del sito; shadcn/ui per i componenti; Lenis o Locomotive Scroll per lo scroll fluido; Scrollama e Barba.js per le transizioni/narrazione; react-three-fiber e p5.js per le visualizzazioni matematiche/grafiche vere e proprie.

---

## Pipeline suggerita

1. **Estrai**: PDF del paper → Marker (o GROBID/Nougat) → Markdown/XML con formule.
2. **Capisci**: carica l'estratto in paper-qa o AnythingLLM, interroga teoria e dimostrazioni, prendi appunti in Markdown.
3. **Progetta**: struttura il sito con Astro (o Quartz se resti in puro Markdown); componenti UI con shadcn/ui.
4. **Racconta**: usa Scrollama/Barba.js/Lenis per la narrazione e lo scroll; p5.js e react-three-fiber per visualizzare la matematica.
5. **Pubblica**: build statica del sito (Astro/Quartz) e deploy su hosting statico a scelta.

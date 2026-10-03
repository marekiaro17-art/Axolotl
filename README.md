Un piccolo progetto DevOps che gira su un server Oracle Cloud (Ubuntu, ARM) e che *si ripara da solo*. Come l'axolotl, che rigenera le zampe perse.

*Demo live:* https://axolotl.speedrace.dpdns.org

Una pagina web mostra lo stato di quattro servizi in tempo reale. Con il pulsante "Simula un guasto" si può provocare un malfunzionamento e guardare il sistema accorgersene e recuperare.

## Cosa fa

- Controlla ogni 30 secondi quattro servizi: il sito Axolotl (nginx in Docker), Google, GitHub e Wikipedia
- Mostra lo stato con un axolotl disegnato in SVG: ogni zampa è un servizio, se uno cade la zampa sparisce e poi ricresce
- Tiene lo storico degli ultimi controlli e calcola la disponibilita (uptime)
- Il pulsante "Simula un guasto" ha un limite di un click al minuto, per non essere abusato
- Ogni modifica caricata su GitHub viene pubblicata sul server in automatico

## Come e fatto

mermaid
flowchart LR
    V[Visitatore] -->|HTTPS| CF[Cloudflare]
    CF --> T[tunnel: cloudflared]
    T --> F[status: pagina di stato]
    F -->|controlla| E[web: nginx]
    G[autoheal] -.->|riavvia se guasti| F
    G -.-> E
    P[Push su GitHub] --> A[GitHub Actions]
    A -->|SSH| S[Server Oracle Cloud]
    S --> D[Docker Compose]


## Tecnologie

- Docker e Docker Compose
- Healthcheck e riavvio automatico dei container (autoheal)
- Cloudflare Tunnel per pubblicare la pagina in HTTPS senza aprire porte
- GitHub Actions per il deploy automatico via SSH
- Python (solo libreria standard) per la pagina di stato
- Ubuntu 24.04 su Oracle Cloud (ARM)

## Sicurezza

Ho seguito il principio del *minimo privilegio*: ogni componente ha solo i permessi che gli servono, niente di piu.

*Rete*
- La pagina e pubblicata con *Cloudflare Tunnel: il server si collega a Cloudflare in uscita, quindi **nessuna porta in entrata e stata aperta* per il sito
- HTTPS gestito da Cloudflare, che fa anche da filtro davanti al server
- La porta della pagina di stato e esposta solo in locale (127.0.0.1), mai su internet
- Firewall di rete Oracle: le porte non necessarie restano chiuse

*Container*
- Il container della pagina di stato non gira come root ma come utente senza privilegi
- Disco in sola lettura: chi violasse l'applicazione non potrebbe scrivere ne scaricare programmi
- Tutte le capability Linux rimosse e no-new-privileges attivo
- Limiti di memoria (128 MB), CPU (mezzo core) e numero di processi (100), per evitare che un sovraccarico fermi il resto del server

*Server*
- Accesso SSH solo con chiave: login con password disattivato, root senza password
- fail2ban attivo: oltre 2000 tentativi di accesso respinti, 148 indirizzi bloccati
- Servizio rpcbind disattivato per ridurre le porte esposte

*Applicazione web*
- Intestazioni di sicurezza: Content-Security-Policy, X-Content-Type-Options, Cache-Control: no-store
- Limite di richieste sul pulsante di simulazione (429 se si preme troppo presto)
- La simulazione agisce solo su un servizio dimostrativo e non puo toccare altri container

*Segreti e deploy*
- Il token del tunnel sta in un file .env fuori dal repository (.gitignore) e l'ho rigenerato dopo averlo usato
- Il deploy usa una chiave SSH salvata nei segreti di GitHub, mai nel repository
- I token GitHub hanno solo i permessi necessari

*Prossimi passi*
- Chiave di deploy dedicata con permessi limitati e rotazione periodica
- Monitoraggio con Prometheus e Grafana

## Problemi incontrati e risolti

- *Il deploy falliva* perche autoheal riavviava il container proprio mentre Docker lo sostituiva. Soluzione: nel deploy si rimuove prima il container, poi lo si ricrea
- *Il controllo di salute non funzionava* perche localhost veniva risolto in IPv6 e il servizio ascoltava solo in IPv4. Soluzione: usare 127.0.0.1
- *Il push veniva rifiutato* perche il token GitHub non aveva il permesso workflow. Soluzione: nuovo token con i permessi giusti
- *Il tunnel non si poteva installare come servizio* perche sul server ce n'era gia uno per un altro progetto. Soluzione: farlo girare come container Docker dentro il progetto, senza toccare quello esistente

## Limiti noti

- autoheal ha accesso al socket di Docker, che e un accesso potente. In un ambiente di produzione si userebbe un orchestratore o un permesso piu ristretto
- Il progetto gira su un singolo server: se cade il server, cade tutto

## Cosa ho imparato

Container, healthcheck, pipeline di deploy automatico, sicurezza di base di un server Linux, tunnel e HTTPS con Cloudflare, e come diagnosticare un problema leggendo i log.

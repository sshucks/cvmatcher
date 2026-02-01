# CLC3-Projekt: Microservice-Architektur für CVMatcher

Im Rahmen dieses Projekts wurde eine bestehende Python-Anwendung bestehend aus Streamlit-Frontend und FastAPI-Backend in eine containerisierte Microservice-Architektur überführt. Ziel war es, die Anwendung modularer, robuster und skalierbarer zu gestalten.


## Applikation starten
### .env File modifizieren
Das .env File konfiguriert den Pfad zu den Google Cloud Credentials. Dieser Pfad muss individuell angepasst werden und zu Credentials führen, die Berechtigung für den Zugriff zu den entsprechenden Google Cloud Storage Buckets haben.

### docker compose build
Der Command "docker compose build" baut den Docker Container mit allen Microservices. Dazu muss Docker Desktop aktiv sein.

### docker compose up
Der Command "docker compose up" startet die Applikation. Sie ist nun auf http://localhost:8501/ erreichbar

---

## Cloud Data Storage

---

## Large Language Model

### Ist-Analyse der aktuellen Implementierung

Für das Parsen der Lebensläufe und Anforderungen wird ein lokal ausgeführtes LLM mit GPU-Unterstützung verwendet. Als Input werden die Dokumente im UI hochgeladen und anschließend wird der Text, zusammen mit einem Prompt Text und den .json-Schema, an das LLM weitergeleitet. Die Parameter begrenzen dabei die Zufälligkeit des Modells, indem die Temperatur auf 0, Top K auf 1 und Top P auf 1 gesetzt werden. Die Temperatur steuert die Zufälligkeit des Modells, wobei eine kleine Zahl für deterministischere Antworten steht. Top K beschränkt die Anzahl der wahrscheinlich nächsten Wörtern, sodass nur das wahrscheinlichste Wort herangezogen wird. Top P steuert die Auswahl der Token anhand von Wahrscheinlichkeiten, was bei einem Wert von 1 keine Einschränkung meint. Zuletzt wird ein Seed gesetzt, der die Varianz des Modells ebenfalls reduzieren soll. Output des Modells ist ein .json, das die folgenden Felder beinhaltet:

* Persönliche Daten: Name, Mail, Telefonnummer und Geburtsdatum
* Hardskills
* Softskills
* Ausbildung: Bereich, Abschluss und Abgeschlossen-Indikator
* Berufserfahrung: Dauer (Start- und Enddatum), Branche, Jobtitel und Verantwortungsbereiche

Ein Lebenslauf wird mehrfach an das Modell übergeben, wobei dann jene Ergebnisse herangezogen werden, die in `n` der `m` Outputs vorkommen. So soll die Varianz des Modells noch weiter reduziert werden. Gespeichert werden die Files lokal, wobei in einer SQLite-Datenbank der Hash-Wert, der Filepath und eine Flag gespeichert wird, die angibt, ob der Lebenslauf schon mal geparsed wurde.

### Datenschutzanalyse der Google Cloud LLM-Lösung

Lebensläufe enthalten personenbezogene Daten, diese müssen laut DSGVO geschützt werden Für Cloud Lösungen müssen zusätzliche Vorgaben der DSGVO berücksichtigt werden. Google Cloud bietet mit Vertex AI eine Plattform, auf der generative AI-Modelle genutzt und weiterentwickelt werden können. Dabei gibt es unterschiedliche Modelle, die entweder Google-eigens sind oder von Drittanbietern. Dabei ergeben sich folgende Probleme:

* Grundsätzlich wird ein Auftragsverarbeitungsvertrag mit Google benötigt, um sicherzustellen, dass die personenbezogenen Daten gesichert verarbeitet werden. Dieser wird grundsätzlich von Google bereitgestellt, allerdings braucht es in dieser Situation eine schriftliche Vereinbarung, die uns als Projektgruppe vom Auftraggeber erlaubt, die Daten an Google weiterzugeben.
* Die Datenverarbeitung kann durch externe Modelle durchgeführt werden, wobei nicht mehr garantiert werden kann, wohin die Daten übermittelt werden. Auch wenn eine Instanz in der EU ausgewählt wird, können die Daten in einem Drittland verarbeitet werden, was eine zusätzliche Vereinbarung erfordert.
* Eine Drittlandübermittlung kann auch beim Google-eigenen Dienst Gemini nicht ausgeschlossen werden, da die Kommuniktion mit Gemini online passiert. 
* Weiters werden die Prompts von Google teils zum Schutz vor Missbrauch zwischengespeichert, was problematisch ist, da der Text der Lebensläufe ebenfalls im Prompt übermittelt wird. Diese Einstellungen können teils deaktiviert werden, ein Restrisiko bleibt allerdings.
* Sowohl wir als Auftragsverarbeiter, wie auch Google als Sub-Auftragsverarbeiter muss gewährleisten, dass die Betroffenenrechte lt. DSGVO (wie Auskunftsrecht oder Recht auf Löschung) gewahrt werden. Weiters muss ein Nachweis über den Datenfluss erbracht werden und die Daten dürfen nicht länger als notwendig gespeichert werden. Dies ist alleine durch die vorher genannten Punkte schwierig bis teils nicht möglich.

Da diese Probleme zu weitreichend sind und eine Anonymisierung bzw. Pseudonymisierung zu viel menschliche Interaktion erfordert, haben wir uns gegen eine Implementierung des LLMs entschieden.

---

## Studienprojekt – CV-Matcher

### Einführung

Unser Studienprojekt ist eine Kooperation mit **Trescon** und beschäftigt sich mit der maschinellen Bewertung von Lebensläufen.  
Dabei werden Lebensläufe mit Anforderungsdokumenten verglichen, welche den/die ideale/n Kandidat/in für eine Stelle beschreiben. Ziel ist es, passende Kandidat*innen effizient zu identifizieren.

Es wurde mit Trescon bereits abgeklärt, dass dieses Studienprojekt in diesem Rahmen verwendet werden darf.

---

## Methodik

Lebensläufe und Anforderungsdokumente werden mithilfe eines **Large Language Models (LLM)** geparst und in ein maschinenlesbares Format überführt (JSON mit vordefinierter Struktur).  
Die geparsten Lebensläufe werden anschließend in einer Datenbank gespeichert.

Für die weitere Verarbeitung und Bewertung wurden mehrere Methoden entwickelt:

- **Vergleich über Embeddings**  
  Cosine Similarity misst die Ähnlichkeit zwischen Lebenslauf und Anforderungsdokument

- **ESCO-Ontologie**  
  Die ESCO-Ontologie beschreibt Berufe und Fähigkeiten.  
  ESCO-Terme aus dem Anforderungsdokument werden im Lebenslauf gesucht.  
  Ein Score gibt an, wie viele dieser Begriffe abgedeckt sind.

- **Vergleich mit LLM**  
  Lebenslauf und Anforderungsdokument werden gemeinsam an das LLM übergeben, das einen sprachlich erklärten Score erzeugt.

---

## Ausgangssituation

Die derzeitige Systemarchitektur besteht aus zwei getrennten Schichten (Frontend und Backend), die beide mit Python implementiert wurden und mittels FastAPI kommunizieren. Beide Komponenten werden gemeinsam in einem Docker Container betrieben. Die Anwendung ist derzeit für den lokalen Betrieb ausgelegt. Die Ausführung des integrierten Large Language Models erfolgt GPU-beschleunigt und wird über Ollama angebunden. Die Entscheidung für das lokale LLM verlief vor allem aufgrund der Datenschutzverordnung, um reale Kundendaten von TRESCON verwenden zu dürfen. Dieser Sicherheitsaspekt soll im gesamten Projekt beachtet werden.

Zurzeit werden die geparsten Lebensläufe als Dateien lokal gespeichert und der Dateipfad wird gemeinsam mit einem eindeutigen Hash in einer Datenbank abgelegt. Bei Upload eines Lebenslaufs wird mittels Hash überprüft ob dieser bereits in der Datenbank vorhanden ist, ansonsten wird er ebenfalls geparst und der Pfad wird in der Datenbank abgelegt.

![Old Architecture](clc_old_architecture.png)

---

## Neues Deployment

Im Rahmen dieses Projekts wurde die bestehende Applikation in eine **Microservice-Architektur** überführt, wobei folgende Microservices umgesetzt wurden

- UI-Service
- CV-Parsing-Service
- Requirements-Parsing-Service
- Matching-Service
- DataAccess-Service

Alle Services laufen in separaten Docker-Containern und kommunizieren über das interne Docker-Netzwerk mittels HTTP. Die Netzwerkverwaltung und Orchestierung wird von Docker Compose übernommen.


![New Architecture](clc_new_architecture.png)

Zusätzlich soll evaluiert werden, wie die Abfrage des LLMs in der **Cloud** ausgeführt werden kann, sodass keine lokalen Ressourcen (GPU) mehr benötigt werden.  Nach Möglichkeit soll diese Cloud-LLM-Lösung auch implementiert werden.

Besondere Schwerpunkte:
- Datensicherheit und Datenschutz
- Kostenoptimierung

---


## Cloud-Technologien

Für dieses Projekt wird **Google Cloud** verwendet.  
Es wurde eine eigene E-Mail-Adresse erstellt, über die alle Teilnehmerinnen Zugriff auf die Cloud-Ressourcen erhalten.  
Diese kann später auch an die Auftraggeber übergeben werden.

---

## Lessons-learned

### Internes Docker-Netzwerk
* **Container-Isolation:** ```localhost``` gilt nur innerhalb eines Containers, keine direkte Kommunikation zwischen Services über ```localhost```.
* **Service-Namen nutzen:** Kommunikation zwischen Microservices muss über die Docker-Service-Namen erfolgen (cv-parsing-service:8000 etc.).
* **Server auf 0.0.0.0 binden:** Nur so sind Services im Docker-internen Netzwerk sichtbar und für andere Container erreichbar.

### Google Cloud Storage 
* **Abstimmung zwischen Services**: Korrekte Abstimmung zwischen Services kann zu Problemen führen.
* **DSGVO**: DSGVO-konforme Einrichtung hat vielseitige Aspekte, die berücksichtigt werden müssen.

### Large Language Model
* **Sicherheitsbewertung**: Sicherheitsbewertung ist als erster Schritt vor der Implementierung notwendig, um Probleme und Anforderungen frühzeitig erkennen und lösen zu können.
* **Parametrisierung des Modells**: Korrekte Parametrisierung des Modells führt zu verlässlicheren Ergebnissen. Zusätzliches Majority Voting erhöht Verlässlichkeit noch mehr.

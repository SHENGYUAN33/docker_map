```mermaid
sequenceDiagram
    actor User as 雿輻??
    participant App as Flask Application
    participant LLM as LLM + Fallback
    participant API as Node.js CMO API
    participant Map as MapState + MapService

    Note over User,Map: ????Step 1: ?臬?喳? ????
    User->>App: "蝜芾ˊ052D?盛瘙摨扳?"
    App->>LLM: 閫????
    LLM-->>App: {enemy: ["052D"], roc: ["瘝望?"]}
    App->>API: POST /import_scenario
    API-->>App: ?西摨扳?鞈?
    App->>Map: 蝜芾ˊ?西璅?
    Map-->>App: ?啣? HTML
    App-->>User: 憿舐內?西雿蔭?啣?

    Note over User,Map: ????Step 2: ???菜 ????
    User->>App: "???脰??菜"
    App->>LLM: 蝣箄??粹?憪?隞?
    App->>API: POST /star_scenario
    App-->>User: "璅⊥?脰?銝?.."

    Note over API: ??瑁? WTA 璅⊥...
    API->>App: POST /wta_completed (?)

    Note over User,Map: ????Step 3: ?亦?甇血?晷 ????
    User->>App: "?亦?甇血?晷蝯?"
    App->>LLM: 閫???格??西
    App->>API: POST /get_wta
    API-->>App: WTA 蝯? (?餅?瘜Ｘ活?郎?具漣璅?
    App->>Map: 蝜芾ˊ?餅?蝺?+ ?
    Map-->>App: ?啣? HTML + ??批??
    App-->>User: 憿舐內 WTA ?啣? + 蝯?銵冽

    Note over User,Map: ????Step 4: 憿舐內?芾楚 ????
    User->>App: "憿舐內?芾楚"
    App->>LLM: 蝣箄??箄頝⊥?隞?
    App->>Map: 霈??track_data.json<br/>蝜芾ˊ頠楚?? + ?嗅?雿蔭
    Map-->>App: ?啣? HTML
    App-->>User: 憿舐內?芾楚?啣?

    Note over User,Map: ????Step 5: 頠??? ????
    User->>App: "??憌?撠?憭??"
    App->>API: POST /get_answer (RAG)
    API-->>App: ?? + 靘??辣
    App-->>User: 憿舐內?? + ??皞?

    Note over User,Map: ????Step 6: ?漱?? ????
    User->>App: ??: "蝑?銝???
    App->>App: ?脣???/feedbacks/
    App-->>User: ??撌脰???

    Note over User,Map: ????Step 7: COP ?芸? ????
    User->>App: "?芸? COP"
    App->>App: Selenium ?芸???啣??
    App-->>User: COP ?芸? (Base64 PNG)
```

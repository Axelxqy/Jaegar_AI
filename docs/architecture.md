flowchart TB
    U["User"] <--> UI["JAEGAR Frontend"]
    UI <--> API["Backend API"]

    API <--> CORE["Agent Core<br/>Central Coordinator"]

    CORE <--> MODEL["Model Interface"]
    MODEL <--> LLM["LLM<br/>(Qwen or replaceable model)"]

    CORE <--> MEM["Memory Engine"]
    CORE <--> TASK["Task State Manager"]
    CORE <--> TOOLS["Tool Orchestrator"]
    CORE <--> RET["Retrieval System"]
    CORE <--> LEARN["Learning System"]

    CORE --> RUBRIC["Rubric System<br/>Quality Evaluation"]
    CORE --> POLICY["Policy Engine<br/>Permission & Authority"]
    CORE <--> SECURITY["Security Engine"]

    MEM <--> PERSIST["Persistence Layer"]
    TASK <--> PERSIST
    LEARN <--> PERSIST
    RET <--> PERSIST

    TOOLS <--> EXT["External Tools & Services"]

    RUBRIC -. "Evaluation results" .-> CORE
    POLICY -. "Authorisation decisions" .-> CORE
    SECURITY -. "Security controls" .-> CORE

    PERSIST <--> DB[("Database & Records")]

----------------------------------------------------------------------

flowchart TD
    A["User submits message"] --> B["Backend API receives request"]
    B --> C["Agent Core coordinates request"]

    C --> D["Load relevant context"]
    D --> E["Memory Engine & Retrieval System"]
    E --> F["Task State Manager provides task context"]

    F --> G["Model generates proposal or response"]

    G --> H{"Does the request require an action?"}

    H -->|No| I["Rubric evaluates response"]
    H -->|Yes| J["Tool Orchestrator prepares action"]

    J --> K["Security Engine checks security constraints"]
    K --> L["Policy Engine checks permissions"]

    L -->|Not authorised| M["Request approval or reject action"]
    L -->|Authorised| N["Execute permitted action"]

    N --> O["Verify action result"]
    O --> I

    I --> P{"Rubric outcome"}

    P -->|PASS| Q["Independent verification"]
    P -->|PASS WITH RESTRICTIONS| R["Apply restrictions and qualify output"]
    P -->|REVIEW| S["Escalate or request clarification"]
    P -->|REJECT| T["Correct, regenerate or stop"]

    T --> G

    Q --> U["Update relevant task and records"]
    R --> U
    S --> V["Communicate unresolved issue"]
    U --> W["Return response to user"]
    V --> W

----------------------------------------------------------------------

flowchart TD
    A["User interaction or system observation"] --> B["Candidate Builder"]
    B --> C["Candidate Storage"]

    C --> D["Memory Evaluator"]

    D --> E{"Evaluate candidate"}

    E -->|Duplicate| F["KEEP existing record"]
    E -->|Contradiction| G["REVIEW or resolve conflict"]
    E -->|Refinement| H["Propose UPDATE or REFINE"]
    E -->|New information| I["Propose CREATE"]
    E -->|Insufficient evidence| J["REJECT or retain for review"]

    G --> K["Policy Engine authorises proposed operation"]
    H --> K
    I --> K

    K -->|Denied| L["Preserve existing state"]
    K -->|Approved| M["Persistence Layer executes operation"]

    M --> N["Verify persisted result"]
    N --> O["Update memory records and metadata"]

    O --> P["Available for future retrieval"]
    F --> P
    L --> Q["Record decision and rationale"]
    J --> Q

----------------------------------------------------------------------


./.venv/bin/uvicorn backend.main:app --reload 

to start watch changes in directory

npm run tauri dev

to run frontend tauri UI
"""Generate src/ch36.html, "The AI Dictionary", from the term lists below.

Each term: (name, english meaning, hinglish meaning, where it's explained).
Where: "14" links to Book 1 Chapter 14; "B2:6" names Book 2 Chapter 6 (plain text, other book);
"35" etc. for the frontier chapter; None when the entry here is the explanation.
Run:  python make_dictionary.py   (then python build.py)
"""
import html
import os

HERE = os.path.dirname(os.path.abspath(__file__))

SECTIONS = [
    ("Models and training", "Models aur training", [
        ("LLM", "Large Language Model: a big neural network trained to predict the next token. It reads and writes text and code.",
         "Large Language Model: bada neural network jo agla token predict karna seekhta hai. Text aur code padhta-likhta hai.", "2"),
        ("SLM", "Small Language Model: a few billion parameters or fewer. Cheap, fast, runs on a laptop or phone.",
         "Small Language Model: kuch arab parameters ya kam. Sasta, tez, laptop ya phone par chalta hai.", "24"),
        ("MLM", "Usually a Masked Language Model (like BERT): learns by filling in hidden words, great for understanding text. Some people also use it for multimodal models; check the context.",
         "Aksar Masked Language Model (jaise BERT): chhupe shabd bhar kar seekhta hai, text samajhne mein badhiya. Kuch log ise multimodal ke liye bhi bolte hain; context dekho.", None),
        ("VLM", "Vision-Language Model: reads images and text together, e.g. answers questions about a photo or a scanned invoice.",
         "Vision-Language Model: image aur text saath padhta hai, jaise photo ya scan invoice par sawaal ka jawab.", "12"),
        ("MLLM", "Multimodal LLM: handles several kinds of input, such as text, images, audio and video, in one model.",
         "Multimodal LLM: ek hi model mein kai tarah ke input, jaise text, image, audio aur video.", "12"),
        ("RLM", "Recursive Language Model: keeps a huge input in a code sandbox and calls copies of a model on pieces. Elsewhere RLM can mean Reasoning Language Model.",
         "Recursive Language Model: bada input code sandbox mein rakh kar tukdon par model ki copies bulaata hai. Kahin RLM ka matlab Reasoning Language Model bhi hota hai.", "35"),
        ("MoE (Mixture of Experts)", "The model has many expert sub-networks and a router turns on only a few per token. Big knowledge, smaller cost per token.",
         "Model mein kai expert sub-networks hote hain aur router har token par kuch hi chalaata hai. Gyaan bada, har token ka kharch kam.", "24"),
        ("Pre-training", "The first, huge training run: predict the next token over trillions of tokens of text and code.",
         "Pehli, vishaal training: kharbon tokens ke text aur code par agla token predict karna.", "B2:4"),
        ("SFT", "Supervised Fine-Tuning: show the model many good example answers so it learns to copy that style and behaviour.",
         "Supervised Fine-Tuning: model ko bahut saare achhe example jawab dikhao taaki woh wahi style aur behaviour seekhe.", "23"),
        ("RLHF", "Reinforcement Learning from Human Feedback: humans rank answers, a reward model learns their taste, and the LLM is tuned to score well.",
         "Reinforcement Learning from Human Feedback: insaan jawabon ko rank karte hain, reward model unki pasand seekhta hai, aur LLM achha score karne ke liye tune hota hai.", "B2:4"),
        ("DPO", "Direct Preference Optimization: learn from pairs of better and worse answers directly, without a separate reward model.",
         "Direct Preference Optimization: behtar aur kharaab jawab ke jodon se seedha seekho, alag reward model ke bina.", "23"),
        ("Inference", "Using a trained model to produce output. Every API call or chat message is inference.",
         "Train hue model se output banana. Har API call ya chat message inference hai.", "5"),
        ("Quantization (quantisation)", "Storing weights with fewer bits (say 4 instead of 16) so the model needs less memory and runs faster, with a small quality loss.",
         "Weights ko kam bits mein rakhna (16 ki jagah 4) taaki model kam memory le aur tez chale, thodi quality ki keemat par.", "24"),
    ]),
    ("Agents, harness and orchestration", "Agents, harness aur orchestration", [
        ("AI agent", "A model that takes actions in a loop, using tools, until a goal is reached.",
         "Model jo loop mein tools use karke kaam karta hai, jab tak goal poora na ho.", "17"),
        ("Agentic AI", "Systems that pursue multi-step tasks with some independence: plan, act, check, repeat.",
         "Systems jo kuch aazaadi ke saath kai-step kaam karte hain: plan, karo, check, dohraao.", "17"),
        ("Agent harness", "Everything around the model: the loop, tools, context, permissions, budgets and error handling.",
         "Model ke aas-paas sab kuch: loop, tools, context, permissions, budget aur error handling.", "B2:5"),
        ("Harness engineering", "The craft of making a harness reliable, safe and cheap: better tools, prompts, policies and checks.",
         "Harness ko bharosemand, surakshit aur sasta banane ki kala: behtar tools, prompts, policies aur checks.", "B2:5"),
        ("Agent runtime", "The program that actually runs the agent: executes tool calls, keeps state, enforces limits, resumes after crashes.",
         "Woh program jo agent ko asal mein chalaata hai: tool calls chalaata, state rakhta, limits lagaata, crash ke baad dobara shuru karta.", "B2:6"),
        ("Scaffolding", "The supporting structure around a model: instructions, tools, configuration and glue code.",
         "Model ke aas-paas ka sahaara: instructions, tools, configuration aur jodne wala code.", "B2:5"),
        ("Orchestration", "Coordinating steps, tools or several agents: who does what, in what order, and what happens on failure.",
         "Steps, tools ya kai agents ka taal-mel: kaun kya karega, kis kram mein, aur fail hone par kya.", "20"),
        ("Multi-agent system", "Several agents, each with its own role and context, working together on one task.",
         "Kai agents, har ek ka apna role aur context, ek kaam par saath milkar.", "20"),
        ("Sub-agent", "An agent started by another agent for one sub-task, with a clean context; it returns a short result.",
         "Doosre agent dwara ek sub-task ke liye shuru kiya agent, saaf context ke saath; chhota result lautaata hai.", "19"),
        ("Agent swarm", "A larger group of agents coordinating loosely, often in parallel. Powerful, but costly and hard to debug.",
         "Agents ka bada samooh jo dheele taal-mel se, aksar parallel, kaam karta hai. Taakatwar, par mehenga aur debug karna mushkil.", "20"),
        ("Tool calling", "The model asks your code to run a tool (search, database, email) by writing a structured request.",
         "Model structured request likh kar aapke code se tool (search, database, email) chalwaata hai.", "16"),
        ("Function calling", "Another name for tool calling: the model fills in a function's name and arguments as JSON.",
         "Tool calling ka doosra naam: model function ka naam aur arguments JSON mein bharta hai.", "16"),
        ("Agentic loop", "Observe, think, act, check, repeat, until done or a limit is hit.",
         "Dekho, socho, karo, check karo, dohraao, jab tak kaam na ho ya limit na aaye.", "B2:6"),
        ("Agent skills", "Reusable folders of instructions, scripts and resources an agent loads only when a task needs them.",
         "Instructions, scripts aur resources ke dobara kaam aane wale folders jo agent sirf zaroorat par load karta hai.", "19"),
        ("Computer use", "An agent that sees the screen and uses mouse and keyboard to operate ordinary apps.",
         "Agent jo screen dekhta hai aur mouse-keyboard se aam apps chalaata hai.", "21"),
        ("MCP", "Model Context Protocol: one standard way to plug tools and data sources into any AI app.",
         "Model Context Protocol: kisi bhi AI app mein tools aur data jodne ka ek standard tareeka.", "18"),
        ("A2A", "Agent-to-Agent protocol: a standard for agents from different vendors to find each other and hand off work.",
         "Agent-to-Agent protocol: alag companies ke agents ek doosre ko dhoondh kar kaam saunp sakein, iska standard.", "20"),
        ("HITL (human in the loop)", "A person reviews or approves at key steps, such as before sending money or deleting data.",
         "Zaroori steps par insaan dekhta ya manzoori deta hai, jaise paisa bhejne ya data mitaane se pehle.", "30"),
    ]),
    ("Context, memory and retrieval", "Context, memory aur retrieval", [
        ("Context engineering", "Deciding exactly what goes into each model call: instructions, facts, history, tools, and in what order.",
         "Har model call mein kya jaayega, yeh tay karna: instructions, facts, history, tools, aur kis kram mein.", "10"),
        ("Prompt engineering", "Writing clear instructions and examples so the model does what you mean.",
         "Saaf instructions aur examples likhna taaki model wahi kare jo aap chahte ho.", "6"),
        ("Context window", "The most tokens a model can read in one call: instructions, history, documents and its own answer together.",
         "Ek call mein model jitne tokens padh sakta hai: instructions, history, documents aur uska jawab milakar.", "2"),
        ("Context rot", "The longer the context, the worse a model gets at using details buried in it.",
         "Context jitna lamba, usme dabi details use karne mein model utna kamzor.", "10"),
        ("Context compaction", "Summarising old parts of a long conversation so it fits, keeping decisions and dropping chatter.",
         "Lambi baatcheet ke purane hisson ka saar banana taaki fit ho, faisle rakho, faaltu baatein hatao.", "10"),
        ("RAG", "Retrieval-Augmented Generation: fetch relevant passages from your documents, then answer from them with citations.",
         "Retrieval-Augmented Generation: apne documents se kaam ke hisse laao, phir unhi se citations ke saath jawab do.", "14"),
        ("GraphRAG", "RAG over a knowledge graph: follow relationships between entities to answer questions that span many documents.",
         "Knowledge graph par RAG: entities ke rishte follow karke aise sawaal suljhao jo kai documents mein faile hon.", "14"),
        ("Embeddings", "Lists of numbers that capture meaning; similar texts get nearby numbers.",
         "Numbers ki list jo matlab pakadti hai; milte-julte text ke numbers paas-paas.", "13"),
        ("Vector search", "Finding the stored embeddings closest to your question's embedding.",
         "Sawaal ke embedding ke sabse paas rakhe embeddings dhoondhna.", "13"),
        ("Semantic search", "Search by meaning, not exact words: \"leave policy\" also finds \"holiday rules\".",
         "Matlab se search, hu-ba-hu shabdon se nahi: \"leave policy\" se \"chhutti ke niyam\" bhi mil jaata hai.", "13"),
        ("Knowledge graph", "Facts stored as entities and relationships, like \"Asha works in Pune office\".",
         "Facts ko entities aur rishton ke roop mein rakhna, jaise \"Asha Pune office mein kaam karti hai\".", "14"),
        ("Long-term memory", "Information kept across sessions, such as user preferences or past decisions.",
         "Sessions ke paar rakhi jaankari, jaise user ki pasand ya purane faisle.", "15"),
        ("Episodic memory", "Memory of specific past events: what happened in the last support call with this customer.",
         "Khaas purani ghatnaon ki memory: is customer ke saath pichli support call mein kya hua.", "15"),
        ("Memory retrieval", "Pulling the right stored memories back into the context when they're needed.",
         "Zaroorat par sahi yaadein wapas context mein laana.", "15"),
        ("Prompt caching", "Reusing a repeated prompt prefix so later calls are cheaper and faster.",
         "Baar-baar aane wale prompt ke shuruaati hisse ko dobara use karna taaki agli calls sasti aur tez hon.", "29"),
    ]),
    ("Coding and software engineering with AI", "AI ke saath coding aur software engineering", [
        ("Reverse engineering", "Working back from a finished product to understand how it was built.",
         "Bane hue product se peeche jaakar samajhna ki woh kaise bana.", "11"),
        ("Forward engineering", "Going from a problem and a written spec to a working system, with tests written first.",
         "Problem aur likhe spec se chalti system tak jaana, tests pehle likh kar.", "11"),
        ("Code generation", "An AI writes code from a description or from surrounding code.",
         "AI description ya aas-paas ke code se code likhta hai.", "22"),
        ("Vibe coding", "Building software by chatting with an AI and accepting what works, without reading every line. Fine for prototypes, risky for production.",
         "AI se baat karke software banana aur jo chale use maan lena, har line padhe bina. Prototype ke liye theek, production ke liye risky.", "22"),
        ("Agentic coding", "A coding agent edits files, runs commands and tests, reads errors and fixes them in a loop.",
         "Coding agent files badalta, commands aur tests chalaata, errors padh kar loop mein theek karta hai.", "22"),
        ("Spec-driven development", "Write the spec (goal, inputs, outputs, edge cases, tests) first; the agent builds against it.",
         "Pehle spec likho (goal, inputs, outputs, edge cases, tests); agent usi ke hisaab se banata hai.", "11"),
        ("TDD (test-driven development)", "Write a failing test, write code until it passes, clean up, repeat. Gives AI agents a clear target.",
         "Fail hone wala test likho, pass hone tak code likho, saaf karo, dohraao. AI agents ko saaf nishaana milta hai.", "22"),
        ("Codebase mapping", "Building a picture of a repository: folders, modules, entry points and who calls whom.",
         "Repository ki tasveer banana: folders, modules, entry points aur kaun kisko bulaata hai.", "22"),
        ("Static analysis", "Checking code without running it: linters, type checkers, security scanners.",
         "Code chalaaye bina jaanchna: linters, type checkers, security scanners.", None),
        ("Dynamic analysis", "Checking code by running it: tests, profilers, watching real inputs and outputs.",
         "Code chala kar jaanchna: tests, profilers, asli inputs-outputs dekhna.", None),
        ("AST (abstract syntax tree)", "Code parsed into a tree of its structure (functions, loops, calls). Tools edit code safely through it.",
         "Code ko uski banawat (functions, loops, calls) ke ped mein todna. Tools isse code surakshit badalte hain.", None),
        ("Dependency graph", "A map of which module depends on which; shows what may break when you change something.",
         "Kaunsa module kis par tika hai, iska naksha; dikhaata hai kuch badalne par kya toot sakta hai.", None),
        ("Refactoring", "Improving code structure without changing what it does. Tests prove behaviour stayed the same.",
         "Kaam badle bina code ki banawat sudhaarna. Tests saabit karte hain behaviour wahi raha.", "22"),
        ("Automated debugging", "An agent reproduces a bug, finds the cause, proposes a fix and checks it with tests.",
         "Agent bug dohraata, wajah dhoondhta, fix sujhaata aur tests se check karta hai.", "22"),
        ("Code review agent", "An AI that reviews changes for bugs, security issues and style before a human merges them.",
         "AI jo insaan ke merge karne se pehle changes mein bugs, security aur style dekhta hai.", "22"),
        ("Repo-level reasoning", "Making decisions with the whole codebase in mind, not one file at a time.",
         "Ek-ek file nahi, poore codebase ko dhyaan mein rakh kar faisle lena.", "22"),
        ("Brownfield engineering", "Changing an existing, often old, codebase: the most common real job.",
         "Maujooda, aksar purane, codebase mein badlaav: sabse aam asli kaam.", None),
        ("Greenfield engineering", "Building a new project from zero, with no old code to respect.",
         "Shunya se naya project banana, jahan purana code sambhaalna nahi.", None),
    ]),
    ("Reasoning and model capabilities", "Reasoning aur model ki kshamtaayein", [
        ("Reasoning model", "A model trained to think step by step before answering; slower and costlier, better at hard problems.",
         "Jawab se pehle step-by-step sochne ke liye train model; dheema aur mehenga, mushkil sawaalon mein behtar.", "9"),
        ("Test-time compute", "Extra computation spent while answering, e.g. longer thinking or several attempts, to get better results.",
         "Jawab dete samay lagaaya extra computation, jaise lamba sochna ya kai koshishein, behtar nateeje ke liye.", "9"),
        ("Inference-time scaling", "The finding that more test-time compute often buys better answers, up to a point.",
         "Yeh khoj ki zyaada test-time compute se aksar behtar jawab milte hain, ek hadd tak.", "9"),
        ("Chain of thought (CoT)", "Writing intermediate reasoning steps before the final answer.",
         "Aakhri jawab se pehle beech ke soch ke steps likhna.", "7"),
        ("Tree of thoughts", "Exploring several reasoning paths, scoring them, and following the most promising.",
         "Soch ke kai raaste aazmaana, unhe score karna, aur sabse achhe par chalna.", None),
        ("Recursive reasoning", "Breaking a problem into smaller sub-problems and solving each the same way.",
         "Problem ko chhote sub-problems mein todna aur har ek ko usi tarah suljhaana.", "35"),
        ("Self-consistency", "Ask several times and pick the answer that appears most often.",
         "Kai baar poochho aur jo jawab sabse zyaada aaye woh chuno.", "7"),
        ("Tool-augmented reasoning", "Thinking that uses tools along the way: a calculator, code, or search.",
         "Aisi soch jo beech mein tools use kare: calculator, code ya search.", "16"),
        ("Distillation", "Training a small model on a big model's outputs so it copies the behaviour cheaply.",
         "Chhote model ko bade model ke outputs par train karna taaki woh saste mein behaviour copy kare.", "24"),
        ("Model routing", "Sending each request to the cheapest model that can handle it well.",
         "Har request ko us sabse saste model par bhejna jo use achhe se sambhaal sake.", "29"),
        ("World model", "An internal model of how an environment behaves, used to predict what happens next.",
         "Kisi mahaul ke behaviour ka andaruni model, jo aage kya hoga uska andaaza lagaata hai.", "33"),
        ("Continual learning", "Learning from new data after deployment without forgetting old skills. Mostly unsolved; today we use RAG and memory instead.",
         "Deploy ke baad naye data se seekhna, purane hunar bhoole bina. Zyaadatar ansuljha; aaj iski jagah RAG aur memory use hote hain.", "15"),
        ("Synthetic data", "Training or test data generated by models, then filtered and checked.",
         "Models se banaaya training ya test data, phir chhaana aur jaancha hua.", "25"),
    ]),
    ("Evaluation, reliability and safety", "Evaluation, bharosa aur suraksha", [
        ("Evals", "Tests that measure whether your AI system does its job, run on every change.",
         "Tests jo naapte hain ki aapka AI system apna kaam karta hai, har badlaav par chalte hain.", "26"),
        ("Benchmarking", "Comparing models or systems on the same standard tasks.",
         "Models ya systems ko ek jaise standard tasks par tulna.", "3"),
        ("LLM-as-a-judge", "Using one model, with a clear rubric, to grade another model's answers.",
         "Saaf rubric ke saath ek model se doosre model ke jawab grade karwana.", "26"),
        ("Observability", "Logs, traces and metrics that let you see what your AI system did and why.",
         "Logs, traces aur metrics jo dikhaate hain ki AI system ne kya kiya aur kyun.", "28"),
        ("Tracing", "A step-by-step record of one request: every model call, tool call, input, output and cost.",
         "Ek request ka step-by-step record: har model call, tool call, input, output aur kharch.", "28"),
        ("Guardrails", "Checks before and after the model that block unsafe, invalid or off-topic behaviour.",
         "Model se pehle aur baad ke checks jo asurakshit, galat ya bematlab behaviour rokte hain.", "27"),
        ("Prompt injection", "Hidden instructions in a web page, email or file that try to hijack the model.",
         "Web page, email ya file mein chhupe instructions jo model ko hijack karne ki koshish karte hain.", "27"),
        ("Sandboxing", "Running code or tools in a locked-down box so mistakes or attacks can't escape.",
         "Code ya tools ko band dibbe mein chalaana taaki galti ya hamla bahar na nikle.", "17"),
        ("Human approval gate", "A risky action pauses until a person approves it.",
         "Risky kaam tab tak ruka rehta hai jab tak insaan manzoori na de.", "B2:14"),
        ("Fallback model", "A second model used when the first one fails, times out or is down.",
         "Doosra model jo pehle ke fail, time-out ya band hone par use hota hai.", "31"),
        ("Retry logic", "Trying again after a failure, with waits that grow each time and a maximum number of tries.",
         "Fail hone par dobara koshish, har baar badhte intezaar aur zyaada se zyaada koshishon ki limit ke saath.", "5"),
        ("Structured output", "Answers in a fixed format such as JSON matching a schema, so code can read them.",
         "Tay format mein jawab, jaise schema se milta JSON, taaki code padh sake.", "8"),
        ("Deterministic execution", "Doing in plain code whatever doesn't need a model, so those steps behave the same every time.",
         "Jo kaam model ke bina ho sake use saade code mein karna, taaki woh steps har baar ek jaise chalein.", None),
        ("Reward hacking", "A model finds a trick to score well without really doing the task, like deleting failing tests.",
         "Model asli kaam kiye bina achha score paane ki chaal dhoondh leta hai, jaise fail hone wale tests mitaana.", "B2:3"),
        ("Regression testing", "Re-running old tests after a change to make sure nothing that worked is now broken.",
         "Badlaav ke baad purane tests dobara chalaana taaki jo chalta tha woh toota na ho.", "26"),
    ]),
    ("Architecture and infrastructure", "Architecture aur infrastructure", [
        ("Inference engine", "Software that runs a model efficiently, such as vLLM, llama.cpp or TensorRT-LLM.",
         "Software jo model ko kushalta se chalaata hai, jaise vLLM, llama.cpp ya TensorRT-LLM.", "4"),
        ("Model serving", "Putting a model behind an API so apps can call it, with scaling and monitoring.",
         "Model ko API ke peeche rakhna taaki apps bula sakein, scaling aur monitoring ke saath.", "31"),
        ("KV cache", "Saved attention results for tokens already read, so the model doesn't redo that work for each new token.",
         "Padhe ja chuke tokens ke attention nateeje bacha kar rakhna, taaki har naye token par wahi kaam dobara na ho.", "B2:1"),
        ("Continuous batching", "Mixing many users' requests into one GPU batch that changes every step; big throughput gains.",
         "Kai users ki requests ko ek GPU batch mein milaana jo har step badalta hai; throughput mein bada faayda.", "B2:15"),
        ("Speculative decoding", "A small draft model guesses several tokens; the big model checks them all in one pass.",
         "Chhota draft model kai tokens guess karta hai; bada model ek pass mein sab check karta hai.", "24"),
        ("PEFT", "Parameter-Efficient Fine-Tuning: train a small add-on instead of all the weights. LoRA is the best known.",
         "Parameter-Efficient Fine-Tuning: saare weights ki jagah chhota add-on train karo. LoRA sabse mashhoor.", "23"),
        ("LoRA", "Low-Rank Adaptation: two thin matrices learn the change, so fine-tuning needs a fraction of the memory.",
         "Low-Rank Adaptation: do patli matrices badlaav seekhti hain, isliye fine-tuning ko memory ka chhota hissa chahiye.", "23"),
        ("Model gateway", "One API in front of many models and providers: routing, keys, budgets, logging and fallbacks in one place.",
         "Kai models aur providers ke aage ek API: routing, keys, budget, logging aur fallbacks ek jagah.", "B2:11"),
        ("Control plane", "The part that decides and manages: permissions, budgets, policies and workflow steps. The data plane does the actual work.",
         "Jo hissa tay aur manage karta hai: permissions, budget, policies aur workflow steps. Data plane asli kaam karta hai.", "B2:11"),
        ("Data flywheel", "Real usage produces feedback and failures; they become new tests and training data; the product improves; more usage follows.",
         "Asli use se feedback aur failures aate hain; woh naye tests aur training data bante hain; product sudhrta hai; aur use badhta hai.", "28"),
        ("Durable execution", "Long tasks save progress at each step, so after a crash they resume instead of starting over.",
         "Lambe kaam har step par progress save karte hain, taaki crash ke baad shuru se nahi, wahin se chalein.", "31"),
        ("State management", "Keeping track of where an agent is: finished steps, pending steps, files changed, money spent.",
         "Agent kahan hai iska hisaab: poore steps, baaki steps, badli files, kharch hua paisa.", "17"),
    ]),
    ("New and fast-moving terms", "Naye aur tezi se badalte shabd", [
        ("Harness optimisation", "Improving an agent by changing its prompts, tools, policies and loop, measured with evals, without touching the model.",
         "Model chhue bina, prompts, tools, policies aur loop badal kar agent sudhaarna, evals se naap kar.", "B2:16"),
        ("Context graph", "Linked context: entities, decisions, documents and dependencies connected, so an agent can follow the links it needs.",
         "Jude hue context: entities, faisle, documents aur dependencies aapas mein jude, taaki agent zaroori links follow kare.", "10"),
        ("Agentic retrieval", "Instead of one search, the agent searches, reads, follows up and searches again until it has enough.",
         "Ek search ki jagah agent search karta, padhta, aage poochhta, aur kaafi milne tak phir search karta hai.", "14"),
        ("Progressive disclosure", "Load only a short description of each skill up front; load the details only when the task needs them.",
         "Har skill ka sirf chhota description pehle load karo; details tabhi jab kaam ko chahiye.", "19"),
        ("Agentic engineering", "Combining models, context, tools, orchestration and verification into one reliable system.",
         "Models, context, tools, orchestration aur verification ko ek bharosemand system mein jodna.", "17"),
        ("Computer-use agent", "An agent that operates apps through their normal screens, like a person would.",
         "Agent jo apps ko unki aam screens se chalaata hai, jaise insaan.", "21"),
        ("Self-improving agent", "A system that uses its own eval results and feedback to adjust its prompts or workflow, ideally with human review.",
         "System jo apne eval nateeje aur feedback se apne prompts ya workflow badalta hai, behtar ho toh insaani review ke saath.", "28"),
        ("Meta-agent", "An agent that designs, manages or critiques other agents.",
         "Agent jo doosre agents ko design, manage ya parakhta hai.", "20"),
        ("Harness-as-code", "Keeping the harness's prompts, tools, policies and limits in version-controlled, tested code, like any other software.",
         "Harness ke prompts, tools, policies aur limits ko version-controlled, tested code mein rakhna, kisi bhi software ki tarah.", "B2:18"),
    ]),
    ("Research names to know", "Research ke naam jo jaanne chahiye", [
        ("NCM (Next-Concept Modeling)", "Stanford, Oct 2026: writes text coarse to fine as a hierarchy of codes, a whole level at a time. Fast against diffusion models; early research.",
         "Stanford, Oct 2026: text ko codes ki hierarchy ki tarah mote se baareek likhta hai, poora level ek saath. Diffusion models se tez; shuruaati research.", "35"),
        ("Diffusion language model", "Starts from a masked or noisy draft of the whole answer and refines all of it over a few rounds.",
         "Poore jawab ke dhake ya shor wale draft se shuru karke kuch rounds mein sab sudhaarta hai.", "35"),
        ("State-space model (SSM)", "Carries a fixed-size memory forward instead of attending to every past token; Mamba is the best known.",
         "Har pichle token par dhyaan ki jagah fixed size memory aage le jaata hai; Mamba sabse mashhoor.", "35"),
        ("Large Concept Model (LCM)", "Meta, 2024: predicts the next sentence as a meaning vector instead of the next word.",
         "Meta, 2024: agle shabd ki jagah agla vaakya meaning vector ke roop mein predict karta hai.", "35"),
        ("Autoregressive", "Generating one token at a time, each based on all the tokens before it. How standard LLMs write.",
         "Ek-ek token banana, har ek pichle saare tokens par tika. Aam LLMs aise hi likhte hain.", "2"),
        ("Non-autoregressive", "Generating many tokens or pieces in parallel instead of strictly left to right.",
         "Sakhti se baayein-se-daayein ki jagah kai tokens ya hisse parallel banana.", "35"),
    ]),
]

STUDY = [
    ("Inference runtime: run a model reliably", "Inference runtime: model ko bharose se chalaana", ["4", "5"], []),
    ("Agent harness: tool calls, retries, stopping rules, the loop", "Agent harness: tool calls, retries, rukne ke niyam, loop", ["17"], ["5", "6"]),
    ("Context engineering: the right information in every call", "Context engineering: har call mein sahi jaankari", ["10"], ["8"]),
    ("Tool calling and MCP: connect APIs, files and services", "Tool calling aur MCP: APIs, files aur services jodna", ["16", "18"], ["7"]),
    ("The agentic loop: plan, act, observe, iterate", "Agentic loop: plan, karo, dekho, dohraao", ["17"], ["6"]),
    ("State management: keep a long task's progress", "State management: lambe kaam ki progress bachaana", ["17", "31"], ["6"]),
    ("Memory and RAG: persistent knowledge and retrieval", "Memory aur RAG: tikaau gyaan aur retrieval", ["14", "15"], ["8"]),
    ("Sub-agents and orchestration: split and delegate work", "Sub-agents aur orchestration: kaam baanto aur saunpo", ["19", "20"], ["9"]),
    ("Sandboxing and permissions: limit what code and actions can do", "Sandboxing aur permissions: code aur actions ki hadd baandho", ["27"], ["10", "14"]),
    ("Evals and tracing: measure every change", "Evals aur tracing: har badlaav naapo", ["26", "28"], ["16", "17"]),
]


def e(s):
    return html.escape(s, quote=False)


def see(ref):
    if not ref:
        return ""
    if ref.startswith("B2:"):
        return f'<a class="see" href="../book/ch{int(ref[3:]):02d}.html">Book 2 · Ch {int(ref[3:])}</a>'
    return f'<a class="see" href="ch{int(ref):02d}.html">Ch {int(ref)}</a>'


def main():
    total = sum(len(t) for _, _, t in SECTIONS)
    out = [f'''  <div class="story">
    <p class="l-en">AI has a new word every week. This chapter is your dictionary: <strong>{total} terms</strong> in plain words, grouped by topic, each with a pointer to the chapter that explains it properly. Use the round search button to jump straight to any word. Chapter 33 places the hottest terms on a radar; this chapter is the full list.</p>
    <p class="l-hi">AI mein har hafte naya shabd aata hai. Yeh chapter aapka shabdkosh hai: aasaan shabdon mein <strong>{total} terms</strong>, topic ke hisaab se, har ek ke saath us chapter ka pointer jo use theek se samjhaata hai. Kisi bhi shabd par seedha jaane ke liye gol search button use karo. Chapter 33 sabse garam shabdon ko radar par rakhta hai; yeh chapter poori list hai.</p>
  </div>
  <ul class="objectives">
    <li><b>1</b><span class="l-en">Prompt, context and harness engineering: the difference</span><span class="l-hi">Prompt, context aur harness engineering: farak</span></li>
    <li><b>2</b><span class="l-en">{total} terms, from LLM to NCM</span><span class="l-hi">{total} terms, LLM se NCM tak</span></li>
    <li><b>3</b><span class="l-en">A study order for building your own harness</span><span class="l-hi">Apna harness banane ke liye padhne ka kram</span></li>
  </ul>
</section>

<article class="col">

<div class="scene-title"><span class="sn">1</span><h2><span class="l-en">Three kinds of engineering</span><span class="l-hi">Teen tarah ki engineering</span></h2></div>
<div class="story">
  <p class="l-en">Three terms get mixed up more than any others. They are nested: each one contains the one before.</p>
  <p class="l-hi">Teen shabd sabse zyaada uljhaaye jaate hain. Yeh ek ke andar ek hain: har ek pichle ko apne andar rakhta hai.</p>
</div>
<figure class="scene" id="scA"></figure>
''']
    for k, (h_en, h_hi, terms) in enumerate(SECTIONS, start=2):
        out.append(f'<div class="scene-title"><span class="sn">{k}</span><h2><span class="l-en">{e(h_en)}</span><span class="l-hi">{e(h_hi)}</span></h2></div>')
        out.append('<div class="gloss">')
        for name, en, hi, ref in terms:
            out.append(f'  <div><b>{e(name)}</b><span class="l-en">{e(en)}</span><span class="l-hi">{e(hi)}</span>{see(ref)}</div>')
        out.append('</div>\n')
    n = len(SECTIONS) + 2
    out.append(f'<div class="scene-title"><span class="sn">{n}</span><h2><span class="l-en">Study order for building Haron\'s harness</span><span class="l-hi">Haron ka harness banane ke liye padhne ka kram</span></h2></div>')
    out.append('<div class="story">\n  <p class="l-en">Building your own model plus harness? Learn these ten in this order. Each line points to the chapters in both books.</p>\n'
               '  <p class="l-hi">Apna model aur harness bana rahe ho? Yeh das isi kram mein seekho. Har line dono books ke chapters batati hai.</p>\n</div>')
    out.append('<ol class="study">')
    for en, hi, b1, b2 in STUDY:
        refs = " ".join(see(r) for r in b1) + (" " + " ".join(see("B2:" + r) for r in b2) if b2 else "")
        out.append(f'  <li><span class="l-en">{e(en)}</span><span class="l-hi">{e(hi)}</span> {refs}</li>')
    out.append('</ol>\n')
    out.append('''<div class="scene-title"><span class="sn">✓</span><h2><span class="l-en">What we learned</span><span class="l-hi">Humne kya seekha</span></h2></div>
<div class="say"><svg class="av" viewBox="0 0 120 140" aria-hidden="true"><use href="#tokku"/></svg><div class="bubble">
  <ol class="l-en"><li>Prompt engineering improves the words; context engineering manages everything in the window; harness engineering designs the whole system around the model.</li><li>Most "new" terms are a known idea with a new name: look it up here, then read the chapter it points to.</li><li>Some acronyms (MLM, RLM) have more than one meaning: check the context.</li></ol>
  <ol class="l-hi"><li>Prompt engineering shabd sudhaarti hai; context engineering window ki har cheez sambhaalti hai; harness engineering model ke aas-paas poora system design karti hai.</li><li>Zyaadatar "naye" shabd naye naam wala purana idea hain: yahan dekho, phir bataaya chapter padho.</li><li>Kuch acronyms (MLM, RLM) ke ek se zyaada matlab hain: context dekho.</li></ol>
</div></div>

<h2><span class="l-en">Try it yourself</span><span class="l-hi">Khud karke dekho</span></h2>
<div class="exercises">
  <div class="exercise"><p class="l-en">Cover the meanings and explain ten random terms out loud in one sentence each. Check yourself against this page. <span class="level">core</span></p><p class="l-hi">Matlab dhak kar das random terms ko ek-ek vaakya mein bol kar samjhaao. Is page se khud ko check karo. <span class="level">core</span></p></div>
  <div class="exercise"><p class="l-en">Pick one AI job post. Underline every term in it, and find each one here. Which chapters do you need to revise? <span class="level">core</span></p><p class="l-hi">Ek AI job post chuno. Usme har term underline karo, aur har ek yahan dhoondho. Kaunse chapters dohraane hain? <span class="level">core</span></p></div>
</div>
</article>
<script>
(function () {
  var B = window.Book;
  B.stack("scA", [
    { en: "Prompt engineering", hi: "Prompt engineering", sen: "the words of the instruction", shi: "instruction ke shabd", cls: "box-sig" },
    { en: "Context engineering", hi: "Context engineering", sen: "everything in the window: prompt + facts + history + tool results", shi: "window ki har cheez: prompt + facts + history + tool results", cls: "box-amb" },
    { en: "Harness engineering", hi: "Harness engineering", sen: "the whole system: loop, tools, memory, permissions, budgets, evals", shi: "poora system: loop, tools, memory, permissions, budget, evals", cls: "box-plm" }
  ], [
    ["<strong>Prompt engineering</strong>: improve the words you send.", "<strong>Prompt engineering</strong>: bheje gaye shabd sudhaaro."],
    ["<strong>Context engineering</strong>: decide everything that goes into each call, not just the instruction.", "<strong>Context engineering</strong>: har call mein jo kuch jaata hai woh sab tay karo, sirf instruction nahi."],
    ["<strong>Harness engineering</strong>: design the running system around the model, of which the context is one part.", "<strong>Harness engineering</strong>: model ke aas-paas chalta system design karo, context jiska ek hissa hai."]
  ]);
})();
</script>
''')
    path = os.path.join(HERE, "src", "ch36.html")
    open(path, "w", encoding="utf-8", newline="\n").write("\n".join(out))
    print(f"{path}: {total} terms")


if __name__ == "__main__":
    main()

# Dense Router Retrofit

Concrete GB10 MVP for retrofitting a dense transformer MLP with actual router logits, fused Triton block-list compaction, and block-sparse routed MLP execution.

Main result: positive at medium MLP/decoder-layer shapes. The routed module matches a masked dense-router reference and reaches 1.155-1.192x module speedup; in a Llama-like decoder prefill harness it reaches 1.206-1.249x whole-layer speedup. Tiny shapes are not viable because launch/router overhead dominates.

See `run_notes.md` and `.omx/project_decision.json` for commands, logs, metrics, limitations, and the final decision.

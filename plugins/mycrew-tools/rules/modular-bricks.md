# Build modular bricks — small single-purpose units, then compose

Code turns into one growing blob when each new need is bolted onto the last function. It does the job
once and resists every change after. Build the opposite: small units that each do one thing, expose a
narrow interface, and combine into the whole.

- **One responsibility per unit.** A function or module does a single job. If you can only describe it
  with "and", it's two units — split it.
- **Compose, don't accrete.** Assemble behaviour from small bricks rather than growing one function to
  cover every case. Each brick should be usable elsewhere, not welded to this one caller.
- **Narrow, stable interfaces.** Expose the least a caller needs and keep the messy detail inside. A
  consumer should work against the interface without reading the internals.
- **Depend on abstractions, not concretions.** Point at an interface, not a concrete implementation, so
  pieces stay substitutable and open to extension without editing what already works.

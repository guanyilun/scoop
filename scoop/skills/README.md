# Skills

A skill is knowledge in markdown for SCOOP's agents: what a survey or archive holds,
which versions and files are official, how to query it, its gotchas, the defaults an
agent picks and what it tells the user, and how to cite it. Skills hold no code; tools
do the computing.

Every agent (the chat agent, the data agent, the proper-motion agent) gets the same
`read_skill` tool and a list of the skills in its instructions (path, status and the
`description` from the front matter), and reads one in full when a request needs it.
[index.md](index.md) groups them by topic.

## Skill, tool or sub-agent?
- **Skill**: domain knowledge an agent would otherwise rediscover or guess. Start here.
- **Tool**: a computation that must be exact and repeatable (a query, a fit, a cutout).
- **Sub-agent**: only when the work takes many steps with a large specialised toolset
  that would clutter the chat agent, or runs under a different contract (the exoplanet
  agent's checked claims). Its prompt says how to use its tools; its domain knowledge
  lives in a skill it reads (the proper-motion agent reads astrometry/proper_motions).

## Writing one
Follow [meta/new_survey_skill.md](meta/new_survey_skill.md). The front matter needs
`name`, a `description` that says when to read it (agents choose by it), `status`
(`draft` until a person reviews it) and `sources_checked` (dated). Notes for developers
about SCOOP's own code belong in `docs/`, not here.

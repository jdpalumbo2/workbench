# Design plan template (step 2)

Two files, both short, both written before any component. The plan is prose the tokens cannot
carry: tokens store values, the plan stores WHY (Stitch's DESIGN.md split; see research memo §2).

## The plan (15 lines or fewer, one per slot; drop a slot only with a stated reason)

```
Subject/job:      <what this surface is, and the single thing its reader does with it>
Register:         operate | read | persuade | experience
Direction:        <the picked direction's name and spec line, verbatim>
Refused defaults: <each default this rejects, and what replaces it>
Palette stance:   <the roles and the relationship, not the hexes (tokens hold those)>
Type character:   <faces, scale ratio, what the display face is FOR>
Hierarchy stance: <what the eye hits first, second, third, and why>
Density:          <airy | working | dense, and what earns it>
Shape/elevation:  <radius stance, shadow stance, one sentence>
Motion stance:    <durations, easing, what moves and what never does>
Layout:           <ASCII sketch of the hero screen's regions>
Signature:        <the ONE element only this subject would have>
Sample data:      <the rule for real-looking labelled data; never lorem, never "Item 1">
```

## tokens.css skeleton

```css
:root {
  /* 6-10 color roles, always surface/on-surface pairs */
  --surface: ;        --on-surface: ;
  --surface-raised: ; --on-surface-raised: ;
  --accent: ;         --on-accent: ;
  --muted: ;          --status-ok: ; --status-warn: ; --status-bad: ;
  /* type: two faces, one scale */
  --face-display: ;   --face-body: ;
  --scale-ratio: ;    --weight-body: ; --weight-strong: ;
  --tracking-caps: ;  --leading-body: ;
  /* rhythm */
  --unit: 8px;        --density: 1;
  --radius: ;         --elevation-1: ;
  --dur: ;            --ease: ;
}
```

Dark and light derive from one set via `light-dark()` + `color-scheme` where Baseline allows;
dark surface is a deep gray, never #000; status hues desaturate in dark.

## Enforcement

Components consume only tokens. The rogue-literal check (step 4, round 0) is a grep over the
files this work touched for hex literals, px font sizes, and named colors outside tokens.css;
models will not self-enforce this (DesignBench: 0.24% component reuse). Advisory thresholds:
distinct font sizes 5 or fewer, weights 3 or fewer, spacing on the unit scale, every color from
the declared palette.

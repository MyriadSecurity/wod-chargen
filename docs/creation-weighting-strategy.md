# How characters are built (LoTN V5)

How the tool assigns creation dots and spends XP. Assumes LoTN familiarity. Formulas where useful.

In-app: [How Characters Are Built](../index.html#strategy). Visual biases: [Weight Map](../index.html#weights).

## Overview

Pick archetype, subtype, clan, predator. Hard rules first — generation caps, prerequisites, costs. Weights break ties among legal options.

## Build order

1. Archetype + subtype  
2. Clan  
3. Predator type  
4. Creation (attrs, skills, disciplines, backgrounds)  
5. Predator package  
6. Step 8 (optional)  
7. Thin-blood pairs (thin blood only)  
8. XP  
9. Loresheet benefits (free; needs purchased dots)  

## Bias layers

```
bias = explicit override
    OR tag-affinity product
    OR 1.0
final = clamp(bias, 0.05 … 3.0)
```

```
merged profile = archetype + subtype
              → clan (discipline floor ≥ 0.85, alternates)
              → predator multipliers
```

| Layer | Effect |
|-------|--------|
| Archetype | Default trait biases |
| Subtype | Deltas on parent |
| Clan | In-clan discipline floor; alternates |
| Predator | Pool and package multipliers |

## Creation

### Attributes, skills, disciplines

One free chunk per attribute/skill. +4 before +1.

```
pick weight = bias × (max − current)
+4 → ×2.0   +3 → ×1.3   +1/+2 → ×1.15
```

In-clan disciplines only for free dots. Off-clan signatures at XP: ×0.6 weight.

### Backgrounds

```
weight = creation_bias[type] × archetype × predator
```

Modifier chance ~12–35%; ~70% for 1–3 free disadvantages; 1 disadv → 1 adv.

### Step 8

Optional. Up to 10 merit dots from flaw credit.

```
merit weight = group weight × merit bias
```

## Experience

Blood Potency to generation minimum first.

### Three-pass pick

```
macro weight = target share × avg group weight × deficit boost
group weight = archetype group weight
trait score = bias × clan factor × efficiency × random(0…1)
```

```
deficit = (expected − actual) / budget
boost = clamp(1 + 4.5 × deficit, 0.25 … 4.0)
```

### Target mix (±18% jitter per character)

| Area | Share |
|------|-------|
| Disciplines | 34% |
| Attributes | 20% |
| Skills | 20% |
| Backgrounds | 12% |
| Merits / loresheets / extra BP | 14% |

### Efficiency (selected)

| Buy | × |
|-----|---|
| •••• → ••••• | 5.0 |
| none → • | 2.5 |
| none → •• | 1.6 |
| none → ••• | 0.1 |

Loresheets: 0→1 ×3.2, 1→2 ×3.6, 2→3 ×2.8.

## Same seed, same sheet

```
seed + wizard options + generator version → sheet
```

## Maintainers

[data paths and bias ranges](archetype-weight-guidelines.md)

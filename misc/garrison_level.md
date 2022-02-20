# Garrison Levels

## Short Description

## Advantages

### Commander

- less busy-work, click once per location instead of 4+ times

- easier to visualize on the map

- less confusion i.e. `What is better to use a Rifleman or a Team-Leader?`

- lower learning curve

### Players

- not a lot will change for them

- less frustration that commander set "bad" garrison.
    ****CAVE:****
    > ***Weak Argument**, seldom ever saw it happen or saw complaining happen*

### Server

- prevention of garrison spam could lead to better performance

- calculation of attack targets could become easier

### Dev

- removal of UI elements simplifies code and makes it more maintainable

- easier to balance against finite levels vs analog garrison strength

## Implementation

### Required Changes

#### Save-Data Changes

#### UI Changes

#### Code Changes

### Gameplay

### Configurable Parts

- deactivation of the garrison-level-system and fallback to the old system. In this case the level of the Location would be stored as `-1`

- max-level vs unlimited-level. Unlimited would just add a fixed array of soldiers to that location after it reached a level above the defined levels. Max would just not let the Commander add more levels.

### Examples

#### Levels

##### Level `-1`

Indicates that the garrison-level-system is deactivated. see [Configurable Parts](#Configurable-Parts)

##### Level `0`

Indicates no garrison

##### Level `1`

```mermaid
graph
    LEADER1[[Team-Leader]] --- UNITS1[ ]
    UNITS1 --> MEDIC1([Medic])
    UNITS1 --> RIFLEMAN1[Rifleman]
    UNITS1 --> RIFLEMAN2[Rifleman]

    style UNITS1 fill:#FFFFFF, stroke:#FFFFFF;
```

##### Level `2`

```mermaid
graph
    subgraph lvl1
    LEADER1[[Team-Leader]] === UNITS1[ ]
    UNITS1 --> MEDIC1([Medic])
    UNITS1 --> RIFLEMAN1[Rifleman]
    UNITS1 --> RIFLEMAN2[Rifleman]
    end

    subgraph lvl2
    UNITS2[ ] -.-> UNITS1
    UNITS2 --> AT1[/AT-Soldier\]
    UNITS2 --> AT2[/AT-Soldier\]
    UNITS2 --> AUTORIFLEMAN1>Auto-Rifleman]
    UNITS2 --> AUTORIFLEMAN2>Auto-Rifleman]
    end
    style UNITS1 fill:#FFFFFF, stroke:#FFFFFF;
    style UNITS2 fill:#FFFFFF, stroke:#FFFFFF;
```

##### Level `3`

```mermaid
graph

    subgraph lvl1
    LEADER1[[Team-Leader]] === UNITS1[ ]
    UNITS1 --> MEDIC1([Medic])
    UNITS1 --> RIFLEMAN1[Rifleman]
    UNITS1 --> RIFLEMAN2[Rifleman]
    end

    subgraph lvl2
    UNITS2[ ] -.- LEADER1
    UNITS2 --> AT1[/AT-Soldier\]
    UNITS2 --> AT2[/AT-Soldier\]
    UNITS2 --> AUTORIFLEMAN1>Auto-Rifleman]
    UNITS2 --> AUTORIFLEMAN2>Auto-Rifleman]
    end

    subgraph lvl3
    UNITS3[ ] -.- LEADER1
    UNITS3 --> SNIPER1{Marksman}
    UNITS3 --> SNIPER2{Marksman}
    UNITS3 --> MEDIC2([Medic])
    UNITS3 --> LEADER2[[Team-Leader]]
    end


    style UNITS1 fill:#FFFFFF, stroke:#FFFFFF;
    style UNITS2 fill:#FFFFFF, stroke:#FFFFFF;
    style UNITS3 fill:#FFFFFF, stroke:#FFFFFF;
```

##### Level `4`

```mermaid
graph

    subgraph lvl1
    LEADER1[[Team-Leader]] === UNITS1[ ]
    UNITS1 --> MEDIC1([Medic])
    UNITS1 --> RIFLEMAN1[Rifleman]
    UNITS1 --> RIFLEMAN2[Rifleman]
    end

    subgraph lvl2
    UNITS2[ ] -.- LEADER1
    UNITS2 --> AT1[/AT-Soldier\]
    UNITS2 --> AT2[/AT-Soldier\]
    UNITS2 --> AUTORIFLEMAN1>Auto-Rifleman]
    UNITS2 --> AUTORIFLEMAN2>Auto-Rifleman]
    end

    subgraph lvl3
    UNITS3[ ] -.- LEADER1
    UNITS3 --> SNIPER1{Marksman}
    UNITS3 --> SNIPER2{Marksman}
    UNITS3 --> MEDIC2([Medic])
    UNITS3 --> LEADER2[[Team-Leader]]
    end

    subgraph lvl4
    UNITS4[ ] -.- LEADER1
    UNITS4 --> AT3[/AT-Soldier\]
    UNITS4 --> AT4[/AT-Soldier\]
    UNITS4 --> AT5[/AT-Soldier\]
    UNITS4 --> AT6[/AT-Soldier\]
    end

    style UNITS1 fill:#FFFFFF, stroke:#FFFFFF;
    style UNITS2 fill:#FFFFFF, stroke:#FFFFFF;
    style UNITS3 fill:#FFFFFF, stroke:#FFFFFF;
    style UNITS4 fill:#FFFFFF, stroke:#FFFFFF;
```

##### Level `4+`

```mermaid
graph
    UNITS[+] --> UNIT[ ]
    UNIT -->  AUTORIFLEMAN1>Auto-Rifleman]
    UNIT --> AUTORIFLEMAN2>Auto-Rifleman]
    UNIT --> RIFLEMAN1[Rifleman]
    UNIT --> RIFLEMAN2[Rifleman]

    style UNIT fill:#FFFFFF, stroke:#FFFFFF;
    style UNIT fill:#FFFFFF, stroke:#FFFFFF;

```

## Further Ideas

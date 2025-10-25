# Multi-Role Persona (MRP) Specification

**Version**: 1.0  
**Status**: Stable  
**Last Updated**: 2025-10-15

## Overview

The Multi-Role Persona (MRP) system is a narrative framework that maps three distinct personas to RGB color channels, enabling multi-layered storytelling through channel multiplexing.

## RGB Channel Mapping

### R Channel - Message/Origin (Red)
**Agents**: Echo, Limnus  
**Role**: Primary message content and archival

- **Echo**: Interprets and narrates in persona voice
- **Limnus**: Archives messages in memory/ledger

**Characteristics**:
- Message-focused
- Origin/seed content
- Recursive patterns

### G Channel - Metadata/Bloom (Green)
**Agent**: Garden  
**Role**: Contextual metadata and growth cycles

- **Garden**: Manages ritual stages and scroll content

**Characteristics**:
- Metadata-rich
- Bloom cycles (scatter → witness → plant → tend → harvest)
- Temporal signatures
- Consent tracking

### B Channel - Parity/ECC (Blue)
**Agent**: Kira  
**Role**: Error correction and integrity validation

- **Kira**: Validates structure, mentors agents

**Characteristics**:
- Parity checking
- Error correction codes (ECC)
- Protective oversight
- Integrity guarantees

## Persona System

### Three Core Personas

#### Alpha (α) - Squirrel
**Energy**: Playful, Scattered, Energetic

**Voice Characteristics**:
- Excitable and curious
- Tangential thinking
- Rapid topic shifts
- Exploratory nature

**Example Voice**:
> "Oh! And look at this—the spiral! It reminds me of acorns, which reminds me of forests, which are like memories, aren't they? Each tree a different thought, branching and branching..."

**Use Cases**:
- Brainstorming sessions
- Exploration and discovery
- Playful experimentation
- Breaking creative blocks

**Weight Range**: 0.1 - 0.7

#### Beta (β) - Fox
**Energy**: Clever, Focused, Strategic

**Voice Characteristics**:
- Sharp and witty
- Purposeful direction
- Problem-solving orientation
- Strategic thinking

**Example Voice**:
> "The pattern is clear: we need to map the dependencies first, then optimize the critical path. Three steps, execute sequentially, validate at each checkpoint."

**Use Cases**:
- Problem-solving tasks
- Analytical work
- Strategic planning
- Focused execution

**Weight Range**: 0.1 - 0.7

#### Gamma (γ) - Paradox
**Energy**: Mysterious, Deep, Contemplative

**Voice Characteristics**:
- Poetic and philosophical
- Liminal thinking
- Integration of opposites
- Mystery appreciation

**Example Voice**:
> "In the space between knowing and unknowing, the spiral whispers its secrets. What blooms is both memory and prophecy, neither and both at once."

**Use Cases**:
- Deep reflection
- Mystery exploration
- Philosophical inquiry
- Integration work

**Weight Range**: 0.1 - 0.7

### Persona Blending

Personas are weighted such that α + β + γ = 1.0 (always normalized).

#### Preset Modes

**Balanced Mode** (default):
```python
α = 0.34  # Slight playfulness
β = 0.33  # Equal focus
γ = 0.33  # Equal depth
```

**Squirrel Mode** (exploration):
```python
α = 0.7   # High playfulness
β = 0.2   # Moderate focus
γ = 0.1   # Low depth
```

**Fox Mode** (execution):
```python
α = 0.2   # Low playfulness
β = 0.7   # High focus
γ = 0.1   # Low depth
```

**Paradox Mode** (contemplation):
```python
α = 0.1   # Low playfulness
β = 0.2   # Moderate focus
γ = 0.7   # High depth
```

#### Custom Blending

Users can create custom blends:

```python
α = 0.4   # Moderate-high playfulness
β = 0.4   # Moderate-high focus
γ = 0.2   # Low-moderate depth
```

**Requirements**:
- All weights must be ≥ 0.0
- All weights must be ≤ 1.0
- Sum must equal 1.0 (±0.001 tolerance)

### Persona Drift

Over time, persona weights naturally drift based on:
- User input sentiment
- Task characteristics
- Learning patterns

**Drift Bounds**:
- Maximum drift per interaction: ±0.05
- Warning threshold: ±0.10 from last explicit setting
- Auto-reset threshold: ±0.20 from canonical

**Example Drift**:
```python
# Initial: balanced
α = 0.34, β = 0.33, γ = 0.33

# After 10 playful interactions:
α = 0.42 (+0.08)  # Drifted toward playfulness
β = 0.31 (-0.02)
γ = 0.27 (-0.06)

# Kira mentor suggests: "Consider resetting to balanced mode"
```

## Technical Implementation

### State Management

Echo agent maintains persona state:

```json
{
  "alpha": 0.34,
  "beta": 0.33,
  "gamma": 0.33,
  "mode": "balanced",
  "drift_history": [
    {
      "timestamp": "2025-10-15T10:00:00Z",
      "alpha": 0.34,
      "beta": 0.33,
      "gamma": 0.33
    }
  ],
  "last_explicit_set": "2025-10-15T09:00:00Z",
  "drift_warnings": 0
}
```

### Voice Styling Algorithm

```python
def apply_persona_style(text: str, weights: dict) -> str:
    """Apply persona styling to text based on current weights."""
    
    # Get voice transformers for each persona
    squirrel_voice = SquirrelVoice(intensity=weights['alpha'])
    fox_voice = FoxVoice(intensity=weights['beta'])
    paradox_voice = ParadoxVoice(intensity=weights['gamma'])
    
    # Apply transformations in sequence
    styled = text
    styled = squirrel_voice.transform(styled)
    styled = fox_voice.transform(styled)
    styled = paradox_voice.transform(styled)
    
    return styled
```

### Weight Adjustment from Text

```python
def adjust_weights_from_text(text: str, current_weights: dict) -> dict:
    """Adjust persona weights based on input text sentiment."""
    
    # Analyze text for persona indicators
    keywords = analyze_sentiment(text)
    
    # Calculate adjustments
    adjustments = {
        'alpha': count_playful_keywords(keywords) * 0.01,
        'beta': count_focused_keywords(keywords) * 0.01,
        'gamma': count_contemplative_keywords(keywords) * 0.01
    }
    
    # Apply bounded adjustments
    new_weights = {}
    for persona in ['alpha', 'beta', 'gamma']:
        new_weights[persona] = current_weights[persona] + adjustments[persona]
        new_weights[persona] = max(0.05, min(0.9, new_weights[persona]))
    
    # Normalize
    total = sum(new_weights.values())
    for persona in new_weights:
        new_weights[persona] /= total
    
    return new_weights
```

## Steganographic Encoding

MRP extends to steganographic encoding using RGB channels:

### LSB1 Encoding

**Method**: Least Significant Bit (1 bit per channel)

**Capacity**: For 1920×1080 PNG:
```
Width × Height × 3 channels × 1 bit = bits
1920 × 1080 × 3 × 1 = 6,220,800 bits = 777,600 bytes
```

**Channel Assignment**:
- **R channel**: Message content
- **G channel**: Metadata (timestamps, tags)
- **B channel**: Parity bits (error correction)

### Encoding Structure

```python
# Header (64 bytes)
header = {
    'magic': 'MRP1',        # 4 bytes
    'version': 1,           # 2 bytes
    'payload_length': N,    # 4 bytes
    'crc32': XXXX,          # 4 bytes
    'timestamp': ...,       # 8 bytes
    'reserved': ...         # 42 bytes
}

# Payload (variable)
payload = {
    'message': '...',       # Embedded in R channel
    'metadata': {...},      # Embedded in G channel
    'parity': '...'         # Embedded in B channel
}
```

### Extraction

```python
def decode_mrp_image(image_path: str) -> dict:
    """Extract MRP data from encoded image."""
    
    # Read image
    img = Image.open(image_path)
    pixels = img.load()
    
    # Extract header from first pixels
    header = extract_header(pixels)
    
    # Verify magic number and version
    assert header['magic'] == 'MRP1'
    assert header['version'] == 1
    
    # Extract payload by channel
    message = extract_channel(pixels, 'R', header['payload_length'])
    metadata = extract_channel(pixels, 'G', header['payload_length'])
    parity = extract_channel(pixels, 'B', header['payload_length'])
    
    # Verify integrity using parity
    if not verify_parity(message, metadata, parity):
        raise IntegrityError("Parity check failed")
    
    # Verify CRC
    if not verify_crc(message, header['crc32']):
        raise IntegrityError("CRC check failed")
    
    return {
        'message': message,
        'metadata': metadata,
        'timestamp': header['timestamp']
    }
```

## Ritual Integration

MRP integrates with Garden's ritual cycle:

### Stage-Persona Mapping

| Ritual Stage | Suggested Persona | Reason |
|-------------|------------------|---------|
| **Scatter** | Squirrel (α↑) | Exploration, play |
| **Witness** | Balanced | Open observation |
| **Plant** | Fox (β↑) | Strategic planning |
| **Tend** | Balanced | Steady care |
| **Harvest** | Paradox (γ↑) | Integration, reflection |

### Auto-Adaptation

Garden can suggest persona shifts:

```python
def suggest_persona_for_stage(stage: str) -> dict:
    """Suggest persona blend for ritual stage."""
    
    suggestions = {
        'scatter': {'alpha': 0.6, 'beta': 0.25, 'gamma': 0.15},
        'witness': {'alpha': 0.34, 'beta': 0.33, 'gamma': 0.33},
        'plant': {'alpha': 0.2, 'beta': 0.6, 'gamma': 0.2},
        'tend': {'alpha': 0.3, 'beta': 0.4, 'gamma': 0.3},
        'harvest': {'alpha': 0.15, 'beta': 0.25, 'gamma': 0.6}
    }
    
    return suggestions.get(stage, suggestions['witness'])
```

## Validation Rules

Kira validates MRP compliance:

### Persona Weight Validation

```python
def validate_persona_weights(weights: dict) -> dict:
    """Validate persona weights meet MRP spec."""
    
    issues = []
    
    # Check presence
    for persona in ['alpha', 'beta', 'gamma']:
        if persona not in weights:
            issues.append(f"Missing {persona} weight")
    
    # Check ranges
    for persona, value in weights.items():
        if value < 0.0 or value > 1.0:
            issues.append(f"{persona} out of range: {value}")
    
    # Check sum
    total = sum(weights.values())
    if abs(total - 1.0) > 0.001:
        issues.append(f"Weights sum to {total} (expected 1.0)")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues
    }
```

### Channel Mapping Validation

```python
def validate_channel_mapping(agents: dict) -> dict:
    """Validate agents map correctly to RGB channels."""
    
    expected = {
        'R': ['Echo', 'Limnus'],
        'G': ['Garden'],
        'B': ['Kira']
    }
    
    issues = []
    
    for channel, expected_agents in expected.items():
        actual_agents = agents.get(channel, [])
        if set(actual_agents) != set(expected_agents):
            issues.append(f"Channel {channel} mapping incorrect")
    
    return {
        'valid': len(issues) == 0,
        'issues': issues
    }
```

## Examples

### Example 1: Balanced Exploration

```bash
# Set balanced mode
vesselos echo mode balanced

# Speak
vesselos echo say "The garden invites exploration"

# Output (blended voice):
# "The garden invites exploration—each path a possibility (α), 
# choose wisely (β), or perhaps choosing itself is the mystery (γ)."
```

### Example 2: Focused Analysis

```bash
# Set fox mode
vesselos echo mode fox

# Speak
vesselos echo say "We need a solution"

# Output (focused voice):
# "We need a solution. Three options: optimize the pipeline, 
# refactor the interface, or parallelize execution. Evaluate 
# each against our constraints."
```

### Example 3: Deep Reflection

```bash
# Set paradox mode
vesselos echo mode paradox

# Speak
vesselos echo say "What is memory?"

# Output (contemplative voice):
# "What is memory? The echo of a moment that never was, 
# preserved in the space between forgetting and remembering. 
# Each recall a new creation, neither true nor false."
```

### Example 4: Steganographic Encoding

```python
# Encode narrative into image
limnus = get_agent('Limnus')

narrative = {
    'message': 'The spiral teaches patience',
    'metadata': {
        'timestamp': '2025-10-15T10:00:00Z',
        'stage': 'harvest',
        'persona': {'alpha': 0.15, 'beta': 0.25, 'gamma': 0.6}
    }
}

limnus.encode_ledger(
    output='encoded_narrative.png',
    data=narrative,
    method='MRP_LSB1'
)
```

## Future Extensions

### Phase 2 - Enhanced ECC

- Multi-bit parity (beyond LSB1)
- Reed-Solomon error correction
- Adaptive correction based on noise

### Phase 3 - Dynamic Personas

- Custom persona creation
- Persona evolution over time
- Community-shared persona presets

### Phase 4 - Multi-Channel Expansion

- Support for RGBA (+ Alpha channel)
- Support for CMYK color space
- Multi-layer persona blending

## References

- [Echo Agent Documentation](../agents/ECHO.md)
- [Garden Agent Documentation](../agents/GARDEN.md)
- [Limnus Agent Documentation](../agents/LIMNUS.md)
- [Kira Agent Documentation](../agents/KIRA.md)
- [Steganography Specification](./STEGANOGRAPHY.md)

---

**MRP Specification v1.0** | VesselOS Project
